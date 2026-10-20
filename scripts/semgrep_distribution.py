"""Build and verify one fixed downstream Semgrep distribution as inert ZIP data."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TypeGuard
from urllib.parse import urlsplit


UPSTREAM = "semgrep-1.179.0"
DOWNSTREAM = "specfact_semgrep-1.179.0.post1"
PYTHON_TAGS = "cp310.cp311.cp312.cp313.cp314.py310.py311.py312.py313.py314"
PLATFORMS = frozenset(
    {
        "macosx_10_14_x86_64",
        "macosx_11_0_arm64",
        "manylinux_2_34_x86_64",
        "manylinux_2_34_aarch64",
        "musllinux_1_2_x86_64",
        "musllinux_1_2_aarch64",
        "win_amd64",
    }
)
NOTICE = "Downstream distribution specfact-semgrep 1.179.0.post1. Based on Semgrep 1.179.0; runtime payloads are unchanged. Packaging changes identify this distribution and require mcp==1.30.0. Upstream project: https://github.com/semgrep/semgrep. Downstream source: https://github.com/nold-ai/specfact-cli.\n\n"
METADATA_EDITS = {
    b"name": (b"Name: semgrep", b"Name: specfact-semgrep"),
    b"version": (b"Version: 1.179.0", b"Version: 1.179.0.post1"),
    b"mcp": (b"Requires-Dist: mcp==1.29.0", b"Requires-Dist: mcp==1.30.0"),
}
STAMP = (1980, 1, 1, 0, 0, 0)
CHUNK = 1024 * 1024
MAX_COMPRESSED_BYTES = 150 * 1024 * 1024


class DistributionError(ValueError):
    """The recipe or archive differs from this exact transformation contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DistributionError(message)


def bounded_read(source: IO[bytes]) -> bytes:
    info = os.fstat(source.fileno())
    require(stat.S_ISREG(info.st_mode), "Input must be a regular file")
    require(info.st_size <= MAX_COMPRESSED_BYTES, "Input exceeds compressed size limit")
    raw = source.read(MAX_COMPRESSED_BYTES + 1)
    require(len(raw) <= MAX_COMPRESSED_BYTES, "Input exceeds compressed size limit")
    return raw


def read_regular_file(path: Path) -> bytes:
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "Input must be a regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        opened = os.fstat(source.fileno())
        require(
            (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino),
            "Input file changed while opening",
        )
        return bounded_read(source)


@dataclass(frozen=True)
class Recipe:
    digest: str
    wheels: tuple[dict[str, str], ...]


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate recipe key")
        result[key] = value
    return result


def _recipe_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _validate_upstream_url(upstream_url: str, filename: str) -> None:
    url = urlsplit(upstream_url)
    require(
        url.scheme == "https"
        and url.netloc == "files.pythonhosted.org"
        and url.path.startswith("/packages/")
        and url.path.endswith("/" + filename)
        and not url.query
        and not url.fragment,
        "Invalid recipe upstream URL",
    )


def _recipe_wheel(value: object, seen: set[str]) -> dict[str, str]:
    if not _recipe_object(value) or set(value) != {"filename", "platform_tag", "upstream_sha256", "upstream_url"}:
        raise DistributionError("Unexpected recipe wheel fields")
    wheel: dict[str, str] = {}
    for key, field in value.items():
        if not isinstance(field, str):
            raise DistributionError("Recipe wheel fields must be strings")
        wheel[key] = field
    platform = wheel["platform_tag"]
    require(platform in PLATFORMS and platform not in seen, "Unknown or duplicate recipe platform")
    seen.add(platform)
    require(
        wheel["filename"] == f"{UPSTREAM}-{PYTHON_TAGS}-none-{platform}.whl",
        "Unexpected recipe wheel tags",
    )
    require(
        re.fullmatch("[0-9a-f]{64}", wheel["upstream_sha256"]) is not None,
        "Invalid recipe hash",
    )
    _validate_upstream_url(wheel["upstream_url"], wheel["filename"])
    return wheel


def load_recipe(path: Path) -> Recipe:
    raw = read_regular_file(path)
    data: object = json.loads(raw, object_pairs_hook=unique_object)
    expected = {
        "schema_version": 1,
        "upstream_name": "semgrep",
        "upstream_version": "1.179.0",
        "downstream_name": "specfact-semgrep",
        "downstream_version": "1.179.0.post1",
        "mcp_from": "1.29.0",
        "mcp_to": "1.30.0",
        "compression": {"method": "ZIP_DEFLATED", "level": 9},
        "metadata_additions": {"description_prefix": NOTICE},
    }
    if not _recipe_object(data) or set(data) != set(expected) | {"wheels"}:
        raise DistributionError("Unexpected recipe fields")
    require(
        all(data.get(key) == value for key, value in expected.items()),
        "Unexpected recipe identity or transformation",
    )
    values = data["wheels"]
    if not isinstance(values, list) or len(values) != 7:
        raise DistributionError("Recipe must contain seven wheels")
    wheels: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        wheels.append(_recipe_wheel(value, seen))
    return Recipe(hashlib.sha256(raw).hexdigest(), tuple(wheels))


