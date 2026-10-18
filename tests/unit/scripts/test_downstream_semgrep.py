from __future__ import annotations

import base64
import copy
import csv
import hashlib
import importlib.util
import io
import json
import stat
import subprocess
import sys
import warnings
import zipfile
from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import NotRequired, Protocol, TypedDict, cast
from unittest.mock import patch

import pytest


class BoundAuditInput(Protocol):
    @property
    def requirements(self) -> Path: ...

    @property
    def actual_inventory(self) -> Mapping[str, str]: ...

    def assert_complete_result(self, proc: subprocess.CompletedProcess[str]) -> dict[str, object]: ...


class CandidateWheel(Protocol):
    @property
    def path(self) -> Path: ...

    @property
    def sha256(self) -> str: ...

    @property
    def platform(self) -> str: ...

    @property
    def recipe_sha256(self) -> str: ...

    def candidate_audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput: ...


class AdmittedWheel(Protocol):
    @property
    def wheel(self) -> Path: ...

    def audit_input(self, actual_requirements: Path, output: Path) -> BoundAuditInput: ...


class WheelEntry(TypedDict):
    filename: str
    platform_tag: str
    upstream_sha256: str
    upstream_url: str


class Recipe(TypedDict):
    schema_version: int
    package: str
    upstream_version: str
    downstream_version: str
    mcp_from: str
    mcp_to: str
    python_versions: list[str]
    build_runtime_policy: dict[str, object]
    build_runtime_digest: str
    wheels: list[WheelEntry]


class NativeRuntime(TypedDict):
    system: str
    machine: str
    python_version: str
    python_executable: str
    sysconfig_platform: str
    python_executable_sha256: str
    libc: list[str]


class CommandEvidence(TypedDict):
    argv: list[str]
    returncode: int
    stdout_sha256: str
    stderr_sha256: str


class MatrixReport(TypedDict):
    runtime: NativeRuntime
    commands: list[CommandEvidence]
    source_commit: str
    source_dirty: bool
    platform: str
    python_version: str
    candidate_sha256: str
    upstream_sha256: str
    recipe_sha256: str
    status: str
    native: bool
    candidate_audit_passed: bool
    control_expected_cve_confirmed: bool
    control_expected_regression_confirmed: bool
    checks: dict[str, bool]


class Artifact(TypedDict):
    filename: str
    candidate_sha256: str
    upstream_sha256: str
    platform_tag: str


class Approval(TypedDict):
    recipe_sha256: str
    matrix_sha256: str
    source_commit: str
    signer_commit: str
    reviewed_on: str
    expires_on: str
    artifacts: list[Artifact]


class Policy(TypedDict):
    schema_version: int
    admissions: list[Approval]


class AuditDependency(TypedDict):
    name: str
    version: str
    vulns: list[object]
    skip_reason: NotRequired[str]


class AuditResult(TypedDict):
    dependencies: list[AuditDependency]


class DownstreamModule(Protocol):
    subprocess: ModuleType

    def build_candidate(self, recipe_path: Path, upstream_wheel: Path, output_directory: Path) -> CandidateWheel: ...

    def verify_candidate(self, recipe_path: Path, upstream_wheel: Path, candidate_wheel: Path) -> CandidateWheel: ...

    def required_matrix(self, recipe_path: Path) -> list[dict[str, str]]: ...

    def aggregate_candidate_reports(self, recipe_path: Path, reports: list[MatrixReport]) -> dict[str, object]: ...

    def admit_artifact(self, wheel: Path, evidence_bundle: Path) -> AdmittedWheel: ...


WheelRecipe = tuple[Path, Recipe, Path]
WheelMember = tuple[str, bytes, int]


PLATFORMS = (
    "macosx_10_14_x86_64",
    "macosx_11_0_arm64",
    "manylinux_2_34_x86_64",
    "manylinux_2_34_aarch64",
    "musllinux_1_2_x86_64",
    "musllinux_1_2_aarch64",
    "win_amd64",
)
UPSTREAM = "1.179.0"
DOWNSTREAM = "1.179.0+specfact.1"
TAGS = "cp310.cp311.cp312.cp313.cp314.py310.py311.py312.py313.py314-none"


