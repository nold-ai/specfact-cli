from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from specfact_cli.validation.command_audit import build_command_audit_cases, official_marketplace_module_ids


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _resolve_modules_repo() -> Path:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    if configured:
        return Path(configured).expanduser()

    root_parts = REPO_ROOT.resolve().parts
    if "specfact-cli-worktrees" in root_parts:
        idx = root_parts.index("specfact-cli-worktrees")
        worktree_root = Path(*root_parts[:idx], "specfact-cli-modules-worktrees")
        relative_tail = REPO_ROOT.resolve().relative_to(Path(*root_parts[: idx + 1]))
        candidate = worktree_root / relative_tail.parts[0] / relative_tail.parts[1]
        if candidate.exists():
            return candidate

    candidates = [
        REPO_ROOT / "specfact-cli-modules",
        REPO_ROOT.parent / "specfact-cli-modules",
        REPO_ROOT.parents[2] / "specfact-cli-modules",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


MODULES_REPO = _resolve_modules_repo()
REGISTRY_INDEX = MODULES_REPO / "registry" / "index.json"
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
    packages_root = MODULES_REPO / "packages"
    if packages_root.exists():
        for bundle_src in sorted(packages_root.glob("*/src")):
            pythonpath_parts.append(str(bundle_src))
    for entry in sys.path:
        if not entry:
            continue
        if "site-packages" in entry or "dist-packages" in entry:
            pythonpath_parts.append(entry)
    existing = env.get("PYTHONPATH", "")
    if existing:
        pythonpath_parts.append(existing)
    deduped_parts: list[str] = []
    seen: set[str] = set()
    for part in pythonpath_parts:
        if part in seen:
            continue
        seen.add(part)
        deduped_parts.append(part)
    env["PYTHONPATH"] = os.pathsep.join(deduped_parts)
    env["HOME"] = str(home_dir)
    env["SPECFACT_REPO_ROOT"] = str(REPO_ROOT)
    env["SPECFACT_MODULES_REPO"] = str(MODULES_REPO.resolve())
    env["SPECFACT_REGISTRY_INDEX_URL"] = REGISTRY_INDEX.resolve().as_uri()
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


@pytest.mark.timeout(300)
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


def test_marketplace_backlog_bundle_registers_cleanly_without_core_overlap(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    env = _subprocess_env(home_dir)

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
