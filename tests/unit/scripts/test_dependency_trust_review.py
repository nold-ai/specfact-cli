"""Policy tests for reviewed exceptions to flagged dependency heuristics."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
TRUST_RECORD = REPO_ROOT / "ci" / "dependency-trust-exceptions.json"
CHECKER = REPO_ROOT / "scripts" / "check_dependency_trust_exceptions.py"


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_dependency_trust_exceptions", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert pycparser["version"] == "3.12"
    assert pycparser["source_url"] == (
        "https://files.pythonhosted.org/packages/b6/ae/315bbeee126a769cbde43cf4908acb4b40408d8bf8bbf334dd7368d8dadf/"
        "pycparser-3.12-py3-none-any.whl"
    )
    assert pycparser["artifact_sha256"] == "a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e"
    assert pycparser["classification"] == "source-provenance-reviewed"
    assert pycparser["reviewed_on"] == "2026-10-22"
    assert pycparser["expires_on"] == "2026-11-04"
    assert pycparser["transitive_path"] == "specfact-cli -> cryptography -> cffi -> pycparser"


@pytest.mark.parametrize(
    "payload, today, expected_errors",
    [
        pytest.param(
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
            },
            date(2026, 7, 24),
            ["pycparser==3.0 is blocked after a security-obfuscation alert"],
            id="blocked-pycparser-3.0",
        ),
        pytest.param(
            {
                "exceptions": [
                    {
                        "package": "pycparser",
                        "version": "2.22",
                        "source_url": "https://files.pythonhosted.org/example.whl",
                        "artifact_sha256": "c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc",
                        "classification": "source-provenance-reviewed",
                        "reviewed_on": "2026-07-24",
                        "expires_on": "2026-07-23",
                        "transitive_path": "specfact-cli -> cryptography -> cffi -> pycparser",
                        "rationale": "test fixture",
                    }
                ]
            },
            date(2026, 7, 24),
            ["pycparser==2.22 expired on 2026-07-23"],
            id="expired-review-record",
        ),
        pytest.param(
            {
                "exceptions": [
                    {
                        "package": "NodeJS_Wheel.Binaries",
                        "version": "1.0.0",
                        "source_url": "https://files.pythonhosted.org/example.whl",
                        "artifact_sha256": "c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc",
                        "classification": "source-provenance-reviewed",
                        "reviewed_on": "2026-07-23",
                        "expires_on": "2026-10-22",
                        "transitive_path": "specfact-cli -> test fixture",
                        "rationale": "test fixture",
                    }
                ]
            },
            date(2026, 7, 24),
            ["nodejs-wheel-binaries==1.0.0 is prohibited from the dependency trust register"],
            id="prohibited-pep503-name",
        ),
    ],
)
def test_invalid_trust_register_is_rejected(
    tmp_path: Path, payload: dict[str, list[dict[str, str]]], today: date, expected_errors: list[str]
) -> None:
    record_path = tmp_path / "exceptions.json"
    record_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker.validate_exception_register(record_path, today=today)

    assert errors == expected_errors


def test_alerted_pycparser_release_family_is_blocked_with_a_pep440_spelling(tmp_path: Path) -> None:
    """Post and local spellings must not reintroduce the blocked 3.0 release family."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    payload["exceptions"][0]["version"] = "3.0.post1"
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker.validate_exception_register(register_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==3.0.post1 is blocked after a security-obfuscation alert"]


def test_alerted_pycparser_release_family_normalizes_equivalent_pep440_spellings() -> None:
    """Equivalent versions must not bypass the blocked 3.0 release-family policy."""
    checker = _load_checker()

    assert checker._is_blocked_release("pycparser", "3.0-1")
    assert checker._is_blocked_release("pycparser", "3.0.post1")
    assert checker._is_blocked_release("pycparser", "3.0+local")


def test_unofficial_executable_wheel_is_not_accepted() -> None:
    """The exception register must not normalize acceptance of executable wheel runtimes."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    assert all(record["package"] != "nodejs-wheel-binaries" for record in payload["exceptions"])


def test_reviewed_artifact_must_exist_in_the_frozen_lock(tmp_path: Path) -> None:
    """A copied review record cannot approve a different frozen artifact."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    reviewed = payload["exceptions"][0]
    reviewed["artifact_sha256"] = "0" * 64
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker.validate_frozen_dependency_policy(register_path, today=date.fromisoformat(reviewed["reviewed_on"]))

    assert errors == [f"pycparser=={reviewed['version']} artifact digest is absent from its frozen lock record"]


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
                f'version = "{reviewed["version"]}"',
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

    errors = checker.validate_frozen_dependency_policy(
        register_path, lock_path, today=date.fromisoformat(reviewed["reviewed_on"])
    )

    assert errors == [
        f"pycparser=={reviewed['version']} source artifact is absent from its frozen lock record",
        f"pycparser=={reviewed['version']} artifact digest is absent from its frozen lock record",
    ]


@pytest.mark.parametrize(
    "lock_text, today, expected_errors",
    [
        pytest.param(
            '\n[[package]]\nname = "NodeJS_Wheel.Binaries"\nversion = "1.0.0"\n',
            date(2026, 7, 24),
            ["nodejs-wheel-binaries==1.0.0 is prohibited in the frozen lock"],
            id="prohibited-executable-wheel",
        ),
        pytest.param(
            '\n[[package]]\nname = "semgrep"\nversion = "1.70.1"\n',
            date(2026, 7, 24),
            ["semgrep==1.70.1 is below the reviewed security floor 1.175.0"],
            id="semgrep-below-security-floor",
        ),
    ],
)
def test_invalid_frozen_lock_is_rejected(
    tmp_path: Path, lock_text: str, today: date, expected_errors: list[str]
) -> None:
    register_path = tmp_path / "exceptions.json"
    register_path.write_text('{"exceptions": []}', encoding="utf-8")
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(lock_text, encoding="utf-8")
    checker = _load_checker()

    errors = checker.validate_frozen_dependency_policy(register_path, lock_path, today=today)

    assert errors == expected_errors
