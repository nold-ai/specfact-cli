from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import re
import ssl
import subprocess
import sys
import time
import tomllib
import urllib.request
from dataclasses import dataclass
from email.message import Message
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from zipfile import ZipFile, ZipInfo

import pytest


_MAX_DOWNLOAD = 150 * 1024 * 1024
_MAX_EXPANDED = 512 * 1024 * 1024
_BAD_CA = "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"
_PLATFORM = "manylinux_2_34_x86_64"


@dataclass(frozen=True)
class WheelContents:
    members: dict[str, bytes]
    modes: dict[str, int]
    metadata: Message
    dist_info: str


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        raise ValueError("Pinned artifact downloads must not redirect")


def _download(url: str, digest: str, destination: Path) -> Path:
    parsed = urlsplit(url)
    assert parsed.scheme == "https" and parsed.netloc == "files.pythonhosted.org", "Unapproved artifact origin"
    assert not parsed.query and not parsed.fragment, "Artifact URLs cannot contain queries or fragments"
    assert re.fullmatch(r"[a-f0-9]{64}", digest), "A SHA256 pin is required"
    assert parsed.path.endswith(".whl"), "Expected a wheel URL"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())
    size = 0
    checksum = hashlib.sha256()
    started = time.monotonic()
    with opener.open(url, timeout=30) as response, destination.open("xb") as output:
        assert response.status == 200, "Artifact download did not succeed"
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            assert size <= _MAX_DOWNLOAD, "Artifact exceeds the 150 MiB download limit"
            assert time.monotonic() - started < 30, "Artifact download exceeded 30 seconds"
            checksum.update(chunk)
            output.write(chunk)
    assert checksum.hexdigest() == digest, "Downloaded artifact SHA256 differs from its pin"
    return destination


def _regular_member(entry: ZipInfo) -> None:
    parts = PurePosixPath(entry.filename).parts
    assert parts and not entry.filename.startswith("/"), "Absolute wheel member"
    assert ".." not in parts and "\\" not in entry.filename, "Unsafe wheel member"
    assert not entry.is_dir(), "Explicit directory members are not supported"
    assert PurePosixPath(entry.filename).as_posix() == entry.filename, "Noncanonical wheel member"
    assert (entry.external_attr >> 16) & 0o170000 in (0, 0o100000), "Nonregular wheel member"


def _member_inventory(entries: list[ZipInfo], expected_root: str) -> None:
    names = [entry.filename for entry in entries]
    assert len(names) == len(set(names)), "Duplicate wheel member"
    assert len(entries) <= 10000, "Wheel member limit exceeded"
    assert sum(entry.file_size for entry in entries) <= _MAX_EXPANDED, "Expanded wheel size limit exceeded"
    for entry in entries:
        _regular_member(entry)
    roots = {name.split("/", 1)[0] for name in names if name.split("/", 1)[0].endswith(".dist-info")}
    assert roots == {expected_root}, "Unexpected wheel distribution root"


def _record_entry(members: dict[str, bytes], record_path: str, row: list[str]) -> None:
    member, digest, size = row
    if member == record_path:
        assert digest == size == "", "RECORD must leave its own hash and size empty"
        return
    expected = base64.urlsafe_b64encode(hashlib.sha256(members[member]).digest()).rstrip(b"=").decode("ascii")
    assert digest == f"sha256={expected}", f"RECORD hash differs for {member}"
    assert size == str(len(members[member])), f"RECORD size differs for {member}"


def _record_inventory(members: dict[str, bytes], record_path: str) -> None:
    rows = list(csv.reader(io.StringIO(members[record_path].decode("utf-8"))))
    assert all(len(row) == 3 for row in rows), "Malformed wheel RECORD"
    assert len(rows) == len({row[0] for row in rows}), "Duplicate wheel RECORD member"
    assert {row[0] for row in rows} == set(members), "RECORD does not cover exactly the wheel members"
    for row in rows:
        _record_entry(members, record_path, row)