def digest_member(archive: zipfile.ZipFile, name: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with archive.open(name) as member:
        while chunk := member.read(CHUNK):
            digest.update(chunk)
            size += len(chunk)
    return "sha256=" + base64.urlsafe_b64encode(digest.digest()).decode().rstrip("="), size


def metadata_parts(raw: bytes) -> tuple[list[bytes], bytes, bytes]:
    match = re.search(rb"\r?\n\r?\n", raw)
    if match is None:
        raise DistributionError("Metadata has no header separator")
    newline = b"\r\n" if match[0] == b"\r\n\r\n" else b"\n"
    header, body = raw[: match.start()], raw[match.end() :]
    require(b"\x00" not in header, "Malformed metadata header")
    lines = header.split(newline)
    require(
        all(b"\n" not in line and b"\r" not in line for line in lines),
        "Mixed metadata line endings",
    )
    fields: list[bytes] = []
    for line in lines:
        if line.startswith((b" ", b"\t")):
            require(bool(fields), "Orphan metadata continuation")
            fields[-1] += newline + line
        else:
            require(
                re.match(rb"^[A-Za-z0-9-]+:", line) is not None,
                "Malformed metadata header",
            )
            fields.append(line)
    return fields, newline, body


def identity_fields(fields: list[bytes]) -> dict[bytes, list[bytes]]:
    found: dict[bytes, list[bytes]] = {b"name": [], b"version": [], b"mcp": []}
    for field in fields:
        key, value = field.split(b":", 1)
        key = key.lower()
        if key in {b"name", b"version"}:
            found[key].append(field)
        if key == b"requires-dist":
            match = re.match(rb"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", value)
            if match is None:
                raise DistributionError("Malformed metadata requirement")
            normalized = re.sub(rb"[-_.]+", b"-", match[1]).lower()
            if normalized == b"mcp":
                found[b"mcp"].append(field)
    return found


def transform_metadata(raw: bytes) -> bytes:
    fields, newline, body = metadata_parts(raw)
    found = identity_fields(fields)
    for key, (before, after) in METADATA_EDITS.items():
        require(found[key] == [before], "Unexpected metadata identity or MCP cardinality")
        fields[fields.index(before)] = after
    return newline.join(fields) + newline * 2 + NOTICE.encode().replace(b"\n", newline) + body


def verify_metadata(upstream: bytes, candidate: bytes) -> None:
    source_fields, newline, source_body = metadata_parts(upstream)
    target_fields, target_newline, target_body = metadata_parts(candidate)
    require(newline == target_newline, "Metadata newline changed")
    notice = NOTICE.encode().replace(b"\n", newline)
    require(target_body == notice + source_body, "Metadata description differs")
    restored = target_fields[:]
    source_identity, target_identity = (
        identity_fields(source_fields),
        identity_fields(restored),
    )
    for key, (before, after) in METADATA_EDITS.items():
        require(
            source_identity[key] == [before] and target_identity[key] == [after],
            "Metadata identity differs",
        )
        restored[restored.index(after)] = before
    require(restored == source_fields, "Unapproved metadata change")


def _validate_member(info: zipfile.ZipInfo, root: str) -> None:
    name = info.filename
    parts = name.split("/")
    require(
        name == info.orig_filename
        and parts[0] in {root + ".dist-info", root + ".data"}
        and len(parts) > 1
        and all(part not in {"", ".", ".."} for part in parts)
        and "\\" not in name
        and ":" not in name
        and "\x00" not in name,
        "Unsafe archive path",
    )
    require(
        stat.S_IFMT(info.external_attr >> 16) in {0, stat.S_IFREG} and not info.is_dir(),
        "Archive special member",
    )
    require(
        info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED} and not info.flag_bits & 1,
        "Unsupported archive encoding",
    )
    require(
        not name.endswith(("/RECORD.jws", "/RECORD.p7s")),
        "Inherited signature is not allowed",
    )


