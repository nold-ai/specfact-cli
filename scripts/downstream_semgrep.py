"""Build exact Semgrep candidates and admit only independently protected artifacts.

This preinstallation boundary intentionally uses only the standard library.
Candidate validation never grants production installation or audit authority.
"""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
import io
import json
import re
import stat
import subprocess
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import cast
from urllib.parse import urlsplit


UPSTREAM_VERSION = "1.179.0"
DOWNSTREAM_VERSION = "1.179.0+specfact.1"
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
CHECKS = frozenset(
    {"install", "pip_check", "sast", "positive_control", "negative_control", "mcp_stdio", "mcp_lifecycle"}
)
REPOSITORY = "nold-ai/specfact-cli"
POLICY_PATH = "ci/downstream-semgrep-admissions.json"
_AUTHORITY = object()
_CANDIDATE_AUTHORITY = object()


class AdmissionError(ValueError):
    """An artifact, evidence record or advisory response cannot be trusted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def _object(value: object) -> dict[str, object]:
    _require(isinstance(value, dict) and all(isinstance(key, str) for key in value), "Expected a JSON object")
    return cast(dict[str, object], value)


def _list(value: object) -> list[object]:
    _require(isinstance(value, list), "Expected a JSON list")
    return cast(list[object], value)


def _text(value: object) -> str:
    _require(isinstance(value, str) and bool(value), "Expected a nonempty string")
    return cast(str, value)


def _digest(value: object, length: int = 64) -> str:
    result = _text(value)
    _require(re.fullmatch(f"[0-9a-f]{{{length}}}", result) is not None, "Invalid immutable digest")
    return result


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise AdmissionError(f"Invalid JSON numeric constant: {value}")


def _json(text: str) -> object:
    try:
        return cast(object, json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_json_constant))
    except (ValueError, TypeError) as exc:
        raise AdmissionError("Invalid JSON evidence") from exc


def _read(path: Path) -> bytes:
    try:
        _require(not path.is_symlink() and path.is_file(), f"Not a regular input file: {path}")
        return path.read_bytes()
    except OSError as exc:
        raise AdmissionError(f"Cannot read input: {path}") from exc


def _read_json(path: Path) -> object:
    try:
        return _json(_read(path).decode("utf-8"))
    except UnicodeError as exc:
        raise AdmissionError("Evidence must be UTF-8") from exc


@dataclass(frozen=True)
class _Wheel:
    filename: str
    platform: str
    upstream_sha256: str


@dataclass(frozen=True)
class _Recipe:
    sha256: str
    wheels: tuple[_Wheel, ...]
    python_versions: tuple[str, ...]


@dataclass(frozen=True)
class CandidateWheel:
    """Verified candidate bytes without production authority."""

    path: Path
    sha256: str
    platform: str
    recipe_sha256: str
    _upstream_sha256: str
    _authority: object

    def __post_init__(self) -> None:
        _require(self._authority is _CANDIDATE_AUTHORITY, "Candidate objects require archive verification")

    def candidate_audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput:
        """Prepare labeled candidate evidence without production admission."""
        _require(_sha(_read(self.path)) == self.sha256, "Candidate artifact has changed")
        return _audit_input(actual_requirements, output, self.sha256, self._upstream_sha256, _CANDIDATE_AUTHORITY)


def _recipe_wheel(value: object) -> _Wheel:
    item = _object(value)
    platform, filename = _text(item.get("platform_tag")), _text(item.get("filename"))
    _require(platform in PLATFORMS, "Unreviewed wheel platform")
    pattern = rf"semgrep-{re.escape(UPSTREAM_VERSION)}-[a-z0-9.]+-none-{re.escape(platform)}\.whl"
    _require(re.fullmatch(pattern, filename) is not None, "Unexpected upstream wheel filename")
    url = urlsplit(_text(item.get("upstream_url")))
    _require(
        url.scheme == "https"
        and url.netloc == "files.pythonhosted.org"
        and not url.query
        and not url.fragment
        and url.path.startswith("/packages/")
        and url.path.endswith("/" + filename),
        "Unexpected upstream origin",
    )
    return _Wheel(filename, platform, _digest(item.get("upstream_sha256")))


def _recipe(path: Path) -> _Recipe:
    raw = _read(path)
    try:
        payload = _object(_json(raw.decode("utf-8")))
    except UnicodeError as exc:
        raise AdmissionError("Recipe must be UTF-8") from exc
    expected = {
        "schema_version": 1,
        "package": "semgrep",
        "upstream_version": UPSTREAM_VERSION,
        "downstream_version": DOWNSTREAM_VERSION,
        "mcp_from": "1.29.0",
        "mcp_to": "1.30.0",
    }
    _require(all(payload.get(key) == value for key, value in expected.items()), "Unreviewed recipe identity")
    _digest(payload.get("build_runtime_digest"))
    versions = tuple(_text(value) for value in _list(payload.get("python_versions")))
    _require(len(versions) == 3 and set(versions) == {"3.11", "3.12", "3.13"}, "Incomplete Python matrix")
    wheels = [_recipe_wheel(value) for value in _list(payload.get("wheels"))]
    _require(
        len(wheels) == 7 and {wheel.platform for wheel in wheels} == PLATFORMS,
        "Incomplete or duplicate platform matrix",
    )
    return _Recipe(_sha(raw), tuple(wheels), versions)


def _wheel(recipe: _Recipe, upstream: Path) -> _Wheel:
    matches = [wheel for wheel in recipe.wheels if wheel.filename == upstream.name]
    _require(len(matches) == 1, "Wheel is absent from recipe")
    wheel = matches[0]
    _require(_sha(_read(upstream)) == wheel.upstream_sha256, "Upstream wheel digest differs")
    return wheel


def _record(entries: dict[str, tuple[zipfile.ZipInfo, bytes]], record_name: str) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    for name in sorted(entries):
        if name != record_name:
            content = entries[name][1]
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            writer.writerow((name, "sha256=" + digest, len(content)))
    writer.writerow((record_name, "", ""))
    return buffer.getvalue().encode()


def _verify_record(entries: dict[str, tuple[zipfile.ZipInfo, bytes]], record_name: str) -> None:
    _require(record_name in entries, "Missing wheel RECORD")
    try:
        rows = list(csv.reader(io.StringIO(entries[record_name][1].decode("utf-8")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise AdmissionError("Malformed wheel RECORD") from exc
    _require(all(len(row) == 3 for row in rows), "Malformed RECORD row")
    _require(len(rows) == len(entries) and {row[0] for row in rows} == set(entries), "RECORD is not bijective")
    for name, digest, size in rows:
        if name == record_name:
            _require((digest, size) == ("", ""), "RECORD cannot authenticate itself")
        else:
            content = entries[name][1]
            expected = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            _require(digest == "sha256=" + expected and size == str(len(content)), "Invalid RECORD digest or size")


def _validate_archive_member(info: zipfile.ZipInfo, roots: set[str]) -> str:
    name, parts = info.filename, PurePosixPath(info.filename).parts
    _require(
        bool(parts)
        and parts[0] in roots
        and not info.is_dir()
        and "\\" not in name
        and ":" not in name
        and "\x00" not in name
        and all(part not in {"", ".", ".."} for part in name.split("/")),
        "Unsafe archive path",
    )
    _require(stat.S_IFMT(info.external_attr >> 16) in {0, stat.S_IFREG}, "Linked or special archive member")
    _require(
        not (info.flag_bits & 1) and info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
        "Unsupported archive encoding",
    )
    _require(not name.endswith(("/RECORD.jws", "/RECORD.p7s")), "Embedded signatures cannot be retained")
    return name


def _archive(path: Path, version: str) -> dict[str, tuple[zipfile.ZipInfo, bytes]]:
    entries: dict[str, tuple[zipfile.ZipInfo, bytes]] = {}
    roots = {f"semgrep-{version}.dist-info", f"semgrep-{version}.data"}
    try:
        with zipfile.ZipFile(io.BytesIO(_read(path))) as archive:
            infos = archive.infolist()
            _require(
                len(infos) <= 10000 and sum(item.file_size for item in infos) <= 1024**3, "Wheel exceeds archive limits"
            )
            folded: set[str] = set()
            for info in infos:
                name = _validate_archive_member(info, roots)
                _require(name.casefold() not in folded, "Duplicate archive member")
                folded.add(name.casefold())
                entries[name] = (info, archive.read(info))
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise AdmissionError("Unreadable wheel archive") from exc
    _verify_record(entries, f"semgrep-{version}.dist-info/RECORD")
    return entries


def _transformed(upstream: Path) -> dict[str, tuple[zipfile.ZipInfo, bytes]]:
    entries = _archive(upstream, UPSTREAM_VERSION)
    metadata_name = f"semgrep-{UPSTREAM_VERSION}.dist-info/METADATA"
    _require(metadata_name in entries, "Missing wheel metadata")
    metadata = entries[metadata_name][1]
    replacements = (
        (b"Version: 1.179.0\n", b"Version: 1.179.0+specfact.1\n"),
        (b"Requires-Dist: mcp==1.29.0\n", b"Requires-Dist: mcp==1.30.0\n"),
    )
    for before, after in replacements:
        _require(metadata.count(before) == 1, "Unexpected metadata field cardinality")
        metadata = metadata.replace(before, after)
    lines = entries[metadata_name][1].split(b"\n\n", 1)[0].splitlines()
    _require(
        sum(line.startswith(b"Version:") for line in lines) == 1
        and sum(line.lower().startswith(b"requires-dist: mcp") for line in lines) == 1
        and lines.count(b"Name: semgrep") == 1,
        "Conflicting wheel metadata identity",
    )
    result: dict[str, tuple[zipfile.ZipInfo, bytes]] = {}
    for name, (original, content) in entries.items():
        renamed = name.replace(f"semgrep-{UPSTREAM_VERSION}.", f"semgrep-{DOWNSTREAM_VERSION}.", 1)
        info = copy.copy(original)
        info.filename, info.compress_type = renamed, zipfile.ZIP_STORED
        result[renamed] = (info, metadata if name == metadata_name else content)
    record_name = f"semgrep-{DOWNSTREAM_VERSION}.dist-info/RECORD"
    result[record_name] = (result[record_name][0], _record(result, record_name))
    return result


def build_candidate(recipe_path: Path, upstream_wheel: Path, output_directory: Path) -> CandidateWheel:
    """Build a reproducible metadata-only wheel without production admission."""
    recipe = _recipe(recipe_path)
    wheel = _wheel(recipe, upstream_wheel)
    entries = _transformed(upstream_wheel)
    filename = wheel.filename.replace(f"semgrep-{UPSTREAM_VERSION}-", f"semgrep-{DOWNSTREAM_VERSION}-", 1)
    output_directory.mkdir(parents=True, exist_ok=True)
    target = output_directory / filename
    _require(not target.exists() and not target.is_symlink(), "Candidate destination already exists")
    try:
        with target.open("xb") as handle, zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(entries):
                info, content = entries[name]
                archive.writestr(info, content)
    except (OSError, ValueError) as exc:
        raise AdmissionError("Candidate could not be written") from exc
    return CandidateWheel(
        target, _sha(_read(target)), wheel.platform, recipe.sha256, wheel.upstream_sha256, _CANDIDATE_AUTHORITY
    )


def verify_candidate(recipe_path: Path, upstream_wheel: Path, candidate_wheel: Path) -> CandidateWheel:
    """Reject every archive change outside the exact reviewed metadata repair."""
    recipe = _recipe(recipe_path)
    wheel = _wheel(recipe, upstream_wheel)
    expected_name = wheel.filename.replace(f"semgrep-{UPSTREAM_VERSION}-", f"semgrep-{DOWNSTREAM_VERSION}-", 1)
    _require(candidate_wheel.name == expected_name, "Unexpected candidate filename")
    expected, actual = _transformed(upstream_wheel), _archive(candidate_wheel, DOWNSTREAM_VERSION)
    _require(set(actual) == set(expected), "Candidate archive members differ")
    for name, (info, content) in expected.items():
        observed, data = actual[name]
        _require(data == content, f"Candidate payload changed: {name}")
        _require(
            all(
                getattr(info, field) == getattr(observed, field)
                for field in ("external_attr", "internal_attr", "create_system", "date_time", "extra", "comment")
            ),
            "Candidate archive attributes changed",
        )
    return CandidateWheel(
        candidate_wheel,
        _sha(_read(candidate_wheel)),
        wheel.platform,
        recipe.sha256,
        wheel.upstream_sha256,
        _CANDIDATE_AUTHORITY,
    )


def required_matrix(recipe_path: Path) -> list[dict[str, str]]:
    """Return the complete execution matrix derived from the validated recipe."""
    recipe = _recipe(recipe_path)
    return [
        {"platform": wheel.platform, "python_version": version}
        for wheel in recipe.wheels
        for version in recipe.python_versions
    ]


def aggregate_candidate_reports(recipe_path: Path, reports: list[dict[str, object]]) -> dict[str, object]:
    """Require every native cell, without converting candidate evidence into trust."""
    recipe = _recipe(recipe_path)
    expected = {(wheel.platform, version): wheel for wheel in recipe.wheels for version in recipe.python_versions}
    seen: set[tuple[str, str]] = set()
    hashes: dict[str, str] = {}
    source_commits: set[str] = set()
    for value in reports:
        report = _object(value)
        key = (_text(report.get("platform")), _text(report.get("python_version")))
        _require(key in expected and key not in seen, "Unknown or duplicate matrix cell")
        seen.add(key)
        _require(
            report.get("status") == "passed" and report.get("native") is True,
            "Cell did not execute successfully on native platform",
        )
        _require(report.get("source_dirty") is False, "Matrix source checkout is dirty")
        source_commits.add(_digest(report.get("source_commit"), 40))
        checks = _object(report.get("checks"))
        _require(all(checks.get(check) is True for check in CHECKS), "Required cell check missing or failed")
        _require(
            report.get("recipe_sha256") == recipe.sha256
            and report.get("upstream_sha256") == expected[key].upstream_sha256,
            "Cell input binding differs",
        )
        digest = _digest(report.get("candidate_sha256"))
        _require(hashes.get(key[0], digest) == digest, "Platform cells used different candidate artifacts")
        hashes[key[0]] = digest
    _require(seen == set(expected), "Missing required matrix cells")
    _require(len(source_commits) == 1, "Matrix cells used different source commits")
    return {
        "status": "passed",
        "production_admission": "not_requested",
        "recipe_sha256": recipe.sha256,
        "artifacts": hashes,
        "source_commit": next(iter(source_commits)),
    }


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdmissionError("Trusted verifier or GitHub API is unavailable") from exc
    _require(result.returncode == 0, "Trusted verifier or GitHub API rejected the request")
    return result


def _fetch_protected_policy() -> dict[str, object]:
    branch = _object(_json(_run(["gh", "api", "--hostname", "github.com", f"repos/{REPOSITORY}/branches/dev"]).stdout))
    _require(branch.get("protected") is True, "Canonical dev branch is not protected")
    commit = _digest(_object(branch.get("commit")).get("sha"), 40)
    response = _object(
        _json(
            _run(
                ["gh", "api", "--hostname", "github.com", f"repos/{REPOSITORY}/contents/{POLICY_PATH}?ref={commit}"]
            ).stdout
        )
    )
    _require(
        response.get("encoding") == "base64" and response.get("path") == POLICY_PATH and response.get("type") == "file",
        "Unexpected canonical policy response",
    )
    try:
        content = base64.b64decode("".join(_text(response.get("content")).split()), validate=True).decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise AdmissionError("Invalid protected policy encoding") from exc
    return _object(_json(content))


def _verify_provenance(wheel: Path, bundle: Path, source_commit: str, signer_commit: str) -> None:
    _read(bundle)
    result = _run(
        [
            "gh",
            "attestation",
            "verify",
            str(wheel.resolve()),
            "--hostname",
            "github.com",
            "--repo",
            REPOSITORY,
            "--signer-repo",
            REPOSITORY,
            "--signer-workflow",
            f"{REPOSITORY}/.github/workflows/downstream-semgrep.yml",
            "--source-ref",
            "refs/heads/dev",
            "--source-digest",
            _digest(source_commit, 40),
            "--signer-digest",
            _digest(signer_commit, 40),
            "--cert-oidc-issuer",
            "https://token.actions.githubusercontent.com",
            "--deny-self-hosted-runners",
            "--bundle",
            str(bundle.resolve()),
            "--format",
            "json",
        ]
    )
    _require(bool(_list(_json(result.stdout))), "Verifier returned no verified attestations")


def _approval(policy: dict[str, object], recipe: _Recipe, matrix_sha256: str) -> dict[str, object]:
    _require(policy.get("schema_version") == 1, "Unsupported protected policy schema")
    matches = [
        _object(value)
        for value in _list(policy.get("admissions"))
        if _object(value).get("recipe_sha256") == recipe.sha256
    ]
    _require(len(matches) == 1, "Recipe has no unique protected approval")
    approval = matches[0]
    _require(approval.get("matrix_sha256") == matrix_sha256, "Matrix is not independently approved")
    try:
        reviewed = date.fromisoformat(_text(approval.get("reviewed_on")))
        expires = date.fromisoformat(_text(approval.get("expires_on")))
    except ValueError as exc:
        raise AdmissionError("Invalid approval validity interval") from exc
    _require(reviewed <= date.today() <= expires, "Protected approval is not currently valid")
    _digest(approval.get("source_commit"), 40)
    _digest(approval.get("signer_commit"), 40)
    return approval


def _approved_artifacts(
    approval: dict[str, object], recipe: _Recipe, matrix: dict[str, object]
) -> dict[str, dict[str, object]]:
    artifacts: dict[str, dict[str, object]] = {}
    for value in _list(approval.get("artifacts")):
        artifact = _object(value)
        platform = _text(artifact.get("platform_tag"))
        _require(platform not in artifacts, "Duplicate approved artifact")
        artifacts[platform] = artifact
    _require(set(artifacts) == PLATFORMS, "Incomplete protected artifact set")
    hashes = _object(matrix.get("artifacts"))
    for wheel in recipe.wheels:
        item = artifacts[wheel.platform]
        expected = wheel.filename.replace(f"semgrep-{UPSTREAM_VERSION}-", f"semgrep-{DOWNSTREAM_VERSION}-", 1)
        _require(
            item.get("filename") == expected
            and item.get("upstream_sha256") == wheel.upstream_sha256
            and item.get("candidate_sha256") == hashes[wheel.platform],
            "Approved artifact does not match tested wheel",
        )
    return artifacts


def admit_artifact(wheel: Path, evidence_bundle: Path) -> AdmittedWheel:
    """Authenticate artifact identity without waiving any existing trust or delivery gate."""
    recipe_path, matrix_path = evidence_bundle / "recipe.json", evidence_bundle / "matrix.json"
    recipe = _recipe(recipe_path)
    approval = _approval(_fetch_protected_policy(), recipe, _sha(_read(matrix_path)))
    reports = [_object(value) for value in _list(_read_json(matrix_path))]
    matrix = aggregate_candidate_reports(recipe_path, reports)
    _require(matrix["source_commit"] == approval["source_commit"], "Approved source differs from matrix source")
    artifacts = _approved_artifacts(approval, recipe, matrix)
    matches = [item for item in artifacts.values() if item["filename"] == wheel.name]
    _require(
        len(matches) == 1 and matches[0]["candidate_sha256"] == _sha(_read(wheel)),
        "Candidate bytes have no protected approval",
    )
    artifact = matches[0]
    upstream_name = wheel.name.replace(f"semgrep-{DOWNSTREAM_VERSION}-", f"semgrep-{UPSTREAM_VERSION}-", 1)
    verified = verify_candidate(recipe_path, evidence_bundle / "upstream" / upstream_name, wheel)
    _verify_provenance(
        wheel, evidence_bundle / "provenance.jsonl", _text(approval["source_commit"]), _text(approval["signer_commit"])
    )
    _require(_sha(_read(wheel)) == verified.sha256, "Artifact changed during admission")
    return AdmittedWheel(wheel, verified.sha256, _text(artifact["upstream_sha256"]), _AUTHORITY)


def _inventory(path: Path) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    try:
        lines = _read(path).decode("utf-8").splitlines(keepends=True)
    except UnicodeError as exc:
        raise AdmissionError("Requirements must be UTF-8") from exc
    inventory: dict[str, str] = {}
    hashes: dict[str, list[str]] = {}
    pattern = r"([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)( +--hash=sha256:[0-9a-f]{64})+"
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.fullmatch(pattern, stripped)
        _require(match is not None, "Requirements must be flat exact hash-pinned identities without markers or options")
        assert match is not None
        name = re.sub(r"[-_.]+", "-", match[1]).lower()
        _require(name not in inventory, "Duplicate inventory identity")
        inventory[name] = match[2]
        hashes[name] = re.findall(r"--hash=sha256:([0-9a-f]{64})", stripped)
    _require(bool(inventory), "Empty actual inventory")
    return inventory, hashes, lines


@dataclass(frozen=True)
class AdmittedWheel:
    """Exact admitted bytes; constructing this object requires the private authority."""

    wheel: Path
    _sha256: str
    _upstream_sha256: str
    _authority: object

    def __post_init__(self) -> None:
        _require(self._authority is _AUTHORITY, "Admission objects require protected verification")

    def audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput:
        """Map only this approved Semgrep artifact; retain every actual dependency."""
        _require(_sha(_read(self.wheel)) == self._sha256, "Admitted artifact has changed")
        return _audit_input(actual_requirements, output, self._sha256, self._upstream_sha256, _AUTHORITY)


def _audit_input(
    actual: Path, output: Path, candidate_sha256: str, upstream_sha256: str, authority: object
) -> BoundAuditInput:
    inventory, hashes, lines = _inventory(actual)
    _require(
        inventory.get("semgrep") == DOWNSTREAM_VERSION and hashes.get("semgrep") == [candidate_sha256],
        "Inventory does not bind this downstream artifact",
    )
    mcp = inventory.get("mcp", "")
    _require(
        re.fullmatch(r"1\.\d+\.\d+", mcp) is not None and tuple(int(part) for part in mcp.split(".")) >= (1, 30, 0),
        "MCP is below the fixed 1.x security floor",
    )
    _require(
        output.resolve() != actual.resolve() and not output.exists() and not output.is_symlink(),
        "Audit output must be a new separate file",
    )
    rendered = "".join(
        f"semgrep=={UPSTREAM_VERSION} --hash=sha256:{upstream_sha256}\n"
        if re.match(r"(?i)^semgrep==", line.lstrip())
        else line
        for line in lines
    )
    try:
        with output.open("x", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
    except OSError as exc:
        raise AdmissionError("Cannot write separate audit input") from exc
    return BoundAuditInput(output, MappingProxyType(inventory), _sha(rendered.encode()), authority)


@dataclass(frozen=True)
class BoundAuditInput:
    """An upstream query identity bound to the complete actual dependency graph."""

    requirements: Path
    actual_inventory: Mapping[str, str]
    _sha256: str
    _authority: object

    def __post_init__(self) -> None:
        _require(
            self._authority is _AUTHORITY or self._authority is _CANDIDATE_AUTHORITY,
            "Audit binding requires verified artifact evidence",
        )

    def assert_complete_result(self, proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
        """Reject every incomplete, failed or vulnerable strict audit response."""
        _require(_sha(_read(self.requirements)) == self._sha256, "Audit input changed after binding")
        _require(
            proc.returncode == 0 and proc.stderr.strip() in {"", "No known vulnerabilities found"},
            "Advisory lookup failed or emitted diagnostics",
        )
        data = _json(proc.stdout)
        dependencies = _list(data if isinstance(data, list) else _object(data).get("dependencies"))
        expected = dict(self.actual_inventory)
        expected["semgrep"] = UPSTREAM_VERSION
        observed: dict[str, str] = {}
        for value in dependencies:
            dependency = _object(value)
            _require("skip_reason" not in dependency, "Audit skipped a dependency")
            name = re.sub(r"[-_.]+", "-", _text(dependency.get("name"))).lower()
            version = _text(dependency.get("version"))
            _require(
                name not in observed and expected.get(name) == version, "Unexpected or duplicate advisory identity"
            )
            _require(_list(dependency.get("vulns")) == [], "Vulnerability or malformed advisory reported")
            observed[name] = version
        _require(observed == expected, "Advisory coverage is incomplete")
        return {
            "status": "passed",
            "actual_inventory": dict(self.actual_inventory),
            "queried_inventory": observed,
            "production_admission": "admitted" if self._authority is _AUTHORITY else "not_requested",
        }
