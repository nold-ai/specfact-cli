from __future__ import annotations

import contextlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from scripts.runtime_discovery_smoke import _build_local_registry
from specfact_cli.validation.command_audit import (
    CommandAuditCase,
    build_command_audit_cases,
    official_marketplace_module_ids,
)


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
    ]
    with contextlib.suppress(IndexError):
        candidates.append(REPO_ROOT.parents[2] / "specfact-cli-modules")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


MODULES_REPO = _resolve_modules_repo()
FORBIDDEN_OUTPUT = (
    "Module compatibility check:",
    "Partially compliant modules:",
    "Legacy modules:",
    "takes precedence over user-scoped module",
    "attempted to extend command 'backlog' with duplicate subcommand",
)


def _required_bundle_names() -> list[str]:
    return [module_id.split("/", 1)[1] for module_id in official_marketplace_module_ids()]


def _require_complete_packages_checkout(packages_root: Path) -> None:
    if not packages_root.exists():
        pytest.skip("specfact-cli-modules packages checkout not available")
    missing = [name for name in _required_bundle_names() if not (packages_root / name).is_dir()]
    if missing:
        missing_csv = ", ".join(sorted(missing))
        pytest.skip(f"specfact-cli-modules partial checkout: missing bundles: {missing_csv}")


def _subprocess_env(home_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(SRC_ROOT), str(REPO_ROOT)]
    packages_root = MODULES_REPO / "packages"
    _require_complete_packages_checkout(packages_root)
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
    smoke_repo = os.environ.get("SPECFACT_SMOKE_MODULES_REPO")
    archive_repository = Path(smoke_repo).expanduser() if smoke_repo else MODULES_REPO
    env["SPECFACT_REGISTRY_INDEX_URL"] = _build_local_registry(home_dir, archive_repository).resolve().as_uri()
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


def _load_cli_app_for_home(home_dir: Path) -> typer.Typer:
    user_modules_root = home_dir / ".specfact" / "modules"
    marketplace_modules_root = home_dir / ".specfact" / "marketplace-modules"
    custom_modules_root = home_dir / ".specfact" / "custom-modules"
    download_cache_root = home_dir / ".specfact" / "downloads" / "cache"
    config_path = home_dir / ".specfact" / "config.yaml"

    import specfact_cli.cli as cli_module
    import specfact_cli.registry.bootstrap as bootstrap_module
    import specfact_cli.registry.module_discovery as module_discovery
    import specfact_cli.registry.module_installer as module_installer
    from specfact_cli.registry.registry import CommandRegistry

    module_discovery.USER_MODULES_ROOT = user_modules_root
    module_discovery.MARKETPLACE_MODULES_ROOT = marketplace_modules_root
    module_discovery.CUSTOM_MODULES_ROOT = custom_modules_root

    module_installer.USER_MODULES_ROOT = user_modules_root
    module_installer.MARKETPLACE_MODULES_ROOT = marketplace_modules_root
    module_installer.MODULE_DOWNLOAD_CACHE_ROOT = download_cache_root

    bootstrap_module._SPECFACT_CONFIG_PATH = config_path

    CommandRegistry._clear_for_testing()
    cli_module.app.registered_groups = []
    cli_module.app.registered_commands = []
    bootstrap_module.register_builtin_commands()
    for name, meta in cli_module._grouped_command_order(CommandRegistry.list_commands_for_help()):
        cli_module.app.add_typer(cli_module._make_lazy_typer(name, meta.help), name=name, help=meta.help)
    return cli_module.app


def _restore_specfact_module_root_paths_after_temp_home() -> None:
    """Undo globals mutated by `_load_cli_app_for_home` so other tests see the real user home."""
    home = Path.home()
    import specfact_cli.registry.bootstrap as bootstrap_module
    import specfact_cli.registry.module_discovery as module_discovery
    import specfact_cli.registry.module_installer as module_installer

    module_discovery.USER_MODULES_ROOT = home / ".specfact" / "modules"
    module_discovery.MARKETPLACE_MODULES_ROOT = home / ".specfact" / "marketplace-modules"
    module_discovery.CUSTOM_MODULES_ROOT = home / ".specfact" / "custom-modules"
    module_installer.USER_MODULES_ROOT = module_discovery.USER_MODULES_ROOT
    module_installer.MARKETPLACE_MODULES_ROOT = module_discovery.MARKETPLACE_MODULES_ROOT
    module_installer.MODULE_DOWNLOAD_CACHE_ROOT = home / ".specfact" / "downloads" / "cache"
    bootstrap_module._SPECFACT_CONFIG_PATH = home / ".specfact" / "config.yaml"


def _run_help_case(
    app: typer.Typer,
    case: CommandAuditCase,
    home_dir: Path,
    env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, str]:
    runner = CliRunner()
    packages_root = MODULES_REPO / "packages"

    with monkeypatch.context() as context:
        context.chdir(home_dir)
        for key in (
            "HOME",
            "SPECFACT_REPO_ROOT",
            "SPECFACT_MODULES_REPO",
            "SPECFACT_REGISTRY_INDEX_URL",
            "SPECFACT_ALLOW_UNSIGNED",
            "SPECFACT_REGISTRY_DIR",
        ):
            context.setenv(key, env[key])
        context.setenv("TEST_MODE", "true")
        context.setattr(sys, "path", list(sys.path), raising=False)
        for bundle_src in sorted(packages_root.glob("*/src"), reverse=True):
            sys.path.insert(0, str(bundle_src))
        sys.path.insert(0, str(SRC_ROOT))
        sys.path.insert(0, str(REPO_ROOT))
        result = runner.invoke(app, list(case.argv), catch_exceptions=False)
    return result.exit_code, result.output


def _audit_commands(
    help_app: typer.Typer, home_dir: Path, env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    failures: list[str] = []
    for case in build_command_audit_cases():
        if case.mode == "help-only":
            return_code, merged_output = _run_help_case(help_app, case, home_dir, env, monkeypatch)
        else:
            result = _run_cli(env, *case.argv, cwd=home_dir)
            return_code = result.returncode
            merged_output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        if return_code != 0:
            failures.append(f"{case.command_path}: rc={return_code}\nOUTPUT:\n{merged_output}")
            continue
        leaked = [marker for marker in FORBIDDEN_OUTPUT if marker in merged_output]
        if leaked:
            failures.append(f"{case.command_path}: leaked diagnostics {leaked}\nOUTPUT:\n{merged_output}")
    return failures


@pytest.mark.timeout(300)
def test_command_audit_help_cases_execute_cleanly_in_temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    env = _subprocess_env(home_dir)
    install = _run_cli(
        env,
        "module",
        "install",
        *official_marketplace_module_ids(),
        "--source",
        "marketplace",
        "--skip-deps",
        cwd=home_dir,
    )
    assert install.returncode == 0, install.stdout + install.stderr

    try:
        with monkeypatch.context() as context:
            context.setenv("HOME", str(home_dir))
            context.setenv("SPECFACT_MODULES_REPO", str(MODULES_REPO.resolve()))
            help_app = _load_cli_app_for_home(home_dir)

            failures = _audit_commands(help_app, home_dir, env, monkeypatch)
    finally:
        _restore_specfact_module_root_paths_after_temp_home()

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
        "--skip-deps",
        cwd=home_dir,
    )
    assert install_result.returncode == 0, install_result.stdout + install_result.stderr

    result = _run_cli(env, "backlog", "map-fields", "--help", cwd=home_dir)
    merged_output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()

    assert result.returncode == 0, merged_output
    assert "attempted to extend command 'backlog' with duplicate subcommand" not in merged_output