def _module() -> DownstreamModule:
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts/downstream_semgrep.py"
    assert path.is_file(), f"Downstream admission boundary is absent: {path}"
    spec = importlib.util.spec_from_file_location("_downstream_semgrep_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(DownstreamModule, module)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _members(version: str = UPSTREAM) -> list[tuple[str, bytes, int]]:
    prefix = f"semgrep-{version}.dist-info/"
    return [
        (
            prefix + "METADATA",
            f"Metadata-Version: 2.1\nName: semgrep\nVersion: {version}\nRequires-Dist: mcp==1.29.0\nRequires-Dist: click>=8\nLicense: LGPL-2.1\n\nSynthetic fixture\n".encode(),
            0o100644,
        ),
        (
            prefix + "WHEEL",
            (
                "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: false\n"
                + "".join(f"Tag: {tag}-none-{PLATFORMS[0]}\n" for tag in TAGS.removesuffix("-none").split("."))
            ).encode(),
            0o100644,
        ),
        (prefix + "entry_points.txt", b"[console_scripts]\nsemgrep = semgrep.main:main\n", 0o100644),
        (prefix + "licenses/LICENSE", b"Synthetic license fixture\n", 0o100644),
        (f"semgrep-{version}.data/purelib/semgrep/main.py", b"def main():\n    return 7\n", 0o100644),
        (f"semgrep-{version}.data/purelib/semgrep/bin/semgrep-core", b"synthetic-native-payload\x00", 0o100755),
    ]


def _write_wheel(path: Path, members: list[tuple[str, bytes, int]], version: str = UPSTREAM) -> None:
    record_path = f"semgrep-{version}.dist-info/RECORD"
    rows: list[tuple[str, str, str]] = []
    for name, content, _mode in members:
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
        rows.append((name, "sha256=" + digest, str(len(content))))
    rows.append((record_path, "", ""))
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w") as archive:
            for name, content, mode in [*members, (record_path, record.getvalue().encode(), 0o100644)]:
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = mode << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)


