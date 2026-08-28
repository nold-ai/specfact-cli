"""Policy tests for reviewed exceptions to flagged dependency heuristics."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
TRUST_RECORD = REPO_ROOT / "ci" / "dependency-trust-exceptions.json"
CHECKER = REPO_ROOT / "scripts" / "check_dependency_trust_exceptions.py"


def _review_record(*, package: str, version: str, reviewed_on: str, expires_on: str) -> dict[str, str]:
    """Build one syntactically complete exception record for policy tests."""
    return {
        "package": package,
        "version": version,
        "source_url": "https://files.pythonhosted.org/example.whl",
        "artifact_sha256": "c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc",
        "classification": "source-provenance-reviewed",
        "reviewed_on": reviewed_on,
        "expires_on": expires_on,
        "transitive_path": "specfact-cli -> test fixture",
        "rationale": "test fixture",
    }


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_dependency_trust_exceptions", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_code_review_graph(tmp_path: Path, requirement: str, *, bound_input: str | None = None) -> tuple[Path, Path]:
    """Write one hash-locked isolated review graph with an explicit input binding."""
    input_path = tmp_path / "requirements.in"
    input_path.write_text(bound_input or f"{requirement}\n", encoding="utf-8")
    input_digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    lock_path = tmp_path / "locked.txt"
    lock_path.write_text(
        "\n".join(
            [
                f"# input-sha256: {input_digest}",
                f"{requirement} \\",
                f"    --hash=sha256:{'a' * 64}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return input_path, lock_path


def test_checker_runs_before_site_packages_are_available() -> None:
    """The CI bootstrap check must not import dependencies installed by uv sync."""
    result = subprocess.run(
        [sys.executable, "-S", str(CHECKER)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Dependency trust register is valid" in result.stdout


def test_pycparser_has_current_exact_version_review_record() -> None:
    """The required C parser remains only with scoped, expiring review evidence."""
    assert TRUST_RECORD.is_file(), "Flagged frozen dependencies require a checked-in review record"
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    records = payload["exceptions"]
    pycparser = next(record for record in records if record["package"] == "pycparser")
    assert pycparser["version"] == "2.22"
    assert pycparser["source_url"].startswith("https://files.pythonhosted.org/")
    assert pycparser["artifact_sha256"] == "c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc"
    assert pycparser["classification"] == "source-provenance-reviewed"
    assert pycparser["expires_on"] >= "2026-07-24"
    assert "cryptography" in pycparser["transitive_path"]


def test_alerted_pycparser_release_is_blocked_even_with_a_review_record(tmp_path: Path) -> None:
    """A Socket-alerted release cannot be normalized through an exception record."""
    record_path = tmp_path / "exceptions.json"
    record_path.write_text(
        json.dumps(
            {
                "exceptions": [
                    {
                        "package": "pycparser",
                        "version": "3.0",
                        "source_url": "https://files.pythonhosted.org/example.whl",
                        "artifact_sha256": "c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc",
                        "classification": "source-provenance-reviewed",
                        "reviewed_on": "2026-07-23",
                        "expires_on": "2026-10-22",
                        "transitive_path": "specfact-cli -> cryptography -> cffi -> pycparser",
                        "rationale": "test fixture",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker._validate_exception_register(record_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==3.0 is blocked after a security-obfuscation alert"]


def test_alerted_pycparser_release_family_is_blocked_with_a_pep440_spelling(tmp_path: Path) -> None:
    """Post and local spellings must not reintroduce the blocked 3.0 release family."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    payload["exceptions"][0]["version"] = "3.0.post1"
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker._validate_exception_register(register_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==3.0.post1 is blocked after a security-obfuscation alert"]


@pytest.mark.parametrize(
    "version",
    ["3.0-1", "3.0.post1", "3.0+local", "v3.0", "03.0", "0!3.0"],
)
def test_alerted_pycparser_release_family_normalizes_equivalent_pep440_spellings(version: str) -> None:
    """Equivalent versions must not bypass the blocked 3.0 release-family policy."""
    checker = _load_checker()

    assert checker._is_blocked_release("pycparser", version)


def test_unofficial_executable_wheel_is_not_accepted() -> None:
    """The exception register must not normalize acceptance of executable wheel runtimes."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    assert all(record["package"] != "nodejs-wheel-binaries" for record in payload["exceptions"])


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            _review_record(
                package="pycparser",
                version="2.22",
                reviewed_on="2026-07-24",
                expires_on="2026-07-23",
            ),
            "pycparser==2.22 expired on 2026-07-23",
        ),
        (
            _review_record(
                package="NodeJS_Wheel.Binaries",
                version="1.0.0",
                reviewed_on="2026-07-23",
                expires_on="2026-10-22",
            ),
            "nodejs-wheel-binaries==1.0.0 is prohibited from the dependency trust register",
        ),
    ],
    ids=["expired", "normalized-prohibited-executable-wheel"],
)
def test_invalid_exception_register_fails_closed(tmp_path: Path, record: dict[str, str], expected: str) -> None:
    """Invalid records fail closed for both temporal and normalized-name policy."""
    record_path = tmp_path / "exceptions.json"
    record_path.write_text(json.dumps({"exceptions": [record]}), encoding="utf-8")
    checker = _load_checker()

    errors = checker._validate_exception_register(record_path, today=date(2026, 7, 24))

    assert errors == [expected]


def test_reviewed_artifact_must_exist_in_the_frozen_lock(tmp_path: Path) -> None:
    """A copied review record cannot approve a different frozen artifact."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    payload["exceptions"][0]["artifact_sha256"] = "0" * 64
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(register_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==2.22 artifact digest is absent from its frozen lock record"]


def test_review_evidence_must_bind_to_the_matching_lock_package(tmp_path: Path) -> None:
    """Evidence copied to another lock record cannot approve pycparser."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    reviewed = payload["exceptions"][0]
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        "\n".join(
            [
                "[[package]]",
                'name = "pycparser"',
                'version = "2.22"',
                'sdist = { url = "https://files.pythonhosted.org/other.tar.gz", hash = "sha256:' + "0" * 64 + '" }',
                "",
                "[[package]]",
                'name = "unrelated-package"',
                'version = "1.0.0"',
                'sdist = { url = "'
                + reviewed["source_url"]
                + '", hash = "sha256:'
                + reviewed["artifact_sha256"]
                + '" }',
                "",
            ]
        ),
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(register_path, lock_path, today=date(2026, 7, 24))

    assert errors == [
        "pycparser==2.22 source artifact is absent from its frozen lock record",
        "pycparser==2.22 artifact digest is absent from its frozen lock record",
    ]


def test_prohibited_executable_wheel_in_lock_fails_without_an_exception(tmp_path: Path) -> None:
    """The lock itself is the enforcement boundary for executable wheel runtimes."""
    register_path = tmp_path / "exceptions.json"
    register_path.write_text('{"exceptions": []}', encoding="utf-8")
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        '\n[[package]]\nname = "NodeJS_Wheel.Binaries"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(register_path, lock_path, today=date(2026, 7, 24))

    assert errors == ["nodejs-wheel-binaries==1.0.0 is prohibited in the frozen lock"]


@pytest.mark.parametrize(
    ("requirement", "expected"),
    [
        ("pycparser==3.0", "pycparser==3.0 is blocked after a security-obfuscation alert"),
        ("NodeJS_Wheel.Binaries==1.0.0", "nodejs-wheel-binaries==1.0.0 is prohibited in the frozen lock"),
        ("mcp==1.23.3", "mcp==1.23.3 is below the reviewed security floor 1.28.1"),
    ],
    ids=("blocked-release", "prohibited-wheel", "below-security-floor"),
)
def test_code_review_only_lock_must_follow_dependency_trust_policy(
    tmp_path: Path, requirement: str, expected: str
) -> None:
    """The isolated review graph cannot bypass policy enforced on the primary lock."""
    input_path, lock_path = _write_code_review_graph(tmp_path, requirement)
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert expected in errors


def test_code_review_lock_must_bind_to_its_exact_input(tmp_path: Path) -> None:
    """The local trust gate rejects a stale isolated review lock before installation."""
    input_path, lock_path = _write_code_review_graph(tmp_path, "pylint==4.0.7", bound_input="pylint==4.0.6\n")
    input_path.write_text("pylint==4.0.7\n", encoding="utf-8")
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert "Code Review lock input SHA-256 binding does not match requirements.in" in errors


@pytest.mark.parametrize("hash_line", [None, "--hash=sha256:not-a-digest"], ids=("missing", "malformed"))
def test_code_review_lock_requires_valid_hash_for_every_pin(tmp_path: Path, hash_line: str | None) -> None:
    """Every isolated exact pin must bind at least one valid distribution digest."""
    input_path, lock_path = _write_code_review_graph(tmp_path, "pylint==4.0.7")
    input_digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    lines = [f"# input-sha256: {input_digest}", "pylint==4.0.7 \\"]
    if hash_line is not None:
        lines.append(f"    {hash_line}")
    lock_path.write_text("\n".join([*lines, ""]), encoding="utf-8")
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert "Code Review lock package pylint==4.0.7 must include at least one valid SHA-256 hash" in errors


def test_code_review_lock_rejects_a_hash_detached_from_the_pin(tmp_path: Path) -> None:
    """A standalone digest must not be credited to an uncontinued package pin."""
    input_path, lock_path = _write_code_review_graph(tmp_path, "pylint==4.0.7")
    input_digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    lock_path.write_text(
        f"# input-sha256: {input_digest}\npylint==4.0.7\n    --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert "Code Review lock hash line 3 is not attached to a continued package pin" in errors
    assert "Code Review lock package pylint==4.0.7 must include at least one valid SHA-256 hash" in errors


@pytest.mark.parametrize(
    ("package", "locked_version", "floor"),
    [("semgrep", "1.174.0", "1.175.0"), ("mcp", "1.23.3", "1.28.1")],
)
def test_security_tool_lock_below_reviewed_floor_fails_before_install(
    tmp_path: Path, package: str, locked_version: str, floor: str
) -> None:
    """A lock downgrade cannot restore a reviewed vulnerable security-tool line."""
    register_path = tmp_path / "exceptions.json"
    register_path.write_text('{"exceptions": []}', encoding="utf-8")
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        f'\n[[package]]\nname = "{package}"\nversion = "{locked_version}"\n',
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker._validate_frozen_dependency_policy(register_path, lock_path, today=date(2026, 7, 24))

    assert errors == [f"{package}=={locked_version} is below the reviewed security floor {floor}"]
