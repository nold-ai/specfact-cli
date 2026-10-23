from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import ssl
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


def test_artifact_download_rejects_wrong_sha256(tmp_path: Path, pytestconfig: pytest.Config) -> None:
    _, url, _ = _certifi_selection(pytestconfig.rootpath)
    with pytest.raises(AssertionError, match="Downloaded artifact SHA256 differs from its pin"):
        _download(url, "0" * 64, tmp_path / "wrong-hash.whl")


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
    ids=["duplicate_member", "duplicate_record", "traversal", "extra_member", "corrupt_payload", "wrong_identity"],
)
def test_wheel_reader_rejects_malformed_artifacts(tmp_path: Path, fault: str, message: str) -> None:
    path = tmp_path / "fixture.whl"
    _write_fixture(path, _malformed_members(fault))
    if fault == "duplicate_member":
        _duplicate_fixture_member(path)
    with pytest.raises(AssertionError, match=message):
        _wheel(path, "fixture", "1.0")


@pytest.mark.parametrize(
    "url",
    [
        "http://files.pythonhosted.org/data.whl",
        "https://example.org/data.whl",
        "https://user:password@files.pythonhosted.org/data.whl",
        "https://files.pythonhosted.org/data.whl?token=credential",
    ],
    ids=["http", "other-host", "credentials", "query"],
)
def test_artifact_download_rejects_unapproved_urls(tmp_path: Path, url: str) -> None:
    with pytest.raises(AssertionError, match=r"origin|queries"):
        _download(url, "a" * 64, tmp_path / "artifact.whl")