@pytest.fixture
def wheel_recipe(tmp_path: Path) -> WheelRecipe:
    upstream = tmp_path / f"semgrep-{UPSTREAM}-{TAGS}-{PLATFORMS[0]}.whl"
    _write_wheel(upstream, _members())
    runtime_policy: dict[str, object] = {
        "implementation": "CPython",
        "python_versions": ["3.11", "3.12", "3.13"],
        "wheel_compression": "ZIP_STORED",
    }
    recipe: Recipe = {
        "schema_version": 1,
        "package": "semgrep",
        "upstream_version": UPSTREAM,
        "downstream_version": DOWNSTREAM,
        "mcp_from": "1.29.0",
        "mcp_to": "1.30.0",
        "python_versions": ["3.11", "3.12", "3.13"],
        "build_runtime_policy": runtime_policy,
        "build_runtime_digest": _sha(json.dumps(runtime_policy, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "wheels": [
            {
                "filename": f"semgrep-{UPSTREAM}-{TAGS}-{platform}.whl",
                "platform_tag": platform,
                "upstream_sha256": _sha(upstream.read_bytes()) if platform == PLATFORMS[0] else "b" * 64,
                "upstream_url": f"https://files.pythonhosted.org/packages/test/semgrep-{UPSTREAM}-{TAGS}-{platform}.whl",
            }
            for platform in PLATFORMS
        ],
    }
    recipe_path = _write_json(tmp_path / "recipe.json", recipe)
    return recipe_path, recipe, upstream


def _assert_record(archive: zipfile.ZipFile) -> None:
    names = archive.namelist()
    assert len(names) == len(set(names))
    record_name = f"semgrep-{DOWNSTREAM}.dist-info/RECORD"
    rows = list(csv.reader(io.StringIO(archive.read(record_name).decode())))
    assert len(rows) == len(names)
    assert {row[0] for row in rows} == set(names)
    for name, digest, size in rows:
        if name == record_name:
            assert (digest, size) == ("", "")
        else:
            content = archive.read(name)
            assert digest == "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            assert size == str(len(content))


def _assert_metadata_transform(original: zipfile.ZipFile, built: zipfile.ZipFile) -> None:
    expected = (
        original.read(f"semgrep-{UPSTREAM}.dist-info/METADATA")
        .replace(b"Version: 1.179.0\n", b"Version: 1.179.0+specfact.1\n")
        .replace(b"Requires-Dist: mcp==1.29.0\n", b"Requires-Dist: mcp==1.30.0\n")
    )
    assert built.read(f"semgrep-{DOWNSTREAM}.dist-info/METADATA") == expected


def _assert_runtime_preserved(upstream: Path, candidate: Path) -> None:
    with zipfile.ZipFile(upstream) as original, zipfile.ZipFile(candidate) as built:
        _assert_record(built)
        expected_names = {
            name.replace(f"semgrep-{UPSTREAM}.", f"semgrep-{DOWNSTREAM}.", 1) for name in original.namelist()
        }
        assert set(built.namelist()) == expected_names
        for name in original.namelist():
            renamed = name.replace(f"semgrep-{UPSTREAM}.", f"semgrep-{DOWNSTREAM}.", 1)
            assert built.getinfo(renamed).external_attr == original.getinfo(name).external_attr
            if not name.endswith(("/METADATA", "/RECORD")):
                assert built.read(renamed) == original.read(name)
        _assert_metadata_transform(original, built)


def test_build_is_reproducible_and_preserves_complete_runtime(wheel_recipe: WheelRecipe, tmp_path: Path) -> None:
    module = _module()
    recipe_path, _recipe, upstream = wheel_recipe
    one = module.build_candidate(recipe_path, upstream, tmp_path / "one")
    two = module.build_candidate(recipe_path, upstream, tmp_path / "two")
    assert one.path.read_bytes() == two.path.read_bytes()
    assert one.sha256 == _sha(one.path.read_bytes())
    assert one.recipe_sha256 == _sha(recipe_path.read_bytes())
    assert one.platform == PLATFORMS[0]
    _assert_runtime_preserved(upstream, one.path)
    verified = module.verify_candidate(recipe_path, upstream, one.path)
    assert (verified.path, verified.sha256, verified.platform) == (one.path, one.sha256, one.platform)
    _assert_crlf_build(module, wheel_recipe, tmp_path)


def _assert_crlf_build(module: DownstreamModule, wheel_recipe: WheelRecipe, tmp_path: Path) -> None:
    recipe_path, _recipe, upstream = wheel_recipe
    members = [
        (name, content.replace(b"\n", b"\r\n") if name.endswith("/METADATA") else content, mode)
        for name, content, mode in _members()
    ]
    _write_wheel(upstream, members)
    recipe = _recipe
    recipe["wheels"][0]["upstream_sha256"] = _sha(upstream.read_bytes())
    _write_json(recipe_path, recipe)
    windows_one = module.build_candidate(recipe_path, upstream, tmp_path / "crlf-one")
    windows_two = module.build_candidate(recipe_path, upstream, tmp_path / "crlf-two")
    assert windows_one.path.read_bytes() == windows_two.path.read_bytes()
    with zipfile.ZipFile(windows_one.path) as built:
        observed = built.read(f"semgrep-{DOWNSTREAM}.dist-info/METADATA")
    expected = next(content for name, content, _ in members if name.endswith("/METADATA"))
    expected = expected.replace(b"Version: 1.179.0\r\n", b"Version: 1.179.0+specfact.1\r\n")
    expected = expected.replace(b"Requires-Dist: mcp==1.29.0\r\n", b"Requires-Dist: mcp==1.30.0\r\n")
    assert observed == expected
    assert module.verify_candidate(recipe_path, upstream, windows_one.path).sha256 == windows_one.sha256


def test_wrong_upstream_hash_cannot_write_candidate(wheel_recipe: WheelRecipe, tmp_path: Path) -> None:
    module = _module()
    recipe_path, _recipe, upstream = wheel_recipe
    upstream.write_bytes(upstream.read_bytes() + b"tamper")
    output = tmp_path / "output"
    with pytest.raises(ValueError):
        module.build_candidate(recipe_path, upstream, output)
    assert not list(output.glob("*.whl"))


def _corrupt_record(upstream: Path) -> None:
    with zipfile.ZipFile(upstream) as archive:
        entries = [(item, archive.read(item)) for item in archive.infolist()]
    with zipfile.ZipFile(upstream, "w") as archive:
        for item, content in entries:
            archive.writestr(item, b"wrong,sha256=bad,1\n" if item.filename.endswith("/RECORD") else content)


def _damage_upstream(upstream: Path, damage: str) -> None:
    members = _members()
    if damage == "duplicate":
        members.append(members[-1])
    if damage == "traversal":
        members.append(("../escape", b"outside", 0o100644))
    if damage == "symlink":
        members.append(("semgrep-link", b"/tmp/outside", stat.S_IFLNK | 0o777))
    if damage == "signature":
        members.append((f"semgrep-{UPSTREAM}.dist-info/RECORD.jws", b"stale-signature", 0o100644))
    if damage == "duplicate-mcp":
        name, content, mode = members[0]
        members[0] = (name, content.replace(b"Requires-Dist: mcp==1.29.0\n", b"Requires-Dist: mcp==1.29.0\n" * 2), mode)
    _write_wheel(upstream, members)
    if damage == "bad-record":
        _corrupt_record(upstream)


@pytest.mark.parametrize(
    "damage", ["duplicate", "traversal", "symlink", "signature", "bad-record", "duplicate-mcp"], ids=str
)
def test_unsafe_upstream_archive_rejects_even_with_reviewed_hash(
    wheel_recipe: WheelRecipe, tmp_path: Path, damage: str
) -> None:
    module = _module()
    recipe_path, recipe, upstream = wheel_recipe
    _damage_upstream(upstream, damage)
    recipe["wheels"][0]["upstream_sha256"] = _sha(upstream.read_bytes())
    _write_json(recipe_path, recipe)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError):
        module.build_candidate(recipe_path, upstream, output)
    assert not list(output.glob("*.whl"))
    assert not (tmp_path / "escape").exists()


def _changed_member(member: WheelMember, damage: str) -> WheelMember:
    name, content, mode = member
    if damage == "runtime":
        return name, b"raise RuntimeError('changed')\n", mode
    if damage == "mode":
        return name, content, 0o100644
    if damage == "entrypoint":
        return name, b"[console_scripts]\nsemgrep = evil:main\n", mode
    return name, content.replace(b"click>=8", b"click>=1"), mode


def _damage_candidate(candidate: Path, damage: str) -> None:
    with zipfile.ZipFile(candidate) as archive:
        members = [
            (item.filename, archive.read(item), item.external_attr >> 16)
            for item in archive.infolist()
            if not item.filename.endswith("/RECORD")
        ]
    target = {
        "runtime": "main.py",
        "mode": "semgrep-core",
        "entrypoint": "entry_points.txt",
        "other-metadata": "/METADATA",
    }[damage]
    for index, member in enumerate(members):
        if member[0].endswith(target):
            members[index] = _changed_member(member, damage)
    _write_wheel(candidate, members, DOWNSTREAM)


@pytest.mark.parametrize("damage", ["runtime", "mode", "entrypoint", "other-metadata"], ids=str)
def test_candidate_rejects_unauthorized_change_with_valid_record(
    wheel_recipe: WheelRecipe, tmp_path: Path, damage: str
) -> None:
    module = _module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    _damage_candidate(candidate.path, damage)
    with pytest.raises(ValueError):
        module.verify_candidate(recipe_path, upstream, candidate.path)


@pytest.mark.parametrize(
    "version",
    ["1.179.0+attacker.1", "1.179.0", "1.174.0+specfact.1"],
    ids=["unknown-local", "masquerade", "below-floor"],
)
def test_unreviewed_downstream_identity_rejects(wheel_recipe: WheelRecipe, tmp_path: Path, version: str) -> None:
    module = _module()
    recipe_path, recipe, upstream = wheel_recipe
    recipe["downstream_version"] = version
    _write_json(recipe_path, recipe)
    with pytest.raises(ValueError):
        module.build_candidate(recipe_path, upstream, tmp_path / "output")


def test_matrix_requires_all_seven_platforms_and_three_interpreters(wheel_recipe: WheelRecipe) -> None:
    module = _module()
    recipe_path, _recipe, _upstream = wheel_recipe
    matrix = module.required_matrix(recipe_path)
    assert len(matrix) == 21
    assert {(cell["platform"], cell["python_version"]) for cell in matrix} == {
        (platform, python) for platform in PLATFORMS for python in ("3.11", "3.12", "3.13")
    }


def _synthetic_runtime(platform: str, python: str) -> NativeRuntime:
    system, machine, sysconfig_platform, libc = {
        "macosx_10_14_x86_64": ("Darwin", "x86_64", "macosx-10.9-universal2", ["", ""]),
        "macosx_11_0_arm64": ("Darwin", "arm64", "macosx-10.9-universal2", ["", ""]),
        "manylinux_2_34_x86_64": ("Linux", "x86_64", "linux-x86_64", ["glibc", "2.39"]),
        "manylinux_2_34_aarch64": ("Linux", "aarch64", "linux-aarch64", ["glibc", "2.39"]),
        "musllinux_1_2_x86_64": ("Linux", "x86_64", "linux-x86_64", ["musl", "Version 1.2"]),
        "musllinux_1_2_aarch64": ("Linux", "aarch64", "linux-aarch64", ["musl", "Version 1.2"]),
        "win_amd64": ("Windows", "AMD64", "win-amd64", ["", ""]),
    }[platform]
    return {
        "system": system,
        "machine": machine,
        "python_version": f"{python}.9",
        "python_executable": "C:/synthetic/python.exe" if system == "Windows" else "/synthetic/bin/python",
        "sysconfig_platform": sysconfig_platform,
        "python_executable_sha256": _sha(f"synthetic interpreter {platform} {python}".encode()),
        "libc": libc,
    }


def _reports(recipe_path: Path, recipe: Recipe) -> list[MatrixReport]:
    """Build deterministic synthetic evidence, never native execution or provenance."""
    return [
        {
            "platform": wheel["platform_tag"],
            "python_version": python,
            "runtime": _synthetic_runtime(wheel["platform_tag"], python),
            "commands": [
                {
                    "argv": ["synthetic-python", "-m", "pip", "check"],
                    "returncode": 0,
                    "stdout_sha256": _sha(b"synthetic pip check output"),
                    "stderr_sha256": _sha(b""),
                },
                {
                    "argv": ["synthetic-python", "-m", "pip_audit"],
                    "returncode": 1,
                    "stdout_sha256": _sha(b"synthetic expected control vulnerability"),
                    "stderr_sha256": _sha(b""),
                },
            ],
            "candidate_sha256": "c" * 64,
            "upstream_sha256": wheel["upstream_sha256"],
            "recipe_sha256": _sha(recipe_path.read_bytes()),
            "status": "passed",
            "native": True,
            "source_commit": "d" * 40,
            "source_dirty": False,
            "candidate_audit_passed": True,
            "control_expected_cve_confirmed": True,
            "control_expected_regression_confirmed": True,
            "checks": dict.fromkeys(
                ("install", "pip_check", "sast", "positive_control", "negative_control", "mcp_stdio", "mcp_lifecycle"),
                True,
            ),
        }
        for wheel in recipe["wheels"]
        for python in recipe["python_versions"]
    ]


def _damage_matrix(reports: list[MatrixReport], damage: str) -> None:
    if damage == "missing":
        reports.pop()
        return
    if damage == "duplicate":
        reports[-1] = copy.deepcopy(reports[0])
        return
    if damage == "failed":
        reports[-1]["status"] = "failed"
        return
    if damage == "emulated":
        reports[-1]["native"] = False
        return
    reports[-1]["checks"]["mcp_lifecycle"] = False


@pytest.mark.parametrize("damage", ["missing", "duplicate", "failed", "emulated", "skipped-check"], ids=str)
def test_matrix_rejects_incomplete_or_non_native_evidence(wheel_recipe: WheelRecipe, damage: str) -> None:
    module = _module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = _reports(recipe_path, recipe)
    _damage_matrix(reports, damage)
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


def test_complete_candidate_matrix_does_not_grant_production_admission(wheel_recipe: WheelRecipe) -> None:
    module = _module()
    recipe_path, recipe, _upstream = wheel_recipe
    report = module.aggregate_candidate_reports(recipe_path, _reports(recipe_path, recipe))
    assert report["production_admission"] == "not_requested"
    assert report["status"] == "passed"
    for evidence in (
        "candidate_audit_passed",
        "control_expected_cve_confirmed",
        "control_expected_regression_confirmed",
    ):
        incomplete: dict[str, object] = dict(_reports(recipe_path, recipe)[0])
        incomplete[evidence] = False
        damaged = _reports(recipe_path, recipe)
        damaged[0] = cast(MatrixReport, incomplete)
        with pytest.raises(ValueError):
            module.aggregate_candidate_reports(recipe_path, damaged)
    reports = _reports(recipe_path, recipe)
    reports[0]["source_dirty"] = True
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)
    reports[0]["source_dirty"] = False
    reports[0]["source_commit"] = "e" * 40
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


