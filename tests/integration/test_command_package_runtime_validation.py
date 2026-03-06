from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from specfact_cli.validation.command_audit import build_command_audit_cases, official_marketplace_module_ids


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
MODULES_REPO = REPO_ROOT.parent / "specfact-cli-modules"
REGISTRY_INDEX = MODULES_REPO / "registry" / "index.json"
BUILTIN_BACKLOG_CORE = REPO_ROOT / "modules" / "backlog-core"
FORBIDDEN_OUTPUT = (
    "Module compatibility check:",
    "Partially compliant modules:",
    "Legacy modules:",
    "takes precedence over user-scoped module",
    "attempted to extend command 'backlog' with duplicate subcommand",
)


def _subprocess_env(home_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(SRC_ROOT), str(REPO_ROOT)]
    existing = env.get("PYTHONPATH", "")
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["HOME"] = str(home_dir)
    env["SPECFACT_REPO_ROOT"] = str(REPO_ROOT)
    env["SPECFACT_REGISTRY_INDEX_URL"] = str(REGISTRY_INDEX)
    env["SPECFACT_ALLOW_UNSIGNED"] = "1"
    env["SPECFACT_REGISTRY_DIR"] = str(home_dir / ".specfact-test-registry")
    return env


def _run_cli(env: dict[str, str], *argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "specfact_cli", *argv],
        cwd=cwd or REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_command_audit_help_cases_execute_cleanly_in_temp_home(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    env = _subprocess_env(home_dir)

    install_failures: list[str] = []
    for module_id in official_marketplace_module_ids():
        result = _run_cli(env, "module", "install", module_id, "--source", "marketplace")
        if result.returncode != 0:
            install_failures.append(
                f"{module_id}: rc={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
    assert not install_failures, "\n\n".join(install_failures)

    failures: list[str] = []
    for case in build_command_audit_cases():
        result = _run_cli(env, *case.argv, cwd=home_dir)
        merged_output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        if result.returncode != 0:
            failures.append(
                f"{case.command_path}: rc={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
            continue
        leaked = [marker for marker in FORBIDDEN_OUTPUT if marker in merged_output]
        if leaked:
            failures.append(f"{case.command_path}: leaked diagnostics {leaked}\nOUTPUT:\n{merged_output}")

    assert not failures, "\n\n".join(failures)


def test_backlog_core_and_marketplace_overlap_is_silent_in_normal_output(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    env = _subprocess_env(home_dir)

    target_root = home_dir / ".specfact" / "modules"
    target_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BUILTIN_BACKLOG_CORE, target_root / "backlog-core")

    install_result = _run_cli(
        env,
        "module",
        "install",
        "nold-ai/specfact-backlog",
        "--source",
        "marketplace",
        cwd=home_dir,
    )
    assert install_result.returncode == 0, install_result.stdout + install_result.stderr

    result = _run_cli(env, "backlog", "map-fields", "--help", cwd=home_dir)
    merged_output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()

    assert result.returncode == 0, merged_output
    assert "attempted to extend command 'backlog' with duplicate subcommand" not in merged_output
