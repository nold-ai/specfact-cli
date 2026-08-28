"""Fail closed when a reviewed dependency-trust exception is malformed or expired.

This script executes before ``uv sync`` in CI, so it must remain standard-library
only.  Do not add runtime contract or validation-library imports here.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tomllib
from datetime import date
from pathlib import Path
from typing import cast


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTER = REPO_ROOT / "ci" / "dependency-trust-exceptions.json"
DEFAULT_UV_LOCK = REPO_ROOT / "uv.lock"
DEFAULT_SECURITY_TOOL_FLOORS = REPO_ROOT / "ci" / "security-tool-minimum-versions.json"
DEFAULT_CODE_REVIEW_INPUT = REPO_ROOT / "requirements" / "code-review" / "requirements.in"
DEFAULT_CODE_REVIEW_LOCK = REPO_ROOT / "requirements" / "code-review" / "locked.txt"
CODE_REVIEW_INPUT_BINDING_PREFIX = "# input-sha256:"
REQUIRED_FIELDS = frozenset(
    {
        "package",
        "version",
        "source_url",
        "artifact_sha256",
        "classification",
        "reviewed_on",
        "expires_on",
        "transitive_path",
        "rationale",
    }
)
PROHIBITED_EXECUTABLE_WHEEL_PACKAGES = frozenset({"nodejs-wheel-binaries"})
# These releases produced high-confidence Socket obfuscation alerts.  They are
# blocked outright: a review record must never turn a known alert into normal
# delivery input.
BLOCKED_DEPENDENCY_RELEASES = frozenset({("pycparser", "3.0")})
PACKAGE_NAME_SEPARATOR = re.compile(r"[-_.]+")
CODE_REVIEW_PIN_PATTERN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)(?:\s*\\)?$")
CODE_REVIEW_HASH_PATTERN = re.compile(r"^--hash=sha256:[0-9a-fA-F]{64}(?:\s*\\)?$")


def _canonical_package_name(value: str) -> str:
    """Return the PEP 503 normalized identity used by lock and policy checks."""
    return PACKAGE_NAME_SEPARATOR.sub("-", value).casefold()


def _pep440_release_components(value: str) -> tuple[int, ...] | None:
    """Return the normalized zero-epoch numeric release prefix without dependencies."""
    public_version = value.casefold().split("+", maxsplit=1)[0]
    match = re.match(r"^v?(?:(\d+)!)?(\d+(?:\.\d+)*)", public_version)
    return (
        tuple(int(component) for component in match.group(2).split("."))
        if match is not None and int(match.group(1) or "0") == 0
        else None
    )


def _is_blocked_release(package_name: str, version: str) -> bool:
    """Return whether a version belongs to a blocked PEP 440 release family."""
    release = _pep440_release_components(version)
    if release is None:
        return False
    for blocked_package, blocked_version in BLOCKED_DEPENDENCY_RELEASES:
        if package_name != blocked_package:
            continue
        blocked_release = _pep440_release_components(blocked_version)
        if blocked_release is not None and release[: len(blocked_release)] == blocked_release:
            return True
    return False


def _version_components(value: str) -> tuple[int, ...] | None:
    """Parse the stable numeric version form used by the reviewed tool floor policy."""
    return tuple(int(component) for component in value.split(".")) if re.fullmatch(r"\d+(?:\.\d+)*", value) else None


def _is_below_security_floor(version: str, floor: str) -> bool | None:
    """Compare stable tool versions without importing dependencies before synchronization."""
    parsed_version = _version_components(version)
    parsed_floor = _version_components(floor)
    if parsed_version is None or parsed_floor is None:
        return None
    length = max(len(parsed_version), len(parsed_floor))
    return parsed_version + (0,) * (length - len(parsed_version)) < parsed_floor + (0,) * (length - len(parsed_floor))


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
    return _canonical_package_name(package.strip()), version.strip()


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


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
    if _is_blocked_release(package_name, version):
        return [f"{package_ref} is blocked after a security-obfuscation alert"]
    source_url = cast(str, record_map["source_url"])
    if not source_url.startswith("https://files.pythonhosted.org/"):
        return [f"{package_ref} must use an immutable files.pythonhosted.org source URL"]
    if not _is_sha256(record_map["artifact_sha256"]):
        return [f"{package_ref} must include a lowercase SHA-256 artifact digest"]
    if record_map["classification"] != "source-provenance-reviewed":
        return [f"{package_ref} must use source-provenance-reviewed classification"]
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


def _validate_exception_register(register_path: Path, *, today: date | None = None) -> list[str]:
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


def _read_locked_packages(lock_path: Path) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Read normalized lock records from uv's committed lock without resolving."""
    try:
        raw_payload = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, [f"could not read frozen lock: {exc}"]
    payload = cast(dict[str, object], raw_payload)
    packages = payload.get("package")
    if not isinstance(packages, list):
        return {}, ["frozen lock must contain a package list"]
    locked_packages: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for index, package in enumerate(cast(list[object], packages)):
        if not isinstance(package, dict):
            errors.append(f"frozen lock package[{index}] must be an object")
            continue
        package_map = cast(dict[str, object], package)
        name = package_map.get("name")
        version = package_map.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            errors.append(f"frozen lock package[{index}] must include name and version")
            continue
        package_name = _canonical_package_name(name)
        if package_name in locked_packages:
            errors.append(f"frozen lock contains duplicate normalized package identity: {package_name}")
            continue
        locked_packages[package_name] = package_map
    return locked_packages, errors


