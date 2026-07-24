"""
Audit the committed frozen dependency export with pip-audit JSON output.

Every advisory reported for the exact requirements file fails the gate. CVSS
metadata is included in the report when supplied by the advisory service, but
is not used to waive a known CVE: advisory records do not reliably carry a
score, and a low-scored finding can still be material in this project's use.

pip-audit's JSON formatter does not always include CVSS vectors; this script
recursively scans each vulnerability object for numeric severity fields and
defaults missing scores to 0.0 (informational / manual review).

The audit uses ``--requirement requirements/ci/locked.txt`` and ``--strict``;
it therefore verifies the committed, hash-pinned delivery graph before an
installer creates a project environment. It fails closed on unavailable
advisory data, invalid JSON, unresolved requirements, or any known advisory.

pip-audit JSON may be either a mapping with a ``dependencies`` list (current
default) or a top-level JSON array of dependency objects (documented in some
pip-audit versions). Both shapes are accepted.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure


DEFAULT_REQUIREMENTS_FILE = "requirements/ci/locked.txt"
DEFAULT_EXCEPTIONS_FILE = "ci/vulnerability-audit-exceptions.json"

_CVSS_KEY_HINTS = frozenset(
    {"cvss", "cvssv3", "cvssv2", "score", "basescore", "base_score"},
)


@beartype
def _emit(message: str, *, error: bool = False) -> None:
    """Write a single log line without using ``print`` in source."""
    stream = sys.stderr if error else sys.stdout
    stream.write(f"{message}\n")
    stream.flush()


def _scores_from_leaf_value(val: Any) -> list[float]:
    """Parse a scalar or string leaf that might hold a CVSS number."""
    if isinstance(val, (int, float)):
        return [float(val)]
    if isinstance(val, str):
        with contextlib.suppress(ValueError, IndexError):
            return [float(val.split()[0])]
    return []


def _gather_cvss_scores(payload: Any) -> list[float]:
    """Collect numeric CVSS-like scores from a nested JSON structure."""

    scores: list[float] = []

    def visit(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                if str(key).lower() in _CVSS_KEY_HINTS:
                    scores.extend(_scores_from_leaf_value(val))
                visit(val)
            return
        if isinstance(obj, list):
            for item in obj:
                visit(item)

    visit(payload)
    return scores


def _cvss_for_vuln(vuln: dict[str, Any]) -> float:
    scores = _gather_cvss_scores(vuln)
    return max(scores) if scores else 0.0


@beartype
def _dependencies_from_pip_audit_json(data: Any) -> list[Any] | None:
    """Return the dependency list from pip-audit JSON, or None if shape is unknown."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        deps = cast(dict[str, Any], data).get("dependencies")
        if isinstance(deps, list):
            return deps
    return None


def _run_pip_audit(requirements_file: str) -> subprocess.CompletedProcess[str] | None:
    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "--requirement",
        requirements_file,
        "--format",
        "json",
        "--strict",
        "--disable-pip",
    ]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        _emit(
            "ERROR: pip-audit timed out after 120s — cannot audit (fail closed)",
            error=True,
        )
        return None
    except OSError as exc:
        _emit(
            f"ERROR: pip-audit could not start ({exc}) — cannot audit (fail closed)",
            error=True,
        )
        return None


def _parse_dependencies_list(proc: subprocess.CompletedProcess[str]) -> tuple[list[Any] | None, int]:
    raw = (proc.stdout or "").strip()
    if not raw:
        _emit("ERROR: pip-audit produced no stdout — cannot audit (fail closed)", error=True)
        if proc.stderr:
            _emit(proc.stderr, error=True)
        return None, 1
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        _emit(f"ERROR: pip-audit JSON parse failed: {exc}", error=True)
        return None, 1
    deps = _dependencies_from_pip_audit_json(data)
    if deps is None:
        _emit(
            "ERROR: pip-audit JSON must be a list of dependencies or an object with a 'dependencies' list",
            error=True,
        )
        return None, 1
    return deps, 0


def _format_vuln_line(dep_name: str, dep_version: str, vuln: dict[str, Any], cvss: float) -> str:
    vid = str(vuln.get("id", "?"))
    aliases = vuln.get("aliases") or []
    desc = (vuln.get("description") or "").replace("\n", " ")[:240]
    alias_txt = f" aliases={aliases!r}" if aliases else ""
    return f"FAIL: {dep_name}=={dep_version} vuln={vid} CVSS={cvss:.1f}{alias_txt} {desc}".rstrip()