def _wheel(path: Path, name: str, version: str) -> WheelContents:
    expected_root = f"{name.replace('-', '_')}-{version}.dist-info"
    with ZipFile(path) as archive:
        entries = archive.infolist()
        _member_inventory(entries, expected_root)
        members = {entry.filename: archive.read(entry) for entry in entries}
        modes = {entry.filename: entry.external_attr >> 16 for entry in entries}
    metadata = BytesParser().parsebytes(members[f"{expected_root}/METADATA"])
    assert metadata.get_all("Name") == [name], "Wheel metadata name differs from selected distribution"
    assert metadata.get_all("Version") == [version], "Wheel metadata version differs from selected distribution"
    _record_inventory(members, f"{expected_root}/RECORD")
    assert f"{expected_root}/WHEEL" in members, "Wheel metadata is missing"
    return WheelContents(members, modes, metadata, expected_root)


def _certifi_selection(root: Path) -> tuple[str, str, str]:
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    packages = [package for package in lock["package"] if package["name"] == "certifi"]
    assert len(packages) == 1, "The frozen graph must select exactly one certifi distribution"
    package = packages[0]
    wheels = package["wheels"]
    assert len(wheels) == 1, "Expected exactly one certifi wheel in the frozen graph"
    version, url, digest = package["version"], wheels[0]["url"], wheels[0]["hash"]
    assert digest.startswith("sha256:"), "Frozen certifi wheel must use SHA256"
    _export_certifi_hash(root, version, digest)
    return version, url, digest.removeprefix("sha256:")


def _export_certifi_hash(root: Path, version: str, digest: str) -> None:
    export = (root / "requirements/ci/locked.txt").read_text(encoding="utf-8").replace("\\\n", " ")
    lines = [line for line in export.splitlines() if line.startswith("certifi==")]
    assert len(lines) == 1, "The exported graph must select exactly one certifi distribution"
    assert re.match(rf"certifi=={re.escape(version)}(?:\s|$)", lines[0]), "Lock and export certifi versions differ"
    assert f"--hash={digest}" in lines[0].split(), "Export omits the selected certifi wheel hash"


def test_frozen_certifi_bundle_excludes_compromised_root(tmp_path: Path, pytestconfig: pytest.Config) -> None:
    version, url, digest = _certifi_selection(pytestconfig.rootpath)
    path = _download(url, digest, tmp_path / "certifi.whl")
    wheel = _wheel(path, "certifi", version)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata=wheel.members["certifi/cacert.pem"].decode("ascii"))
    fingerprints = {hashlib.sha256(cert).hexdigest() for cert in context.get_ca_certs(binary_form=True)}
    assert fingerprints, "Frozen certifi artifact must provide a nonempty CA trust store"
    assert _BAD_CA not in fingerprints, "Frozen certifi artifact retains the compromised emSign root"


def _normalized_members(wheel: WheelContents) -> dict[str, tuple[bytes, int]]:
    data_root = wheel.dist_info.removesuffix(".dist-info") + ".data"
    normalized = {}
    for name, payload in wheel.members.items():
        root, separator, suffix = name.partition("/")
        if root == wheel.dist_info:
            root = "DIST-INFO"
        elif root == data_root:
            root = "DATA"
        normalized[root + separator + suffix] = (payload, wheel.modes[name])
    assert len(normalized) == len(wheel.members), "Wheel root normalization collides with another member"
    return normalized


@dataclass(frozen=True)
class ScannerSource:
    filename: str
    url: str
    digest: str
    notice: str


def _scanner_source(recipe_path: Path) -> ScannerSource:
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    _scanner_identity(recipe)
    rows = [row for row in recipe["wheels"] if row["platform_tag"] == _PLATFORM]
    assert len(rows) == 1, "Recipe must select exactly one fixed Linux data artifact"
    source = rows[0]
    filename, url, digest = source["filename"], source["upstream_url"], source["upstream_sha256"]
    assert isinstance(filename, str) and isinstance(url, str) and isinstance(digest, str)
    assert Path(filename).name == filename, "Source filename must be a basename"
    assert urlsplit(url).path.rsplit("/", 1)[1] == filename
    notice = recipe["metadata_additions"]["description_prefix"]
    assert isinstance(notice, str), "Recipe must declare the exact downstream notice"
    return ScannerSource(filename, url, digest, notice)