def _validate_code_review_input_binding(input_bytes: bytes, contents: str) -> list[str]:
    """Verify one exact digest binding from the review lock to its input."""
    binding_lines = [line for line in contents.splitlines() if line.startswith(CODE_REVIEW_INPUT_BINDING_PREFIX)]
    if len(binding_lines) != 1:
        return ["Code Review lock must contain exactly one input SHA-256 binding"]
    bound_digest = binding_lines[0].removeprefix(CODE_REVIEW_INPUT_BINDING_PREFIX).strip()
    if not _is_sha256(bound_digest):
        return ["Code Review lock input SHA-256 binding is malformed"]
    if bound_digest != hashlib.sha256(input_bytes).hexdigest():
        return ["Code Review lock input SHA-256 binding does not match requirements.in"]
    return []


def _parse_code_review_pins(contents: str) -> tuple[dict[str, str], list[str]]:
    """Parse the fail-closed exact-pin subset emitted by the frozen compiler."""
    errors: list[str] = []
    packages: dict[str, str] = {}
    hashed_packages: set[str] = set()
    current_package: str | None = None
    for line_number, line in enumerate(contents.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("--hash=sha256:"):
            if current_package is not None and CODE_REVIEW_HASH_PATTERN.fullmatch(stripped) is not None:
                hashed_packages.add(current_package)
            continue
        match = CODE_REVIEW_PIN_PATTERN.fullmatch(stripped)
        if match is None:
            errors.append(f"Code Review lock line {line_number} must be an exact name==version pin")
            current_package = None
            continue
        package_name = _canonical_package_name(match.group(1))
        version = match.group(2)
        if package_name in packages:
            errors.append(f"Code Review lock contains duplicate normalized package identity: {package_name}")
            current_package = None
            continue
        packages[package_name] = version
        current_package = package_name
    if not packages:
        errors.append("Code Review lock must contain at least one exact package pin")
    for package_name, version in packages.items():
        if package_name not in hashed_packages:
            errors.append(
                f"Code Review lock package {package_name}=={version} must include at least one valid SHA-256 hash"
            )
    return packages, errors


def _read_code_review_locked_packages(input_path: Path, lock_path: Path) -> tuple[dict[str, str], list[str]]:
    """Read exact pins and verify the isolated review lock's input binding."""
    try:
        input_bytes = input_path.read_bytes()
        contents = lock_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {}, [f"could not read Code Review dependency graph: {exc}"]
    packages, errors = _parse_code_review_pins(contents)
    return packages, [*_validate_code_review_input_binding(input_bytes, contents), *errors]


def _read_security_tool_floors(policy_path: Path = DEFAULT_SECURITY_TOOL_FLOORS) -> tuple[dict[str, str], list[str]]:
    """Load normalized, locally verifiable security-tool minimum versions."""
    try:
        raw_payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"could not read security tool floor policy: {exc}"]
    if not isinstance(raw_payload, dict):
        return {}, ["security tool floor policy must contain a minimum_versions object"]
    payload = cast(dict[str, object], raw_payload)
    minimum_versions = payload.get("minimum_versions")
    if not isinstance(minimum_versions, dict):
        return {}, ["security tool floor policy must contain a minimum_versions object"]
    floors: dict[str, str] = {}
    errors: list[str] = []
    for package_name, version in cast(dict[str, object], minimum_versions).items():
        if not isinstance(version, str) or _version_components(version) is None:
            errors.append("security tool floor policy entries must use package names and stable numeric versions")
            continue
        floors[_canonical_package_name(package_name)] = version
    return floors, errors


def _artifact_values(package: dict[str, object]) -> tuple[set[str], set[str]]:
    """Return URLs and hashes declared by one exact frozen package record."""
    urls: set[str] = set()
    hashes: set[str] = set()
    artifacts: list[object] = [package.get("sdist")]
    wheels = package.get("wheels")
    if isinstance(wheels, list):
        artifacts.extend(cast(list[object], wheels))
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_map = cast(dict[str, object], artifact)
        url = artifact_map.get("url")
        digest = artifact_map.get("hash")
        if isinstance(url, str):
            urls.add(url)
        if isinstance(digest, str):
            hashes.add(digest)
    return urls, hashes


