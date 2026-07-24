"""Policy tests for reviewed exceptions to flagged dependency heuristics."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TRUST_RECORD = REPO_ROOT / "ci" / "dependency-trust-exceptions.json"
CHECKER = REPO_ROOT / "scripts" / "check_dependency_trust_exceptions.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_dependency_trust_exceptions", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    errors = checker.validate_exception_register(record_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==3.0 is blocked after a security-obfuscation alert"]


def test_unofficial_executable_wheel_is_not_accepted() -> None:
    """The exception register must not normalize acceptance of executable wheel runtimes."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    assert all(record["package"] != "nodejs-wheel-binaries" for record in payload["exceptions"])


def test_expired_exception_fails_closed(tmp_path: Path) -> None:
    """Expiry is enforced by CI rather than merely documented in static policy."""
    record_path = tmp_path / "exceptions.json"
    record_path.write_text(
        json.dumps(
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
            }
        ),
        encoding="utf-8",
    )
    checker = _load_checker()

    errors = checker.validate_exception_register(record_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==2.22 expired on 2026-07-23"]


def test_reviewed_artifact_must_exist_in_the_frozen_lock(tmp_path: Path) -> None:
    """A copied review record cannot approve a different frozen artifact."""
    payload = json.loads(TRUST_RECORD.read_text(encoding="utf-8"))
    payload["exceptions"][0]["artifact_sha256"] = "0" * 64
    register_path = tmp_path / "exceptions.json"
    register_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = _load_checker()

    errors = checker.validate_frozen_dependency_policy(register_path, today=date(2026, 7, 24))

    assert errors == ["pycparser==2.22 artifact digest is absent from frozen lock"]
