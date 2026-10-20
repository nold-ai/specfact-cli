import base64
import copy
import csv
import errno
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

from scripts import semgrep_distribution as producer


ROOT = Path(__file__).resolve().parents[3]
PRODUCER = ROOT / "scripts/semgrep_distribution.py"
UP = "semgrep-1.179.0"
DOWN = "specfact_semgrep-1.179.0.post1"


def symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except NotImplementedError as error:
        raise unittest.SkipTest(f"Symlink fixture API is unavailable: {error}") from error
    except OSError as error:
        if error.errno in {errno.ENOSYS, errno.ENOTSUP} or getattr(error, "winerror", None) in {1, 50, 1314}:
            raise unittest.SkipTest(f"Symlink fixture is unsupported or lacks Windows privilege: {error}") from error
        raise


def record_bytes(entries: Mapping[str, tuple[int, bytes]]) -> bytes:
    rows: list[list[str]] = []
    for name, (_mode, data) in entries.items():
        if name in {UP + ".dist-info/RECORD", DOWN + ".dist-info/RECORD"}:
            rows.append([name, "", ""])
        else:
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            rows.append([name, "sha256=" + digest, str(len(data))])
    result = io.StringIO(newline="")
    csv.writer(result, lineterminator="\n").writerows(rows)
    return result.getvalue().encode()


def write_archive(
    path: Path,
    entries: Mapping[str, tuple[int, bytes]],
    extra: tuple[str, bytes] | None = None,
    canonical: bool = False,
) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, (mode, content) in entries.items():
            info = zipfile.ZipInfo(
                name,
                date_time=((1980, 1, 1, 0, 0, 0) if canonical else (2020, 1, 1, 0, 0, 0)),
            )
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = mode << 16
            archive.writestr(info, content)
        if extra:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                archive.writestr(*extra)