def _protected_fixture(
    module: DownstreamModule, wheel_recipe: WheelRecipe, tmp_path: Path
) -> tuple[CandidateWheel, Path, Policy]:
    recipe_path, recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    bundle = tmp_path / "evidence"
    (bundle / "upstream").mkdir(parents=True)
    (bundle / "recipe.json").write_bytes(recipe_path.read_bytes())
    (bundle / "upstream" / upstream.name).write_bytes(upstream.read_bytes())
    (bundle / "provenance.jsonl").write_text('{"synthetic": "not cryptographically verified"}\n')
    reports = _reports(recipe_path, recipe)
    for report in reports:
        if report["platform"] == PLATFORMS[0]:
            report["candidate_sha256"] = candidate.sha256
    matrix = _write_json(bundle / "matrix.json", reports)
    policy: Policy = {
        "schema_version": 1,
        "admissions": [
            {
                "recipe_sha256": _sha(recipe_path.read_bytes()),
                "matrix_sha256": _sha(matrix.read_bytes()),
                "source_commit": "d" * 40,
                "signer_commit": "e" * 40,
                "reviewed_on": (date.today() - timedelta(days=1)).isoformat(),
                "expires_on": (date.today() + timedelta(days=7)).isoformat(),
                "artifacts": [
                    {
                        "filename": item["filename"].replace(f"semgrep-{UPSTREAM}-", f"semgrep-{DOWNSTREAM}-", 1),
                        "candidate_sha256": candidate.sha256 if item["platform_tag"] == PLATFORMS[0] else "c" * 64,
                        "upstream_sha256": item["upstream_sha256"],
                        "platform_tag": item["platform_tag"],
                    }
                    for item in recipe["wheels"]
                ],
            }
        ],
    }
    return candidate, bundle, policy


