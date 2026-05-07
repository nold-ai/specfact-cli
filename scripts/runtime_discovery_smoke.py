#!/usr/bin/env python3
"""Fail-fast real-world smoke checks for runtime discovery and init behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_IDS = ("nold-ai/specfact-project", "nold-ai/specfact-codebase", "nold-ai/specfact-code-review")
NO_ENV_WARNING = "No Compatible Environment Manager Detected"
LOGGER = logging.getLogger("runtime-discovery-smoke")


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    LOGGER.info("+ %s", " ".join(command))
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.stdout:
        LOGGER.info("%s", result.stdout.rstrip())
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return result


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_rootless_monorepo_demo(workspace: Path, template: Path | None) -> Path:
    demo = workspace / "specfact-cli-demo-rootless-monorepo"
    if template is not None:
        shutil.copytree(template, demo)
    else:
        demo.mkdir(parents=True)
        _write(demo / "README.md", "# SpecFact runtime discovery smoke demo\n")

    _write(
        demo / "backend" / "pyproject.toml",
        """[project]
name = "demo-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv]
package = false
""",
    )
    _write(
        demo / "backend" / "uv.lock",
        """version = 1
revision = 3
requires-python = ">=3.12"
""",
    )
    _write(
        demo / "worker" / "pyproject.toml",
        """[project]