def _scanner_identity(recipe: dict[str, object]) -> None:
    assert recipe["downstream_name"] == "specfact-semgrep"
    assert recipe["downstream_version"] == "1.179.0.post1"
    assert recipe["upstream_version"] == "1.179.0"
    assert recipe["mcp_from"] == "1.29.0" and recipe["mcp_to"] == "1.30.0"


def _build_scanner_artifact(root: Path, upstream: Path, output: Path) -> Path:
    command = [sys.executable, "-I", "-S", str(root / "scripts/semgrep_distribution.py"), "build"]
    command.extend(("--recipe", str(root / "ci/semgrep-distribution.json")))
    command.extend(("--upstream", str(upstream), "--output", str(output)))
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    filename = "specfact_semgrep-1.179.0.post1-" + upstream.name.split("-", 2)[2]
    return output / filename


def _selected_scanner_artifact(tmp_path: Path, root: Path) -> tuple[WheelContents, WheelContents, str]:
    source = _scanner_source(root / "ci/semgrep-distribution.json")
    upstream_path = _download(source.url, source.digest, tmp_path / source.filename)
    upstream = _wheel(upstream_path, "semgrep", "1.179.0")
    actual = upstream
    if (root / "scripts/semgrep_distribution.py").is_file():
        candidate = _build_scanner_artifact(root, upstream_path, tmp_path / "built")
        actual = _wheel(candidate, "specfact-semgrep", "1.179.0.post1")
    return upstream, actual, source.notice


def _assert_scanner_dependencies(upstream: WheelContents, actual: WheelContents) -> None:
    requires = actual.metadata.get_all("Requires-Dist", [])
    mcp = [requirement for requirement in requires if re.match(r"(?i)^mcp(?:\s|[=<>!~;\[]|$)", requirement)]
    assert mcp == ["mcp==1.30.0"], "Selected scanner artifact must require the fixed MCP release"
    old_requires = upstream.metadata.get_all("Requires-Dist", [])
    assert old_requires.count("mcp==1.29.0") == 1
    assert requires == ["mcp==1.30.0" if requirement == "mcp==1.29.0" else requirement for requirement in old_requires]


def _assert_scanner_description(upstream: WheelContents, actual: WheelContents, notice: str) -> None:
    description = actual.metadata.get_payload()
    source_description = upstream.metadata.get_payload()
    assert isinstance(description, str) and isinstance(source_description, str)
    newline = "\r\n" if b"\r\n\r\n" in upstream.members[f"{upstream.dist_info}/METADATA"] else "\n"
    assert description == notice.replace("\n", newline) + source_description, "Unreviewed downstream description change"


def _assert_scanner_metadata(upstream: WheelContents, actual: WheelContents, notice: str) -> None:
    _assert_scanner_dependencies(upstream, actual)
    assert actual.metadata.get_all("Name") == ["specfact-semgrep"]
    assert actual.metadata.get_all("Version") == ["1.179.0.post1"]
    mutable_headers = {"name", "version", "requires-dist"}
    assert [(key, value) for key, value in actual.metadata.items() if key.lower() not in mutable_headers] == [
        (key, value) for key, value in upstream.metadata.items() if key.lower() not in mutable_headers
    ], "Downstream wheel changed unrelated metadata headers"
    _assert_scanner_description(upstream, actual, notice)


def _assert_scanner_payloads(upstream: WheelContents, actual: WheelContents) -> None:
    expected = _normalized_members(upstream)
    observed = _normalized_members(actual)
    assert observed.keys() == expected.keys(), "Downstream wheel changed the installed member inventory"
    assert "DIST-INFO/entry_points.txt" in expected
    assert any(name.endswith(".py") for name in expected), "Source wheel has no Python payload"
    assert any("semgrep-core" in name for name in expected), "Source wheel has no native scanner payload"
    assert upstream.metadata.get_all("License-Expression") == ["LGPL-2.1-or-later"]
    for name, (payload, mode) in expected.items():
        assert observed[name][1] == mode, f"Downstream wheel changed member mode for {name}"
        if name not in {"DIST-INFO/METADATA", "DIST-INFO/RECORD"}:
            assert observed[name][0] == payload, f"Downstream wheel changed installed payload for {name}"