class DistributionContract(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.recipe = json.loads((ROOT / "ci/semgrep-distribution.json").read_text())
        self.recipe_path = self.root / "recipe.json"
        self.wheel = self.recipe["wheels"][0]
        self.source = self.root / self.wheel["filename"]
        tags = self.wheel["filename"].split("-")[2].split(".")
        self.entries: dict[str, tuple[int, bytes]] = {
            UP + ".data/purelib/semgrep/__init__.py": (
                0o100644,
                b'__VERSION__ = "1.179.0"\n',
            ),
            UP + ".data/purelib/semgrep/bin/semgrep-core": (
                0o100755,
                b"INERT NATIVE DATA\0" * 400,
            ),
            UP + ".dist-info/METADATA": (
                0o100644,
                b"Metadata-Version: 2.4\nName: semgrep\nVersion: 1.179.0\nSummary: Leave exactly as written\n continuation\nRequires-Dist: mcp==1.29.0\nRequires-Dist: mcp-extra==4\nLicense-Expression: LGPL-2.1-or-later\n\nOriginal body\nName: semgrep\n",
            ),
            UP + ".dist-info/WHEEL": (
                0o100644,
                (
                    "Wheel-Version: 1.0\nRoot-Is-Purelib: false\n"
                    + "".join("Tag: " + t + "-none-" + self.wheel["platform_tag"] + "\n" for t in tags)
                    + "\n"
                ).encode(),
            ),
            UP + ".dist-info/entry_points.txt": (
                0o100644,
                b"[console_scripts]\nsemgrep = semgrep.console_scripts.entrypoint:main\n",
            ),
            UP + ".dist-info/licenses/LICENSE": (
                0o100644,
                b"Original license notice\n",
            ),
            UP + ".dist-info/RECORD": (0o100644, b""),
        }

    def save(self, regenerate: bool = True, extra: tuple[str, bytes] | None = None) -> None:
        if regenerate:
            self.entries[UP + ".dist-info/RECORD"] = (
                0o100644,
                record_bytes(self.entries),
            )
        write_archive(self.source, self.entries, extra)
        self.wheel["upstream_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.recipe_path.write_text(json.dumps(self.recipe))

    def command(
        self, action: str = "build", candidate: Path | None = None, output: str = "out"
    ) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            str(PRODUCER),
            action,
            "--recipe",
            str(self.recipe_path),
            "--upstream",
            str(self.source),
        ]
        args += ["--candidate", str(candidate)] if action == "verify" else ["--output", str(self.root / output)]
        return subprocess.run(args, capture_output=True, text=True, timeout=20)

    def build(self) -> Path:
        result = self.command()
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(json.loads(result.stdout)["path"])

    def rejected(self, substring: str) -> None:
        result = self.command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(substring.lower(), result.stderr.lower())

    def test_exact_metadata_roots_modes_tags_notices_and_determinism(self) -> None:
        self.save()
        candidate = self.build()
        again = self.command(output="other")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(candidate.read_bytes(), Path(json.loads(again.stdout)["path"]).read_bytes())
        self.assertEqual(candidate.name, self.source.name.replace(UP, DOWN, 1))
        with zipfile.ZipFile(candidate) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {name.replace(UP, DOWN, 1) for name in self.entries},
            )
            for name, (mode, data) in self.entries.items():
                target = name.replace(UP, DOWN, 1)
                self.assertEqual(archive.getinfo(target).external_attr >> 16, mode)
                self.assertEqual(archive.getinfo(target).compress_type, zipfile.ZIP_DEFLATED)
                self._assert_member_content(archive, name, target, data)
        result = self.command("verify", candidate)
        self.assertEqual(result.returncode, 0, result.stderr)

    def _assert_member_content(self, archive: zipfile.ZipFile, name: str, target: str, data: bytes) -> None:
        if name.endswith("/METADATA"):
            expected = (
                data.replace(b"Name: semgrep\n", b"Name: specfact-semgrep\n", 1)
                .replace(b"Version: 1.179.0\n", b"Version: 1.179.0.post1\n", 1)
                .replace(
                    b"Requires-Dist: mcp==1.29.0\n",
                    b"Requires-Dist: mcp==1.30.0\n",
                    1,
                )
            )
            head, body = expected.split(b"\n\n", 1)
            additions = self.recipe["metadata_additions"]
            expected = head + b"\n\n" + additions["description_prefix"].encode() + body
            self.assertEqual(archive.read(target), expected)
        elif not name.endswith("/RECORD"):
            self.assertEqual(archive.read(target), data)

    def test_crlf_metadata_is_preserved(self) -> None:
        key = UP + ".dist-info/METADATA"
        self.entries[key] = (0o100644, self.entries[key][1].replace(b"\n", b"\r\n"))
        self.save()
        candidate = self.build()
        with zipfile.ZipFile(candidate) as archive:
            data = archive.read(DOWN + ".dist-info/METADATA")
        self.assertIn(b"\r\nSummary: Leave exactly as written\r\n continuation\r\n", data)
        self.assertTrue(data.endswith(b"Original body\r\nName: semgrep\r\n"))

    def test_bad_metadata(self) -> None:
        original = self.entries[UP + ".dist-info/METADATA"][1]
        mutations = [
            original.replace(b"Name: semgrep", b"Name: different", 1),
            original.replace(b"Version: 1.179.0", b"Version: 1.180.0", 1),
            original.replace(b"Name: semgrep\n", b"Name: semgrep\nname: semgrep\n", 1),
            original.replace(b"Version: 1.179.0\n", b"Version: 1.179.0\nversion: 1.179.0\n", 1),
            original.replace(b"mcp==1.29.0", b"mcp>=1.29.0", 1),
            original.replace(
                b"Requires-Dist: mcp==1.29.0\n",
                b"Requires-Dist: mcp==1.29.0\nrequires-dist: MCP[cli]==1.29.0\n",
                1,
            ),
            original.replace(b"Requires-Dist: mcp==1.29.0", b"Requires-Dist: mcp\n ==1.29.0", 1),
            original.replace(b"\n\n", b"\nBad header\n\n", 1),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.entries[UP + ".dist-info/METADATA"] = (0o100644, mutation)
                self.save()
                self.rejected("metadata")

    def test_archive_paths_and_special_members(self) -> None:
        for name, mode in [
            ("..//escape", 0o100644),
            ("/absolute", 0o100644),
            (UP + ".data/../escape", 0o100644),
            (UP + ".data/./escape", 0o100644),
            (UP + ".data/back\\slash", 0o100644),
            (UP + ".data/C:drive", 0o100644),
            (UP + ".data/link", stat.S_IFLNK | 0o777),
            (UP + ".data/pipe", stat.S_IFIFO | 0o644),
            (UP + ".data/directory/", stat.S_IFDIR | 0o755),
            ("unknown/extra", 0o100644),
        ]:
            with self.subTest(name=name):
                self.entries[name] = (mode, b"x")
                self.save()
                self.rejected("archive")
                del self.entries[name]

    def test_duplicate_archive_member(self) -> None:
        self.save(extra=(UP + ".dist-info/METADATA", b"copy"))
        self.rejected("duplicate")

    def test_casefold_collision(self) -> None:
        self.entries[UP + ".dist-info/metadata"] = (0o100644, b"collision")
        self.save()
        self.rejected("duplicate")

    def test_bad_record(self) -> None:
        self.save()
        valid = self.entries[UP + ".dist-info/RECORD"][1]
        for malformed in [
            b"",
            valid.split(b"\n", 1)[1],
            valid + valid.splitlines(keepends=True)[0],
            valid.replace(b"sha256=", b"sha512=", 1),
            valid.replace(b",23\n", b",99\n", 1),
            b"bad,row\n",
        ]:
            if malformed == valid:
                continue
            with self.subTest(record=malformed):
                self.entries[UP + ".dist-info/RECORD"] = (0o100644, malformed)
                self.save(regenerate=False)
                self.rejected("record")

    def test_source_hash_mismatch(self) -> None:
        self.save()
        with self.source.open("ab") as handle:
            handle.write(b"changed")
        self.rejected("hash")

    def test_recipe_rejects_missing_or_duplicate_platform_or_identity_changes(self) -> None:
        original = copy.deepcopy(self.recipe)
        mutations: list[dict[str, object]] = []
        for key, value in [
            ("downstream_name", "other"),
            ("downstream_version", "1.179.0.post2"),
            ("mcp_to", "1.31.0"),
        ]:
            current = copy.deepcopy(original)
            current[key] = value
            mutations.append(current)
        current = copy.deepcopy(original)
        current["wheels"].pop()
        mutations.append(current)
        current = copy.deepcopy(original)
        current["wheels"][-1] = current["wheels"][0]
        mutations.append(current)
        for current in mutations:
            with self.subTest(recipe=current):
                self.save()
                self.recipe_path.write_text(json.dumps(current))
                self.rejected("recipe")

    def test_tag_mismatch(self) -> None:
        key = UP + ".dist-info/WHEEL"
        self.entries[key] = (
            0o100644,
            self.entries[key][1].replace(b"Tag: cp310", b"Tag: cp399", 1),
        )
        self.save()
        self.rejected("tag")

    def test_embedded_signature_rejected(self) -> None:
        self.entries[UP + ".dist-info/RECORD.jws"] = (
            0o100644,
            b"invalid inherited signature",
        )
        self.save()
        self.rejected("signature")

    def test_candidate_tampering_rejected_even_with_fresh_record(self) -> None:
        self.save()
        candidate = self.build()
        with zipfile.ZipFile(candidate) as archive:
            pristine = {i.filename: (i.external_attr >> 16, archive.read(i)) for i in archive.infolist()}
        keys = [
            DOWN + ".data/purelib/semgrep/bin/semgrep-core",
            DOWN + ".dist-info/WHEEL",
            DOWN + ".dist-info/licenses/LICENSE",
            DOWN + ".dist-info/entry_points.txt",
            DOWN + ".dist-info/METADATA",
        ]
        for key in keys:
            with self.subTest(key=key):
                entries = copy.deepcopy(pristine)
                mode, data = entries[key]
                entries[key] = (mode, data + b"tamper")
                entries[DOWN + ".dist-info/RECORD"] = (0o100644, record_bytes(entries))
                write_archive(candidate, entries, canonical=True)
                result = self.command("verify", candidate)
                self.assertNotEqual(result.returncode, 0)
        entries = copy.deepcopy(pristine)
        key = keys[0]
        mode, data = entries[key]
        entries[key] = (0o100644, data)
        write_archive(candidate, entries, canonical=True)
        result = self.command("verify", candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mode", result.stderr.lower())

    def test_nested_metadata_and_record_are_ordinary_runtime_payloads(self) -> None:
        for basename in ("METADATA", "RECORD"):
            self.entries[UP + ".data/purelib/semgrep/" + basename] = (
                0o100644,
                b"runtime resource",
            )
        self.save()
        candidate = self.build()
        with zipfile.ZipFile(candidate) as archive:
            pristine = {i.filename: (i.external_attr >> 16, archive.read(i)) for i in archive.infolist()}
        for basename in ("METADATA", "RECORD"):
            entries = copy.deepcopy(pristine)
            entries[DOWN + ".data/purelib/semgrep/" + basename] = (
                0o100644,
                b"changed runtime resource",
            )
            entries[DOWN + ".dist-info/RECORD"] = (0o100644, record_bytes(entries))
            write_archive(candidate, entries, canonical=True)
            result = self.command("verify", candidate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("payload", result.stderr.lower())

    def test_semantic_verify_reports_hash_for_other_valid_compression(self) -> None:
        self.save()
        candidate = self.build()
        canonical_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        with zipfile.ZipFile(candidate) as archive:
            entries = {i.filename: (i.external_attr >> 16, archive.read(i)) for i in archive.infolist()}
        write_archive(candidate, entries, canonical=True)
        actual_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        self.assertNotEqual(canonical_digest, actual_digest)
        result = self.command("verify", candidate)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sha256"], actual_digest)
        self.assertNotEqual(json.loads(result.stdout)["sha256"], canonical_digest)

    def test_refuses_existing_output(self) -> None:
        self.save()
        self.build()
        self.rejected("exists")

    def test_oversized_sparse_upstream_rejected_before_hash(self) -> None:
        self.save()
        with self.source.open("r+b") as handle:
            handle.truncate(150 * 1024 * 1024 + 1)
        self.rejected("compressed size limit")

    def test_oversized_sparse_candidate_rejected_before_zip(self) -> None:
        self.save()
        candidate = self.build()
        with candidate.open("r+b") as handle:
            handle.truncate(150 * 1024 * 1024 + 1)
        result = self.command("verify", candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compressed size limit", result.stderr.lower())

    def test_bounded_build_rejects_output_growth_without_publishing(self) -> None:
        self.entries[UP + ".data/purelib/semgrep/inert.bin"] = (
            0o100644,
            b"".join(hashlib.sha256(str(i).encode()).digest() for i in range(256)),
        )
        self.save()
        candidate = self.build()
        self.assertGreater(candidate.stat().st_size, self.source.stat().st_size)
        with (
            patch.object(producer, "MAX_COMPRESSED_BYTES", self.source.stat().st_size, create=True),
            self.assertRaisesRegex(producer.DistributionError, "compressed size limit"),
        ):
            producer.build(self.recipe_path, self.source, self.root / "bounded")
        self.assertEqual(list((self.root / "bounded").iterdir()), [])

    def test_upstream_directory_rejected(self) -> None:
        self.save()
        self.source.unlink()
        self.source.mkdir()
        self.rejected("regular file")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixture requires the Unix-only os.mkfifo API")
    def test_upstream_fifo_rejected(self) -> None:
        self.save()
        self.source.unlink()
        os.mkfifo(self.source)
        self.rejected("regular file")

    def test_upstream_symlink_rejected(self) -> None:
        self.save()
        original = self.source.with_suffix(".original")
        self.source.rename(original)
        symlink_or_skip(self.source, original)
        self.rejected("regular file")

    def test_prefixed_semantically_valid_candidate_reports_actual_hash(self) -> None:
        self.save()
        candidate = self.build()
        candidate.write_bytes(b"inert prefix\n" + candidate.read_bytes())
        result = self.command("verify", candidate)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sha256"], hashlib.sha256(candidate.read_bytes()).hexdigest())

    def test_exact_compressed_limit_is_accepted(self) -> None:
        path = self.root / "bounded.bin"
        path.write_bytes(b"x" * 16)
        with patch.object(producer, "MAX_COMPRESSED_BYTES", 16):
            self.assertEqual(producer.read_regular_file(path), b"x" * 16)
            with path.open("ab") as writer:
                writer.write(b"x")
            with self.assertRaisesRegex(producer.DistributionError, "compressed size limit"):
                producer.read_regular_file(path)

    def test_file_growth_after_stat_still_has_a_bounded_read(self) -> None:
        path = self.root / "growing.bin"
        path.write_bytes(b"x")

        class GrowingFile(io.BufferedReader):
            def read(self, size: int | None = -1) -> bytes:
                with path.open("ab") as writer:
                    writer.write(b"y" * 64)
                return super().read(size)

        with (
            GrowingFile(path.open("rb", buffering=0)) as reader,
            patch.object(producer, "MAX_COMPRESSED_BYTES", 16),
        ):
            with self.assertRaisesRegex(producer.DistributionError, "compressed size limit"):
                producer.bounded_read(reader)
            self.assertEqual(reader.tell(), 17)
            self.assertEqual(path.stat().st_size, 65)

    def test_candidate_directory_rejected(self) -> None:
        self.save()
        candidate = self.build()
        candidate.unlink()
        candidate.mkdir()
        result = self.command("verify", candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file type", result.stderr.lower())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixture requires the Unix-only os.mkfifo API")
    def test_candidate_fifo_rejected(self) -> None:
        self.save()
        candidate = self.build()
        candidate.unlink()
        os.mkfifo(candidate)
        result = self.command("verify", candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file type", result.stderr.lower())

    def test_candidate_symlink_rejected(self) -> None:
        self.save()
        candidate = self.build()
        original = candidate.with_suffix(".original")
        candidate.rename(original)
        symlink_or_skip(candidate, original)
        result = self.command("verify", candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file type", result.stderr.lower())


class SymlinkFixtureCapabilities(unittest.TestCase):
    def test_unsupported_api_skips(self) -> None:
        for error in (
            NotImplementedError("symlink API unavailable"),
            OSError(errno.ENOSYS, "symlink API unavailable"),
            OSError(errno.ENOTSUP, "symlink filesystem unsupported"),
        ):
            with (
                self.subTest(error=error),
                patch.object(Path, "symlink_to", side_effect=error),
                self.assertRaises(unittest.SkipTest),
            ):
                symlink_or_skip(Path("link"), Path("target"))

    def test_windows_unsupported_or_privilege_errors_skip(self) -> None:
        for code in (1, 50, 1314):
            error = OSError(errno.EACCES, "simulated Windows symlink error")
            error.winerror = code
            with (
                self.subTest(winerror=code),
                patch.object(Path, "symlink_to", side_effect=error),
                self.assertRaises(unittest.SkipTest),
            ):
                symlink_or_skip(Path("link"), Path("target"))

    def test_unexpected_errors_are_not_skipped(self) -> None:
        for code in (errno.EACCES, errno.EPERM, errno.EIO, errno.EEXIST, errno.ENOENT):
            error = OSError(code, "unexpected fixture error")
            with self.subTest(errno=code), patch.object(Path, "symlink_to", side_effect=error):
                with self.assertRaises(OSError) as raised:
                    symlink_or_skip(Path("link"), Path("target"))
                self.assertIs(raised.exception, error)


if __name__ == "__main__":
    unittest.main()