def _validate_record(archive: zipfile.ZipFile, root: str, members: dict[str, zipfile.ZipInfo]) -> None:
    record_name = root + ".dist-info/RECORD"
    require(record_name in members, "Missing RECORD")
    try:
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise DistributionError("Malformed RECORD") from exc
    require(all(len(row) == 3 for row in rows), "Malformed RECORD row")
    require(
        len(rows) == len(members) and {row[0] for row in rows} == set(members),
        "Incomplete or duplicate RECORD",
    )
    for name, digest, size in rows:
        if name == record_name:
            require((digest, size) == ("", ""), "RECORD must not hash itself")
        else:
            expected, length = digest_member(archive, name)
            require((digest, size) == (expected, str(length)), "RECORD hash or size differs")


def _validate_wheel(archive: zipfile.ZipFile, root: str, platform: str, members: dict[str, zipfile.ZipInfo]) -> None:
    for required in ("METADATA", "WHEEL", "entry_points.txt"):
        require(
            root + ".dist-info/" + required in members,
            "Missing archive metadata " + required,
        )
    wheel_data = archive.read(root + ".dist-info/WHEEL")
    fields, _, body = metadata_parts(wheel_data)
    require(not body.strip(), "Unexpected WHEEL body")
    expected_tags = {f"{tag}-none-{platform}".encode() for tag in PYTHON_TAGS.split(".")}
    tags = [value.strip() for field in fields for key, value in [field.split(b":", 1)] if key.lower() == b"tag"]
    require(
        len(tags) == len(expected_tags) and set(tags) == expected_tags,
        "WHEEL tags differ from filename",
    )


def validate_archive(archive: zipfile.ZipFile, root: str, platform: str) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    require(
        len(infos) <= 10000 and sum(info.file_size for info in infos) <= 1024**3,
        "Archive exceeds size limits",
    )
    members: dict[str, zipfile.ZipInfo] = {}
    folded: set[str] = set()
    for info in infos:
        _validate_member(info, root)
        name = info.filename
        require(name.casefold() not in folded, "Duplicate archive member")
        folded.add(name.casefold())
        members[name] = info
    _validate_record(archive, root, members)
    _validate_wheel(archive, root, platform, members)
    return members


def renamed(name: str) -> str:
    root, suffix = name.split("/", 1)
    require(root in {UPSTREAM + ".data", UPSTREAM + ".dist-info"}, "Unexpected archive root")
    return DOWNSTREAM + root[len(UPSTREAM) :] + "/" + suffix


class _CompressedZipInfo(zipfile.ZipInfo):
    # Python 3.11/3.12 streaming writes have no public compression-level setter.
    _compresslevel: int | None


def _output_info(original: zipfile.ZipInfo, name: str) -> zipfile.ZipInfo:
    info = _CompressedZipInfo(name, STAMP)
    info.create_system = original.create_system
    info.external_attr = original.external_attr
    info.compress_type = zipfile.ZIP_DEFLATED
    require(hasattr(info, "_compresslevel"), "Unsupported ZIP compression API")
    info._compresslevel = 9
    return info


def _write_member(
    output: zipfile.ZipFile,
    source: zipfile.ZipFile,
    original: zipfile.ZipInfo,
    metadata: bytes,
) -> tuple[str, str, str]:
    name = renamed(original.filename)
    info = _output_info(original, name)
    digest = hashlib.sha256()
    length = 0
    reader = io.BytesIO(metadata) if original.filename == UPSTREAM + ".dist-info/METADATA" else source.open(original)
    with reader, output.open(info, "w") as member:
        while chunk := reader.read(CHUNK):
            member.write(chunk)
            digest.update(chunk)
            length += len(chunk)
    return (
        name,
        "sha256=" + base64.urlsafe_b64encode(digest.digest()).decode().rstrip("="),
        str(length),
    )


def write_archive(destination: IO[bytes], source: zipfile.ZipFile, metadata: bytes) -> None:
    record_name = DOWNSTREAM + ".dist-info/RECORD"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        rows = [
            _write_member(output, source, original, metadata)
            for original in sorted(source.infolist(), key=lambda info: info.filename)
            if renamed(original.filename) != record_name
        ]
        rows.append((record_name, "", ""))
        buffer = io.StringIO(newline="")
        csv.writer(buffer, lineterminator="\n").writerows(rows)
        info = _output_info(source.getinfo(UPSTREAM + ".dist-info/RECORD"), record_name)
        output.writestr(
            info,
            buffer.getvalue().encode(),
            compress_type=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        )


def upstream_snapshot(recipe: Recipe, path: Path) -> tuple[dict[str, str], bytes]:
    matches = [wheel for wheel in recipe.wheels if wheel["filename"] == path.name]
    require(len(matches) == 1, "Upstream wheel absent from recipe")
    raw = read_regular_file(path)
    require(
        hashlib.sha256(raw).hexdigest() == matches[0]["upstream_sha256"],
        "Upstream hash differs",
    )
    return matches[0], raw