def test_selected_scanner_wheel_requires_patched_mcp(tmp_path: Path, pytestconfig: pytest.Config) -> None:
    upstream, actual, notice = _selected_scanner_artifact(tmp_path, pytestconfig.rootpath)
    _assert_scanner_metadata(upstream, actual, notice)
    _assert_scanner_payloads(upstream, actual)


def _malformed_members(fault: str) -> dict[str, bytes]:
    members = {
        "fixture-1.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: fixture\nVersion: 1.0\n",
        "fixture-1.0.dist-info/WHEEL": b"Wheel-Version: 1.0\nTag: py3-none-any\n",
        "fixture/data.txt": b"original data\n",
    }
    record_name = "fixture-1.0.dist-info/RECORD"
    rows: list[list[str]] = []
    for name, payload in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
        rows.append([name, f"sha256={digest}", str(len(payload))])
    rows.append([record_name, "", ""])
    if fault == "duplicate_record":
        rows.append(rows[0])
    record = io.StringIO(newline="")
    csv.writer(record).writerows(rows)
    members[record_name] = record.getvalue().encode("utf-8")
    mutations = {
        "traversal": {"../outside.txt": b"untrusted"},
        "extra_member": {"fixture/unrecorded.txt": b"untrusted"},
        "corrupt_payload": {"fixture/data.txt": b"changed data\n"},
        "wrong_identity": {"fixture-1.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: other\nVersion: 1.0\n"},
    }
    members.update(mutations.get(fault, {}))
    return members


def _write_fixture(path: Path, members: dict[str, bytes]) -> None:
    with ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _duplicate_fixture_member(path: Path) -> None:
    with ZipFile(path, "a") as archive, pytest.warns(UserWarning, match="Duplicate name"):
        archive.writestr("fixture/data.txt", b"duplicate")


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("duplicate_member", "Duplicate wheel member"),
        ("duplicate_record", "Duplicate wheel RECORD member"),
        ("traversal", "Unsafe wheel member"),
        ("extra_member", "RECORD does not cover"),
        ("corrupt_payload", "RECORD hash differs"),
        ("wrong_identity", "metadata name differs"),
    ],
)
def test_wheel_reader_rejects_malformed_artifacts(tmp_path: Path, fault: str, message: str) -> None:
    path = tmp_path / "fixture.whl"
    _write_fixture(path, _malformed_members(fault))
    if fault == "duplicate_member":
        _duplicate_fixture_member(path)
    with pytest.raises(AssertionError, match=message):
        _wheel(path, "fixture", "1.0")


def _description_wheel(description: str) -> WheelContents:
    root = "fixture-1.0.dist-info"
    metadata = b"Name: fixture\nVersion: 1.0\n\n" + description.encode()
    return WheelContents({f"{root}/METADATA": metadata}, {}, BytesParser().parsebytes(metadata), root)


@pytest.mark.parametrize("description", ["extra\napproved\nupstream\n", "approved\nupstream\nextra\n"])
def test_scanner_description_rejects_unreviewed_text(description: str) -> None:
    upstream = _description_wheel("upstream\n")
    actual = _description_wheel(description)
    with pytest.raises(AssertionError, match="Unreviewed downstream description change"):
        _assert_scanner_description(upstream, actual, "approved\n")


@pytest.mark.parametrize(
    "url",
    [
        "http://files.pythonhosted.org/data.whl",
        "https://example.org/data.whl",
        "https://user:password@files.pythonhosted.org/data.whl",
        "https://files.pythonhosted.org/data.whl?token=credential",
    ],
)
def test_artifact_download_rejects_unapproved_urls(tmp_path: Path, url: str) -> None:
    with pytest.raises(AssertionError, match=r"origin|queries"):
        _download(url, "a" * 64, tmp_path / "artifact.whl")
