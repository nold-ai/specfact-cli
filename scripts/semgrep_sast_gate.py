#!/usr/bin/env python3
"""Fail CI when Semgrep OSS SAST reports findings outside the accepted baseline."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure


FindingKey = tuple[str, str, int]


def _finding_key(result: dict[str, Any]) -> FindingKey:
    check_id = result.get("check_id")
    path = result.get("path")
    start = result.get("start")
    if not isinstance(check_id, str) or not check_id.strip():
        raise ValueError("Semgrep result missing non-empty check_id")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Semgrep result missing non-empty path")
    if not isinstance(start, dict):
        raise ValueError("Semgrep result missing integer start.line")
    start_line = cast(Mapping[str, object], start).get("line")
    if not isinstance(start_line, int):
        raise ValueError("Semgrep result missing integer start.line")
    return (check_id, path, start_line)


def _emit_stdout(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"::error::Could not read JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"::error::{path} must contain a JSON object")
    return payload


def _load_baseline(path: Path) -> set[FindingKey]:
    payload = _load_json(path)
    raw_findings = payload.get("accepted_findings")
    if not isinstance(raw_findings, list):
        raise SystemExit(f"::error::{path} missing accepted_findings list")

    baseline: set[FindingKey] = set()
    for index, raw in enumerate(raw_findings):
        if (
            not isinstance(raw, list)
            or len(raw) != 3
            or not isinstance(raw[0], str)
            or not isinstance(raw[1], str)
            or not isinstance(raw[2], int)
        ):
            raise SystemExit(f"::error::{path} accepted_findings[{index}] must be [check_id, path, start_line]")
        baseline.add((raw[0], raw[1], raw[2]))
    return baseline


def _load_results(path: Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise SystemExit(f"::error::{path} missing Semgrep results list")
    results: list[dict[str, Any]] = []
    for index, result in enumerate(raw_results):
        if not isinstance(result, dict):
            raise SystemExit(f"::error::{path} results[{index}] must be an object")
        try:
            _finding_key(result)
        except ValueError as exc:
            raise SystemExit(f"::error::{path} results[{index}] is malformed: {exc}") from exc
        results.append(result)
    return results


@beartype
@ensure(lambda result: result in {0, 1}, "exit code must be 0 or 1")
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True, help="Semgrep JSON results file")
    parser.add_argument("--baseline", type=Path, required=True, help="Accepted Semgrep findings baseline")
    args = parser.parse_args()

    baseline = _load_baseline(args.baseline)
    results = _load_results(args.results)
    current = {_finding_key(result) for result in results}
    new_findings = sorted(current - baseline)
    resolved_findings = sorted(baseline - current)

    _emit_stdout(f"Semgrep SAST findings: {len(current)} current, {len(baseline)} accepted baseline")
    if resolved_findings:
        _emit_stdout(f"Semgrep SAST baseline can shrink by {len(resolved_findings)} finding(s)")
    if not new_findings:
        _emit_stdout("Semgrep SAST gate passed: no new findings outside baseline")
        return 0

    for check_id, path, line in new_findings:
        _emit_stdout(f"::error file={path},line={line}::New Semgrep SAST finding: {check_id}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