def _validate_locked_version_policy(locked_versions: dict[str, str], tool_floors: dict[str, str]) -> list[str]:
    """Return policy violations intrinsic to exact frozen package versions."""
    errors: list[str] = []
    for package_name, version in sorted(locked_versions.items()):
        if package_name in PROHIBITED_EXECUTABLE_WHEEL_PACKAGES:
            errors.append(f"{package_name}=={version} is prohibited in the frozen lock")
        if _is_blocked_release(package_name, version):
            errors.append(f"{package_name}=={version} is blocked after a security-obfuscation alert")
        floor = tool_floors.get(package_name)
        if floor is None:
            continue
        below_floor = _is_below_security_floor(version, floor)
        if below_floor is None:
            errors.append(f"{package_name}=={version} cannot be compared with reviewed security floor {floor}")
        elif below_floor:
            errors.append(f"{package_name}=={version} is below the reviewed security floor {floor}")
    return errors


def _validate_locked_package_policy(
    locked_packages: dict[str, dict[str, object]], tool_floors: dict[str, str]
) -> list[str]:
    """Return policy violations intrinsic to exact uv frozen package records."""
    locked_versions = {
        package_name: version
        for package_name, package in locked_packages.items()
        if isinstance((version := package.get("version")), str)
    }
    return _validate_locked_version_policy(locked_versions, tool_floors)


def _validate_review_record(
    record: dict[str, object], index: int, locked_packages: dict[str, dict[str, object]]
) -> list[str]:
    """Ensure one exception record points to one exact frozen package artifact."""
    identity = _record_identity(record, index=index)
    if isinstance(identity, str):
        return []
    package_name, version = identity
    locked_package = locked_packages.get(package_name)
    if locked_package is None:
        return [f"{package_name}=={version} does not match frozen lock (absent)"]
    locked_version = locked_package.get("version")
    if locked_version != version:
        return [f"{package_name}=={version} does not match frozen lock ({locked_version or 'absent'})"]
    errors: list[str] = []
    source_url = record.get("source_url")
    artifact_sha256 = record.get("artifact_sha256")
    urls, hashes = _artifact_values(locked_package)
    if isinstance(source_url, str) and source_url not in urls:
        errors.append(f"{package_name}=={version} source artifact is absent from its frozen lock record")
    if isinstance(artifact_sha256, str) and f"sha256:{artifact_sha256}" not in hashes:
        errors.append(f"{package_name}=={version} artifact digest is absent from its frozen lock record")
    return errors


def _validate_review_records(register_path: Path, locked_packages: dict[str, dict[str, object]]) -> list[str]:
    """Validate every review record against the exact frozen lock artifacts."""
    records, register_errors = _read_exception_records(register_path)
    if register_errors:
        return register_errors
    errors: list[str] = []
    for index, record in enumerate(records):
        if isinstance(record, dict):
            errors.extend(_validate_review_record(cast(dict[str, object], record), index, locked_packages))
    return errors


def _validate_frozen_dependency_policy(
    register_path: Path = DEFAULT_REGISTER,
    lock_path: Path = DEFAULT_UV_LOCK,
    *,
    today: date | None = None,
    code_review_input_path: Path = DEFAULT_CODE_REVIEW_INPUT,
    code_review_lock_path: Path = DEFAULT_CODE_REVIEW_LOCK,
) -> list[str]:
    """Reject blocked releases and reviews that do not bind to either frozen graph."""
    errors = _validate_exception_register(register_path, today=today)
    locked_packages, lock_errors = _read_locked_packages(lock_path)
    errors.extend(lock_errors)
    if lock_errors:
        return errors
    tool_floors, floor_errors = _read_security_tool_floors()
    errors.extend(floor_errors)
    if floor_errors:
        return errors
    errors.extend(_validate_locked_package_policy(locked_packages, tool_floors))
    errors.extend(_validate_review_records(register_path, locked_packages))
    code_review_packages, code_review_errors = _read_code_review_locked_packages(
        code_review_input_path, code_review_lock_path
    )
    errors.extend(code_review_errors)
    errors.extend(_validate_locked_version_policy(code_review_packages, tool_floors))
    return errors


def _main() -> int:
    """Print register validation errors and return a CI-friendly exit status."""
    errors = _validate_frozen_dependency_policy()
    if errors:
        for error in errors:
            sys.stderr.write(f"DEPENDENCY TRUST VIOLATION: {error}\n")
        return 1
    sys.stdout.write(f"Dependency trust register is valid: {DEFAULT_REGISTER}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
