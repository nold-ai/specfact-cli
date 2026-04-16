"""
Run pip-audit with JSON output and enforce CVSS-based severity thresholds.

Exits with code 1 only when the maximum CVSS score across all reported
vulnerabilities is at least 7.0. Findings below that threshold print as WARNING
and do not fail the gate.

pip-audit's JSON formatter does not always include CVSS vectors; this script
recursively scans each vulnerability object for numeric severity fields and
defaults missing scores to 0.0 (informational / manual review).

``--skip-editable`` skips the editable project when using ``pip install -e .``,
so the local package is not confused with a PyPI release during auditing.

``pip-audit`` ``--strict`` (``-S``) is not used: with ``--skip-editable`` it
still errors on the root editable and emits no JSON. The gate remains
fail-closed on empty or invalid JSON and on CVSS at or above 7.0 in the parsed
dependency list.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from typing import Any

from beartype import beartype
from icontract import ensure


HIGH_SEVERITY_THRESHOLD = 7.0

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


def _run_pip_audit() -> subprocess.CompletedProcess[str] | None:
    cmd = [sys.executable, "-m", "pip_audit", "-f", "json", "--skip-editable"]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        _emit(
            "ERROR: pip-audit timed out after 900s — cannot audit (fail closed)",
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
    deps = data.get("dependencies")
    if not isinstance(deps, list):
        _emit("ERROR: pip-audit JSON missing 'dependencies' list", error=True)
        return None, 1
    return deps, 0


def _format_vuln_line(dep_name: str, dep_version: str, vuln: dict[str, Any], cvss: float) -> str:
    vid = str(vuln.get("id", "?"))
    aliases = vuln.get("aliases") or []
    desc = (vuln.get("description") or "").replace("\n", " ")[:240]
    prefix = "FAIL" if cvss >= HIGH_SEVERITY_THRESHOLD else "WARNING"
    alias_txt = f" aliases={aliases!r}" if aliases else ""
    return f"{prefix}: {dep_name}=={dep_version} vuln={vid} CVSS={cvss:.1f}{alias_txt} {desc}".rstrip()


def _scan_and_print_vulnerabilities(deps: list[Any]) -> tuple[float, bool]:
    max_cvss = 0.0
    any_vuln = False
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
            any_vuln = True
            cvss = _cvss_for_vuln(vuln)
            max_cvss = max(max_cvss, cvss)
            _emit(_format_vuln_line(str(name), str(version), vuln, cvss))
    return max_cvss, any_vuln


def _finalize_audit_exit(max_cvss: float, any_vuln: bool) -> int:
    if not any_vuln:
        _emit("Security audit passed. No high-severity vulnerabilities found.")
        return 0
    if max_cvss >= HIGH_SEVERITY_THRESHOLD:
        _emit(
            f"\nACTION REQUIRED: max CVSS {max_cvss:.1f} >= {HIGH_SEVERITY_THRESHOLD} — "
            "update or replace affected packages",
        )
        return 1
    _emit(
        f"\nSecurity audit passed. No high-severity vulnerabilities found "
        f"(max CVSS {max_cvss:.1f} < {HIGH_SEVERITY_THRESHOLD}; review WARNING lines above).",
    )
    return 0


@beartype
@ensure(lambda result: result in (0, 1))
def main() -> int:
    proc = _run_pip_audit()
    if proc is None:
        return 1
    deps, err = _parse_dependencies_list(proc)
    if err or deps is None:
        return 1
    max_cvss, any_vuln = _scan_and_print_vulnerabilities(deps)
    return _finalize_audit_exit(max_cvss, any_vuln)


if __name__ == "__main__":
    raise SystemExit(main())