def _read_exception_items(path: Path) -> tuple[list[Any] | None, str | None]:
    """Read the exception list, returning one fail-closed error on invalid input."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"could not read vulnerability exception register: {exc}"
    if not isinstance(payload, dict):
        return None, "vulnerability exception register must contain an exceptions list"
    exception_items = cast(dict[str, Any], payload).get("exceptions")
    if not isinstance(exception_items, list):
        return None, "vulnerability exception register must contain an exceptions list"
    return exception_items, None


def _exception_fields(item: dict[str, Any]) -> tuple[str, str, list[str], str, str] | None:
    """Return the fields that make an exception exact and time-bounded."""
    package = item.get("package")
    version = item.get("version")
    vulnerability_ids = item.get("vulnerability_ids")
    reviewed_on = item.get("reviewed_on")
    expires_on = item.get("expires_on")
    rationale = item.get("rationale")
    mitigation = item.get("mitigation")
    valid = all(
        (
            isinstance(package, str) and bool(package),
            isinstance(version, str) and bool(version),
            isinstance(vulnerability_ids, list)
            and bool(vulnerability_ids)
            and all(isinstance(item_id, str) and item_id for item_id in vulnerability_ids),
            isinstance(reviewed_on, str),
            isinstance(expires_on, str),
            isinstance(rationale, str) and bool(rationale),
            isinstance(mitigation, str) and bool(mitigation),
        )
    )
    if not valid:
        return None
    return cast(tuple[str, str, list[str], str, str], (package, version, vulnerability_ids, reviewed_on, expires_on))


def _approved_exception_ids(item: Any, index: int) -> tuple[set[tuple[str, str, str]], str | None]:
    """Validate one register entry and return its exact approved advisory IDs."""
    if not isinstance(item, dict):
        return set(), f"exceptions[{index}] must be an object"
    fields = _exception_fields(item)
    if fields is None:
        return set(), f"exceptions[{index}] must contain exact package, version, IDs, dates, rationale, and mitigation"
    package, version, vulnerability_ids, reviewed_on, expires_on = fields
    try:
        reviewed_date = date.fromisoformat(reviewed_on)
        expiry_date = date.fromisoformat(expires_on)
    except ValueError:
        return set(), f"exceptions[{index}] must use ISO-8601 review and expiry dates"
    if reviewed_date > date.today() or expiry_date < date.today():
        return set(), f"exceptions[{index}] is not currently valid"
    return {(package.casefold(), version, item_id) for item_id in vulnerability_ids}, None


def _load_reviewed_exceptions(path: Path) -> tuple[set[tuple[str, str, str]], list[str]]:
    """Load exact, unexpired advisory exceptions or return fail-closed errors."""
    items, read_error = _read_exception_items(path)
    if read_error:
        return set(), [read_error]

    approved: set[tuple[str, str, str]] = set()
    errors: list[str] = []
    for index, item in enumerate(items or []):
        exception_ids, error = _approved_exception_ids(item, index)
        if error:
            errors.append(error)
        else:
            approved.update(exception_ids)
    return approved, errors


def _scan_and_print_vulnerabilities(deps: list[Any], approved: set[tuple[str, str, str]]) -> bool:
    any_unreviewed_vulnerability = False
    for dep in deps:
        if not isinstance(dep, dict) or "skip_reason" in dep:
            continue
        dep_map = dict[str, Any](dep)
        name = dep_map.get("name", "?")
        version = dep_map.get("version", "?")
        vulns = dep_map.get("vulns") or []
        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue
            vuln_map = cast(dict[str, Any], vuln)
            cvss = _cvss_for_vuln(vuln_map)
            vulnerability_id = str(vuln_map.get("id", "?"))
            if (str(name).casefold(), str(version), vulnerability_id) in approved:
                _emit(f"WAIVED: {_format_vuln_line(str(name), str(version), vuln_map, cvss)[6:]}")
                continue
            any_unreviewed_vulnerability = True
            _emit(_format_vuln_line(str(name), str(version), vuln_map, cvss))
    return any_unreviewed_vulnerability


def _finalize_audit_exit(any_vuln: bool) -> int:
    if not any_vuln:
        _emit("Security audit passed. No unreviewed vulnerabilities found in the frozen requirements.")
        return 0
    _emit(
        "\nACTION REQUIRED: known vulnerabilities were found in the frozen dependency graph — "
        "update, replace, or explicitly document an approved temporary exception.",
    )
    return 1


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requirement",
        default=DEFAULT_REQUIREMENTS_FILE,
        help="hash-pinned requirements export to audit (default: %(default)s)",
    )
    parser.add_argument(
        "--exceptions",
        default=DEFAULT_EXCEPTIONS_FILE,
        help="reviewed, expiring advisory exceptions (default: %(default)s)",
    )
    return parser.parse_args(argv or [])


@ensure(lambda result: result in (0, 1))
def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    approved, exception_errors = _load_reviewed_exceptions(Path(args.exceptions))
    if exception_errors:
        for error in exception_errors:
            _emit(f"ERROR: {error}", error=True)
        return 1
    proc = _run_pip_audit(args.requirement)
    if proc is None:
        return 1
    deps, err = _parse_dependencies_list(proc)
    if err or deps is None:
        return 1
    any_vuln = _scan_and_print_vulnerabilities(deps, approved)
    return _finalize_audit_exit(any_vuln)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