def test_exact_protected_boundary_admits_only_the_verified_wheel(wheel_recipe: WheelRecipe, tmp_path: Path) -> None:
    module = _module()
    candidate, bundle, policy = _protected_fixture(module, wheel_recipe, tmp_path)
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance", return_value=None) as verifier,
    ):
        admitted = module.admit_artifact(candidate.path, bundle)
    assert admitted.wheel == candidate.path
    verifier.assert_called_once_with(candidate.path, bundle / "provenance.jsonl", "d" * 40, "e" * 40)
    policy["admissions"][0]["source_commit"] = "f" * 40
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance", side_effect=AssertionError("Wrong source reached verifier")),
        pytest.raises(ValueError, match="Approved source differs"),
    ):
        module.admit_artifact(candidate.path, bundle)


@pytest.mark.parametrize("damage", ["empty-policy", "expired", "wrong-hash", "wrong-matrix"], ids=str)
def test_unapproved_artifact_rejects_before_verifier(wheel_recipe: WheelRecipe, tmp_path: Path, damage: str) -> None:
    module = _module()
    candidate, bundle, policy = _protected_fixture(module, wheel_recipe, tmp_path)
    if damage == "empty-policy":
        policy["admissions"] = []
    elif damage == "expired":
        policy["admissions"][0]["expires_on"] = (date.today() - timedelta(days=1)).isoformat()
    elif damage == "wrong-hash":
        policy["admissions"][0]["artifacts"][0]["candidate_sha256"] = "f" * 64
    else:
        policy["admissions"][0]["matrix_sha256"] = "f" * 64
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(
            module, "_verify_provenance", side_effect=AssertionError("Unapproved artifacts must not reach verifier")
        ),
        pytest.raises(ValueError),
    ):
        module.admit_artifact(candidate.path, bundle)