def _verify_member(
    source: zipfile.ZipFile,
    target: zipfile.ZipFile,
    name: str,
    original: zipfile.ZipInfo,
    target_members: dict[str, zipfile.ZipInfo],
) -> None:
    target_name = renamed(name)
    actual = target_members[target_name]
    require(
        actual.external_attr == original.external_attr and actual.create_system == original.create_system,
        "Candidate mode or platform attributes differ",
    )
    require(
        actual.date_time == STAMP
        and actual.compress_type == zipfile.ZIP_DEFLATED
        and not actual.extra
        and not actual.comment,
        "Candidate archive attributes differ",
    )
    if name == UPSTREAM + ".dist-info/METADATA":
        verify_metadata(source.read(name), target.read(target_name))
        return
    if name == UPSTREAM + ".dist-info/RECORD":
        return
    with source.open(name) as left, target.open(target_name) as right:
        while True:
            chunk = left.read(CHUNK)
            require(chunk == right.read(CHUNK), "Candidate payload differs: " + name)
            if not chunk:
                break


def verify_snapshots(wheel: dict[str, str], source_raw: bytes, candidate_raw: bytes) -> dict[str, object]:
    with (
        zipfile.ZipFile(io.BytesIO(source_raw)) as source,
        zipfile.ZipFile(io.BytesIO(candidate_raw)) as target,
    ):
        source_members = validate_archive(source, UPSTREAM, wheel["platform_tag"])
        target_members = validate_archive(target, DOWNSTREAM, wheel["platform_tag"])
        require(
            set(target_members) == {renamed(name) for name in source_members},
            "Candidate archive members differ",
        )
        for name, original in source_members.items():
            _verify_member(source, target, name, original, target_members)
        return {
            "sha256": hashlib.sha256(candidate_raw).hexdigest(),
            "upstream_sha256": wheel["upstream_sha256"],
            "platform": wheel["platform_tag"],
            "bytes": len(candidate_raw),
            "members": len(target_members),
            "status": "verified-data-only",
        }


def verify(recipe_path: Path, upstream: Path, candidate: Path) -> dict[str, object]:
    recipe = load_recipe(recipe_path)
    wheel, source_raw = upstream_snapshot(recipe, upstream)
    expected_name = wheel["filename"].replace(UPSTREAM + "-", DOWNSTREAM + "-", 1)
    require(
        candidate.name == expected_name and candidate.is_file() and not candidate.is_symlink(),
        "Unexpected candidate filename or file type",
    )
    result = verify_snapshots(wheel, source_raw, read_regular_file(candidate))
    return dict(result, path=str(candidate), recipe_sha256=recipe.digest)


def build(recipe_path: Path, upstream: Path, output: Path) -> dict[str, object]:
    recipe = load_recipe(recipe_path)
    wheel, source_raw = upstream_snapshot(recipe, upstream)
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / wheel["filename"].replace(UPSTREAM + "-", DOWNSTREAM + "-", 1)
    require(
        not candidate.exists() and not candidate.is_symlink(),
        "Candidate output already exists",
    )
    with zipfile.ZipFile(io.BytesIO(source_raw)) as source:
        validate_archive(source, UPSTREAM, wheel["platform_tag"])
        metadata = transform_metadata(source.read(UPSTREAM + ".dist-info/METADATA"))
        with tempfile.NamedTemporaryFile(dir=output, prefix=".semgrep-", suffix=".tmp") as temporary:
            write_archive(temporary.file, source, metadata)
            temporary.flush()
            temporary.seek(0)
            result = verify_snapshots(wheel, source_raw, bounded_read(temporary.file))
            os.link(temporary.name, candidate)
    return dict(
        result,
        path=str(candidate),
        recipe_sha256=recipe.digest,
        python=sys.version,
        zlib=zlib.ZLIB_RUNTIME_VERSION,
        compression="ZIP_DEFLATED",
        compression_level=9,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for action in ("build", "verify"):
        command = commands.add_parser(action)
        command.add_argument("--recipe", type=Path, required=True)
        command.add_argument("--upstream", type=Path, required=True)
        command.add_argument("--output" if action == "build" else "--candidate", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            build(args.recipe, args.upstream, args.output)
            if args.command == "build"
            else verify(args.recipe, args.upstream, args.candidate)
        )
    except (
        DistributionError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        zipfile.BadZipFile,
        RuntimeError,
        NotImplementedError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