name = "demo-worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.hatch.envs.default]
dependencies = []
""",
    )
    _write(demo / "tools" / "data-job" / "requirements.txt", "click\n")
    (demo / "backend" / ".venv").mkdir(parents=True, exist_ok=True)
    (demo / "worker" / ".venv").mkdir(parents=True, exist_ok=True)
    return demo


def _resolve_modules_repo(configured: str | None) -> Path:
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    env_repo = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    if env_repo:
        candidates.append(Path(env_repo).expanduser())
    candidates.extend(
        [
            REPO_ROOT.parent / "specfact-cli-modules",
            REPO_ROOT.parents[2] / "specfact-cli-modules",
            Path.cwd().parent / "specfact-cli-modules",
        ]
    )
    for candidate in candidates:
        packages = candidate / "packages"
        if all((packages / module_id.split("/", 1)[1] / "module-package.yaml").exists() for module_id in MODULE_IDS):
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates)
    raise RuntimeError(f"Could not find specfact-cli-modules with required packages. Searched: {searched}")


def _module_payload_for_checksum(package_dir: Path) -> bytes:
    from specfact_cli.registry.module_installer import _module_artifact_payload_signed

    return _module_artifact_payload_signed(package_dir)


def _build_local_registry(workspace: Path, modules_repo: Path) -> Path:
    registry = workspace / "local-registry"
    modules_dir = registry / "modules"
    staging_dir = registry / "staging"
    modules_dir.mkdir(parents=True)
    staging_dir.mkdir(parents=True)
    entries: list[dict[str, Any]] = []

    for module_id in MODULE_IDS:
        bundle_name = module_id.split("/", 1)[1]
        source_dir = modules_repo / "packages" / bundle_name
        staged_dir = staging_dir / bundle_name
        shutil.copytree(source_dir, staged_dir)

        manifest_path = staged_dir / "module-package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise RuntimeError(f"Invalid module manifest: {manifest_path}")
        manifest_data = cast(dict[str, Any], manifest)
        manifest_data["integrity"] = {
            "checksum": f"sha256:{hashlib.sha256(_module_payload_for_checksum(staged_dir)).hexdigest()}"
        }
        manifest_path.write_text(yaml.safe_dump(manifest_data, sort_keys=False, allow_unicode=False), encoding="utf-8")

        archive_path = modules_dir / f"{bundle_name}-{manifest_data['version']}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(staged_dir, arcname=bundle_name)
        entries.append(
            {
                "id": module_id,
                "latest_version": str(manifest_data["version"]),
                "download_url": archive_path.resolve().as_uri(),
                "checksum_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                "tier": manifest_data.get("tier", "official"),
                "publisher": manifest_data.get("publisher", {}),
                "bundle_dependencies": manifest_data.get("bundle_dependencies", []),
                "description": manifest_data.get("description", ""),
            }
        )

    index_path = registry / "index.json"
    index_path.write_text(json.dumps({"modules": entries}, indent=2), encoding="utf-8")
    return index_path


def _create_pip_editable_launcher(workspace: Path) -> list[str]:
    venv_dir = workspace / "pip-editable-venv"
    try:
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(venv_dir)
    except subprocess.CalledProcessError:
        virtualenv = shutil.which("virtualenv")
        if virtualenv is None:
            raise
        _run([virtualenv, "--system-site-packages", str(venv_dir)], cwd=REPO_ROOT, env=os.environ.copy(), timeout=120)
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    _run(
        [str(python), "-m", "pip", "install", "-e", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        timeout=180,
    )
    specfact = venv_dir / ("Scripts/specfact.exe" if os.name == "nt" else "bin/specfact")
    return [str(specfact)]


def _launcher_command(name: str, workspace: Path) -> list[str]:
    if name == "direct":
        return [sys.executable, "-m", "specfact_cli.cli"]
    if name == "pip-editable":
        return _create_pip_editable_launcher(workspace)
    if name == "console":
        return ["specfact"]
    if name == "uvx":
        return ["uvx", "--from", str(REPO_ROOT), "specfact"]
    raise ValueError(f"Unsupported launcher: {name}")


def _assert_no_env_warning(result: subprocess.CompletedProcess[str]) -> None:
    if NO_ENV_WARNING in result.stdout:
        raise AssertionError(f"Unexpected environment-manager warning in output:\n{result.stdout}")


def _install_marketplace_modules(cli: list[str], demo: Path, env: dict[str, str]) -> None:
    for module_id in MODULE_IDS:
        _run(
            [
                *cli,
                "module",
                "install",
                module_id,
                "--source",
                "marketplace",
                "--scope",
                "user",
                "--reinstall",
            ],
            cwd=demo,
            env=env,
        )


def _smoke_launcher(name: str, workspace: Path, demo: Path, index_path: Path, modules_repo: Path) -> None:
    home = workspace / f"home-{name}"
    home.mkdir(parents=True)
    cli = _launcher_command(name, workspace / f"launcher-{name}")
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "SPECFACT_MODULES_REPO": str(modules_repo),
            "SPECFACT_REGISTRY_INDEX_URL": str(index_path),
            "SPECFACT_ALLOW_UNSIGNED": "1",
            "SPECFACT_NO_TIMING": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )

    _install_marketplace_modules(cli, demo, env)
    list_result = _run([*cli, "module", "list"], cwd=demo, env=env)
    for module_id in MODULE_IDS:
        if module_id not in list_result.stdout:
            raise AssertionError(f"{module_id} missing from module list output")

    _run([*cli, "upgrade", "--help"], cwd=demo, env=env)
    _run([*cli, "module", "upgrade", "--help"], cwd=demo, env=env)

    init_result = _run([*cli, "init", "ide", "--ide", "cursor", "--repo", str(demo), "--force"], cwd=demo, env=env)
    _assert_no_env_warning(init_result)
    explicit_result = _run(
        [*cli, "init", "ide", "--ide", "cursor", "--repo", str(demo), "--force", "--env-manager", "uv"],
        cwd=demo,
        env=env,
    )
    _assert_no_env_warning(explicit_result)

    help_result = _run([*cli, "code", "--help"], cwd=demo, env=env)
    for token in ("review", "import", "analyze", "drift", "validate", "repro"):
        if token not in help_result.stdout:
            raise AssertionError(f"`specfact code --help` did not include {token!r}")
    _run([*cli, "code", "review", "run", "--help"], cwd=demo, env=env)
    _run([*cli, "code", "import", "--help"], cwd=demo, env=env)
    LOGGER.info("runtime-discovery smoke passed for launcher=%s", name)


@beartype
@ensure(lambda result: result in (0, 1), "exit code must be 0 or 1")
def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules-repo", help="Path to sibling specfact-cli-modules checkout")
    parser.add_argument(
        "--demo-repo", type=Path, help="Optional demo repo checkout to copy before adding monorepo markers"
    )
    parser.add_argument(
        "--launcher",
        action="append",
        choices=("direct", "pip-editable", "console", "uvx"),
        help="Launcher to test. Repeatable. Defaults to direct.",
    )
    parser.add_argument("--keep-workspace", action="store_true", help="Keep the temporary workspace for debugging")
    args = parser.parse_args()

    modules_repo = _resolve_modules_repo(args.modules_repo)
    workspace_obj = tempfile.TemporaryDirectory(prefix="specfact-runtime-discovery-smoke-")
    workspace = Path(workspace_obj.name)
    try:
        demo = _create_rootless_monorepo_demo(workspace, args.demo_repo)
        index_path = _build_local_registry(workspace, modules_repo)
        for launcher in args.launcher or ["direct"]:
            _smoke_launcher(launcher, workspace, demo, index_path, modules_repo)
        if args.keep_workspace:
            LOGGER.info("Kept workspace: %s", workspace)
            workspace_obj = None  # type: ignore[assignment]
        return 0
    finally:
        if workspace_obj is not None:
            workspace_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