@pytest.mark.parametrize("failure", ["pr-origin", "missing-verifier", "timeout"], ids=str)
def test_verifier_failure_cannot_turn_claims_into_admission(
    wheel_recipe: WheelRecipe, tmp_path: Path, failure: str
) -> None:
    module = _module()
    candidate, bundle, policy = _protected_fixture(module, wheel_recipe, tmp_path)
    _write_json(
        bundle / "provenance.jsonl", {"event_name": "pull_request", "ref": "refs/pull/772/merge", "verified": True}
    )
    result = subprocess.CompletedProcess(["gh"], 1, '{"verified":true}', "source ref is not protected dev")
    error = {
        "pr-origin": None,
        "missing-verifier": FileNotFoundError("gh"),
        "timeout": subprocess.TimeoutExpired("gh", 30),
    }[failure]
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module.subprocess, "run", return_value=result, side_effect=error) as run,
        pytest.raises(ValueError),
    ):
        module.admit_artifact(candidate.path, bundle)
    assert run.call_args_list
    for call in run.call_args_list:
        argv = call.args[0]
        assert "attestation" in argv and "verify" in argv
        assert "refs/heads/dev" in argv
        assert "d" * 40 in argv and "e" * 40 in argv
        assert "--deny-self-hosted-runners" in argv


