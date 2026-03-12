from __future__ import annotations

from specfact_cli.validation.command_audit import build_command_audit_cases


def test_command_audit_cases_cover_core_and_bundle_surfaces() -> None:
    cases = build_command_audit_cases()
    paths = {case.command_path for case in cases}

    expected_paths = {
        "specfact",
        "init",
        "init ide",
        "module init",
        "module install",
        "module uninstall",
        "module enable",
        "module disable",
        "module search",
        "module list",
        "module show",
        "module upgrade",
        "module alias",
        "module alias create",
        "module alias list",
        "module alias remove",
        "upgrade",
        "project",
        "project health-check",
        "project init-personas",
        "project link-backlog",
        "project snapshot",
        "project version",
        "project version check",
        "project sync bridge",
        "spec",
        "spec validate",
        "spec backward-compat",
        "spec generate-tests",
        "spec mock",
        "code",
        "code import",
        "code analyze contracts",
        "code drift detect",
        "code validate sidecar init",
        "code validate sidecar run",
        "code repro",
        "code repro setup",
        "backlog",
        "backlog ceremony standup",
        "backlog auth status",
        "backlog daily",
        "backlog refine",
        "backlog init-config",
        "backlog map-fields",
        "govern",
        "govern enforce",
        "govern enforce stage",
        "govern enforce sdd",
        "govern patch apply",
    }

    missing = sorted(expected_paths - paths)
    assert not missing, f"Missing command audit cases: {missing}"
    assert all(case.phase for case in cases)
    assert all(case.owner for case in cases)
    assert {case.mode for case in cases}.issubset({"help-only", "fixture-backed", "dry-run"})
