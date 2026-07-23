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
    assert pycparser["version"] == "3.0"
    assert pycparser["source_url"].startswith("https://files.pythonhosted.org/")
    assert pycparser["expires_on"] >= "2026-07-24"
    assert "cryptography" in pycparser["transitive_path"]


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
                        "version": "3.0",
                        "source_url": "https://files.pythonhosted.org/example.whl",
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

    assert errors == ["pycparser==3.0 expired on 2026-07-23"]