def _bound_audit(
    module: DownstreamModule, wheel_recipe: WheelRecipe, tmp_path: Path
) -> tuple[AdmittedWheel, Path, CandidateWheel]:
    candidate, bundle, policy = _protected_fixture(module, wheel_recipe, tmp_path)
    actual = tmp_path / "actual.txt"
    actual.write_text(
        f"semgrep=={DOWNSTREAM} --hash=sha256:{candidate.sha256}\n"
        f"mcp==1.30.0 --hash=sha256:{'1' * 64}\n"
        f"click==8.3.0 --hash=sha256:{'2' * 64}\n",
        encoding="utf-8",
    )
    with (
        patch.object(module, "_fetch_protected_policy", return_value=policy),
        patch.object(module, "_verify_provenance", return_value=None),
    ):
        admitted = module.admit_artifact(candidate.path, bundle)
    return admitted, actual, candidate


def _audit_result() -> AuditResult:
    return {
        "dependencies": [
            {"name": "semgrep", "version": UPSTREAM, "vulns": []},
            {"name": "mcp", "version": "1.30.0", "vulns": []},
            {"name": "click", "version": "8.3.0", "vulns": []},
        ]
    }


def _assert_audit_view(
    actual: Path, output: Path, original: bytes, candidate_sha256: str, upstream_sha256: str
) -> None:
    rendered = output.read_text()
    assert actual.read_bytes() == original
    assert f"semgrep=={UPSTREAM}" in rendered
    assert DOWNSTREAM not in rendered
    assert candidate_sha256 not in rendered
    assert upstream_sha256 in rendered
    for line in actual.read_text().splitlines()[1:]:
        assert line in rendered


def _assert_audit_status_output(bound: BoundAuditInput, production_admission: str) -> None:
    report = bound.assert_complete_result(
        subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(_audit_result()), "No known vulnerabilities found\n")
    )
    assert report["actual_inventory"] == bound.actual_inventory
    assert report["production_admission"] == production_admission
    with pytest.raises(ValueError):
        bound.assert_complete_result(
            subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(_audit_result()), "HTTP503 advisory backend\n")
        )


