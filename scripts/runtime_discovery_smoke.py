#!/usr/bin/env python3
"""Fail-fast real-world smoke checks for runtime discovery and init behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
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
MODULE_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
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


def _normalized_output(output: str) -> str:
    return " ".join(output.split())


_HATCH_SOURCE_RUNNER = (
    "import os; "
    "os.environ['PYTHONPATH'] = os.environ.get('SPECFACT_CHILD_PYTHONPATH', ''); "
    "from hatch.cli import main; "
    "raise SystemExit(main())"
)


def _hatch_launcher_python_and_site() -> tuple[str, str] | None:
    hatch_executable = shutil.which("hatch")
    if hatch_executable is None:
        return None
    try:
        first_line = Path(hatch_executable).read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError, UnicodeDecodeError):
        return None
    if not first_line.startswith("#!") or "python" not in first_line.lower():
        return None
    python_executable = first_line[2:].strip().split()[0]
    if not python_executable:
        return None
    result = subprocess.run(
        [
            python_executable,
            "-c",
            "import hatch, pathlib; print(pathlib.Path(hatch.__file__).resolve().parents[1])",
        ],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        return None
    site_path = result.stdout.strip()
    return (python_executable, site_path) if site_path else None


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
            Path.cwd().parent / "specfact-cli-modules",
        ]
    )
    parts = REPO_ROOT.parts
    if "specfact-cli-worktrees" in parts:
        marker_index = parts.index("specfact-cli-worktrees")
        candidates.append(
            Path(*parts[:marker_index]) / "specfact-cli-modules-worktrees" / Path(*parts[marker_index + 1 :])
        )
    if len(REPO_ROOT.parents) > 2:
        candidates.append(REPO_ROOT.parents[2] / "specfact-cli-modules")
    for candidate in candidates:
        packages = candidate / "packages"
        if all((packages / module_id.split("/", 1)[1] / "module-package.yaml").exists() for module_id in MODULE_IDS):
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates)
    raise RuntimeError(f"Could not find specfact-cli-modules with required packages. Searched: {searched}")


def _module_payload_for_checksum(package_dir: Path) -> bytes:
    from specfact_cli.registry.module_installer import _module_artifact_payload_signed

    return _module_artifact_payload_signed(package_dir)


def _module_dependency_closure(modules_repo: Path) -> tuple[str, ...]:
    """Return smoke roots and their manifest-declared bundle dependencies once each."""
    from specfact_cli.registry.module_installer import _extract_bundle_dependency_specs

    module_ids: list[str] = []
    pending: list[str] = list(MODULE_IDS)
    while pending:
        module_id = pending.pop(0)
        if module_id in module_ids:
            continue
        bundle_name = module_id.split("/", 1)[1]
        manifest_path = modules_repo / "packages" / bundle_name / "module-package.yaml"
        if not manifest_path.is_file():
            raise RuntimeError(f"Required module manifest not found: {manifest_path}")
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise RuntimeError(f"Invalid module manifest: {manifest_path}")
        manifest_data = cast(dict[str, Any], manifest)
        module_ids.append(module_id)
        pending.extend(dependency.module_id for dependency in _extract_bundle_dependency_specs(manifest_data))
    return tuple(module_ids)


def _build_local_registry(workspace: Path, modules_repo: Path) -> Path:
    registry = workspace / "local-registry"
    modules_dir = registry / "modules"
    staging_dir = registry / "staging"
    modules_dir.mkdir(parents=True)
    staging_dir.mkdir(parents=True)
    entries: list[dict[str, Any]] = []

    for module_id in _module_dependency_closure(modules_repo):
        bundle_name = module_id.split("/", 1)[1]
        source_dir = modules_repo / "packages" / bundle_name
        staged_dir = staging_dir / bundle_name
        shutil.copytree(source_dir, staged_dir)

        manifest_path = staged_dir / "module-package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise RuntimeError(f"Invalid module manifest: {manifest_path}")
        manifest_data = cast(dict[str, Any], manifest)
        version = manifest_data.get("version")
        if not isinstance(version, str) or MODULE_VERSION_PATTERN.fullmatch(version) is None:
            raise RuntimeError(f"Invalid module version in {manifest_path}: {version!r}")
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
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    except subprocess.CalledProcessError:
        virtualenv = shutil.which("virtualenv")
        if virtualenv is None:
            raise
        _run([virtualenv, str(venv_dir)], cwd=REPO_ROOT, env=os.environ.copy(), timeout=120)
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
    if name == "hatch-source":
        hatch_launcher = _hatch_launcher_python_and_site()
        if hatch_launcher is not None:
            python_executable, _site_path = hatch_launcher
            return [python_executable, "-c", _HATCH_SOURCE_RUNNER, "run", "specfact"]
        return ["hatch", "run", "specfact"]
    if name == "pip-editable":
        return _create_pip_editable_launcher(workspace)
    if name == "pipx":
        return ["pipx", "run", "--python", sys.executable, "--spec", str(REPO_ROOT), "specfact"]
    if name == "uv-run":
        return [
            "uv",
            "--cache-dir",
            str(workspace / "uv-cache"),
            "run",
            "--no-project",
            "--python",
            sys.executable,
            "--with",
            str(REPO_ROOT),
            "specfact",
        ]
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


def _build_launcher_env(name: str, home: Path, index_path: Path, modules_repo: Path) -> dict[str, str]:
    env = os.environ.copy()
    python_path = str(SRC_ROOT)
    if env.get("PYTHONPATH"):
        python_path = os.pathsep.join([python_path, env["PYTHONPATH"]])
    env.update(
        {
            "HOME": str(home),
            "PYTHONPATH": python_path,
            "SPECFACT_CHILD_PYTHONPATH": python_path,
            "SPECFACT_MODULES_REPO": str(modules_repo),
            "SPECFACT_REGISTRY_INDEX_URL": str(index_path),
            "SPECFACT_ALLOW_UNSIGNED": "1",
            "SPECFACT_NO_TIMING": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )
    hatch_launcher = _hatch_launcher_python_and_site()
    if name == "hatch-source" and hatch_launcher is not None:
        _python_executable, hatch_site_path = hatch_launcher
        env["PYTHONPATH"] = hatch_site_path
    return env


def _assert_module_list_contains(result: subprocess.CompletedProcess[str]) -> None:
    for module_id in MODULE_IDS:
        if module_id not in result.stdout:
            raise AssertionError(f"{module_id} missing from module list output")


def _assert_tokens_present(output: str, command: str, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        if token not in output:
            raise AssertionError(f"`{command}` did not include {token!r}")


def _assert_code_help(cli: list[str], demo: Path, env: dict[str, str]) -> None:
    help_result = _run([*cli, "code", "--help"], cwd=demo, env=env)
    _assert_tokens_present(
        help_result.stdout, "specfact code --help", ("review", "import", "analyze", "drift", "validate", "repro")
    )
    _run([*cli, "code", "review", "run", "--help"], cwd=demo, env=env)
    import_help = _run([*cli, "code", "import", "--help"], cwd=demo, env=env)
    _assert_tokens_present(import_help.stdout, "specfact code import --help", ("from-bridge",))


def _assert_project_help(cli: list[str], demo: Path, env: dict[str, str]) -> None:
    export_help = _run([*cli, "project", "export", "--help"], cwd=demo, env=env)
    if "project export" not in export_help.stdout:
        raise AssertionError("`specfact project export --help` did not render the export command")
    import_project_help = _run([*cli, "project", "import", "--help"], cwd=demo, env=env)
    if "project import" not in import_project_help.stdout:
        raise AssertionError("`specfact project import --help` did not render the import command")
    sync_bridge_help = _run([*cli, "project", "sync", "bridge", "--help"], cwd=demo, env=env)
    if "project sync bridge" not in _normalized_output(sync_bridge_help.stdout):
        raise AssertionError("`specfact project sync bridge --help` did not include the canonical command path")
    flat_sync_help = subprocess.run(
        [*cli, "sync", "bridge", "--help"],
        cwd=demo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
        check=False,
    )
    if flat_sync_help.returncode == 0:
        raise AssertionError("`specfact sync bridge --help` still resolves as a root command")


def _smoke_launcher(name: str, workspace: Path, demo: Path, index_path: Path, modules_repo: Path) -> None:
    home = workspace / f"home-{name}"
    home.mkdir(parents=True)
    cli = _launcher_command(name, workspace / f"launcher-{name}")
    env = _build_launcher_env(name, home, index_path, modules_repo)

    _install_marketplace_modules(cli, demo, env)
    _assert_module_list_contains(_run([*cli, "module", "list"], cwd=demo, env=env))

    _run([*cli, "upgrade", "--help"], cwd=demo, env=env)
    _run([*cli, "module", "upgrade", "--help"], cwd=demo, env=env)
    _run([*cli, "module", "upgrade", "--all", "--yes"], cwd=demo, env=env)

    init_result = _run([*cli, "init", "ide", "--ide", "cursor", "--repo", str(demo), "--force"], cwd=demo, env=env)
    _assert_no_env_warning(init_result)
    explicit_result = _run(
        [*cli, "init", "ide", "--ide", "cursor", "--repo", str(demo), "--force", "--env-manager", "uv"],
        cwd=demo,
        env=env,
    )
    _assert_no_env_warning(explicit_result)

    _assert_code_help(cli, demo, env)
    _assert_project_help(cli, demo, env)
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
        choices=("direct", "hatch-source", "pip-editable", "pipx", "uv-run", "console", "uvx"),
        help="Launcher to test. Repeatable. Defaults to direct.",
    )
    parser.add_argument("--keep-workspace", action="store_true", help="Keep the temporary workspace for debugging")
    args = parser.parse_args()

    modules_repo = _resolve_modules_repo(args.modules_repo)
    workspace_obj: tempfile.TemporaryDirectory[str] | None = None
    if args.keep_workspace:
        workspace = Path(tempfile.mkdtemp(prefix="specfact-runtime-discovery-smoke-"))
    else:
        workspace_obj = tempfile.TemporaryDirectory(prefix="specfact-runtime-discovery-smoke-")
        workspace = Path(workspace_obj.name)
    try:
        index_path = _build_local_registry(workspace, modules_repo)
        for launcher in args.launcher or ["direct"]:
            launcher_workspace = workspace / f"run-{launcher}"
            demo = _create_rootless_monorepo_demo(launcher_workspace, args.demo_repo)
            _smoke_launcher(launcher, launcher_workspace, demo, index_path, modules_repo)
        if args.keep_workspace:
            LOGGER.info("Kept workspace: %s", workspace)
        return 0
    finally:
        if workspace_obj is not None:
            workspace_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
