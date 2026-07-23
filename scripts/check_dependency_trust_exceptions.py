"""Fail closed when a reviewed dependency-trust exception is malformed or expired."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import cast


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTER = REPO_ROOT / "ci" / "dependency-trust-exceptions.json"
REQUIRED_FIELDS = frozenset(
    {
        "package",
        "version",
        "source_url",
        "reviewed_on",
        "expires_on",
        "transitive_path",
        "rationale",
    }
)
PROHIBITED_EXECUTABLE_WHEEL_PACKAGES = frozenset({"nodejs-wheel-binaries"})


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _read_exception_records(register_path: Path) -> tuple[list[object], list[str]]:
    """Load the register while preserving fail-closed parse errors."""
    try:
        raw_payload = json.loads(register_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"could not read dependency trust register: {exc}"]
    if not isinstance(raw_payload, dict):
        return [], ["dependency trust register must contain an exceptions list"]
    payload = cast(dict[str, object], raw_payload)
    raw_records = payload.get("exceptions")
    if not isinstance(raw_records, list):
        return [], ["dependency trust register must contain an exceptions list"]
    return cast(list[object], raw_records), []


def _record_identity(record: dict[str, object], *, index: int) -> tuple[str, str] | str:
    package = record.get("package")
    version = record.get("version")
    if not isinstance(package, str) or not package.strip() or not isinstance(version, str) or not version.strip():
        return f"exceptions[{index}] must include non-empty package and version"
    return package.strip(), version.strip()


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _missing_fields(record: dict[str, object]) -> list[str]:
    return sorted(field for field in REQUIRED_FIELDS if not _is_nonempty_string(record.get(field)))


def _validate_record(record: object, *, index: int, current_date: date) -> list[str]:
    """Validate one reviewed exception record without allowing partial acceptance."""
    if not isinstance(record, dict):
        return [f"exceptions[{index}] must be an object"]
    record_map = cast(dict[str, object], record)
    identity = _record_identity(record_map, index=index)
    if isinstance(identity, str):
        return [identity]
    package_name, version = identity
    package_ref = f"{package_name}=={version}"
    missing = _missing_fields(record_map)
    if missing:
        return [f"{package_ref} missing required fields: {', '.join(missing)}"]
    if package_name in PROHIBITED_EXECUTABLE_WHEEL_PACKAGES:
        return [f"{package_ref} is prohibited from the dependency trust register"]
    source_url = cast(str, record_map["source_url"])
    if not source_url.startswith("https://files.pythonhosted.org/"):
        return [f"{package_ref} must use an immutable files.pythonhosted.org source URL"]
    reviewed_on = _parse_date(record_map["reviewed_on"])
    expires_on = _parse_date(record_map["expires_on"])
    if reviewed_on is None or expires_on is None:
        return [f"{package_ref} must use ISO-8601 reviewed_on and expires_on dates"]
    return _validate_dates(package_ref, reviewed_on=reviewed_on, expires_on=expires_on, current_date=current_date)


def _validate_dates(package_ref: str, *, reviewed_on: date, expires_on: date, current_date: date) -> list[str]:
    errors: list[str] = []
    if reviewed_on > current_date:
        errors.append(f"{package_ref} review date {reviewed_on.isoformat()} is in the future")
    if expires_on < current_date:
        errors.append(f"{package_ref} expired on {expires_on.isoformat()}")
    return errors


def validate_exception_register(register_path: Path, *, today: date | None = None) -> list[str]:
    """Return deterministic policy errors for a dependency-trust exception register."""
    records, errors = _read_exception_records(register_path)
    if errors:
        return errors

    current_date = today or date.today()
    return [
        error
        for index, record in enumerate(records)
        for error in _validate_record(record, index=index, current_date=current_date)
    ]


def main() -> int:
    """Print register validation errors and return a CI-friendly exit status."""
    errors = validate_exception_register(DEFAULT_REGISTER)
    if errors:
        for error in errors:
            sys.stderr.write(f"DEPENDENCY TRUST VIOLATION: {error}\n")
        return 1
    sys.stdout.write(f"Dependency trust register is valid: {DEFAULT_REGISTER}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