def test_bound_audit_preserves_real_graph_and_reports_local_identity(wheel_recipe: WheelRecipe, tmp_path: Path) -> None:
    module = _module()
    admitted, actual, candidate = _bound_audit(module, wheel_recipe, tmp_path)
    output = tmp_path / "audit.txt"
    original = actual.read_bytes()
    bound = admitted.audit_input(actual, output)
    assert bound.requirements == output
    _assert_audit_view(actual, output, original, candidate.sha256, wheel_recipe[1]["wheels"][0]["upstream_sha256"])
    assert bound.actual_inventory == {"semgrep": DOWNSTREAM, "mcp": "1.30.0", "click": "8.3.0"}
    report = bound.assert_complete_result(
        subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(_audit_result()), "")
    )
    assert report["actual_inventory"] == bound.actual_inventory

    candidate_identity = module.verify_candidate(wheel_recipe[0], wheel_recipe[2], candidate.path)
    assert callable(getattr(candidate_identity, "candidate_audit_input", None)), "Candidate audit proof is absent"
    candidate_bound = candidate_identity.candidate_audit_input(actual, tmp_path / "candidate-audit.txt")
    candidate_report = candidate_bound.assert_complete_result(
        subprocess.CompletedProcess(["pip-audit"], 0, json.dumps(_audit_result()), "")
    )
    assert candidate_report["actual_inventory"] == bound.actual_inventory
    assert candidate_report["production_admission"] == "not_requested"
    _assert_audit_status_output(bound, "admitted")
    _assert_audit_status_output(candidate_bound, "not_requested")


def _damaged_audit_response(damage: str) -> tuple[AuditResult, int, str]:
    result = _audit_result()
    deps = result["dependencies"]
    returncode, stderr = 0, ""
    if damage == "empty-skip":
        deps[-1]["skip_reason"] = ""
    if damage == "missing":
        deps.pop()
    if damage == "duplicate":
        deps.append(copy.deepcopy(deps[0]))
    if damage == "wrong-version":
        deps[1]["version"] = "1.29.0"
    if damage == "malformed-vuln":
        deps[0]["vulns"] = [None]
    if damage == "advisory-and-error":
        deps[1]["vulns"] = [{"id": "CVE-2026-59951"}]
        returncode, stderr = 2, "HTTP 503 fetching another dependency"
    return result, returncode, stderr


@pytest.mark.parametrize(
    "damage", ["empty-skip", "missing", "duplicate", "wrong-version", "malformed-vuln", "advisory-and-error"], ids=str
)
def test_bound_audit_rejects_incomplete_or_unsafe_responses(
    wheel_recipe: WheelRecipe, tmp_path: Path, damage: str
) -> None:
    module = _module()
    admitted, actual, _candidate = _bound_audit(module, wheel_recipe, tmp_path)
    bound = admitted.audit_input(actual, tmp_path / "audit.txt")
    result, returncode, stderr = _damaged_audit_response(damage)
    with pytest.raises(ValueError):
        bound.assert_complete_result(subprocess.CompletedProcess(["pip-audit"], returncode, json.dumps(result), stderr))

    if damage == "malformed-vuln":
        for constant in ("NaN", "Infinity", "-Infinity"):
            invalid_json = json.dumps(_audit_result())[:-1] + ', "unknown":' + constant + "}"
            with pytest.raises(ValueError):
                bound.assert_complete_result(subprocess.CompletedProcess(["pip-audit"], 0, invalid_json, ""))


@pytest.mark.parametrize("damage", ["vulnerable-mcp", "wrong-local-hash", "marker"], ids=str)
def test_bound_audit_rejects_unbound_inventory_before_writing_view(
    wheel_recipe: WheelRecipe, tmp_path: Path, damage: str
) -> None:
    module = _module()
    admitted, actual, candidate = _bound_audit(module, wheel_recipe, tmp_path)
    contents = actual.read_text()
    if damage == "vulnerable-mcp":
        contents = contents.replace("mcp==1.30.0", "mcp==1.29.0")
    elif damage == "wrong-local-hash":
        contents = contents.replace(candidate.sha256, "f" * 64)
    else:
        contents = contents.replace("click==8.3.0", 'click==8.3.0 ; python_version < "3.12"')
    actual.write_text(contents)
    output = tmp_path / "rejected-audit.txt"
    with pytest.raises(ValueError):
        admitted.audit_input(actual, output)
    assert not output.exists()
