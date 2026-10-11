#!/usr/bin/env python3
"""Fail-fast real-world smoke checks for runtime discovery and init behavior."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_VERSION_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
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
    smoke_repo = os.environ.get("SPECFACT_SMOKE_MODULES_REPO", "").strip()
    if smoke_repo:
        candidates.append(Path(smoke_repo).expanduser())
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


def _verify_smoke_fixture(modules_repo: Path) -> None:
    """Reject unreviewed fixture bytes before building or executing module archives."""
    identity = json.loads((REPO_ROOT / "ci/runtime-smoke-fixture.lock.json").read_text(encoding="utf-8"))
    if identity.get("repository") != "nold-ai/specfact-cli-modules":
        raise RuntimeError("Smoke fixture identity does not match the reviewed repository")
    for key, revision in (("commit", "HEAD"), ("tree", "HEAD^{tree}")):
        actual = subprocess.check_output(["git", "-C", str(modules_repo), "rev-parse", revision], text=True).strip()
        if actual != identity.get(key):
            raise RuntimeError("Smoke fixture identity does not match the reviewed " + key)
    if subprocess.check_output(["git", "-C", str(modules_repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Smoke fixture identity has unreviewed working-tree bytes")


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


@beartype
@ensure(lambda result: result is None, "tracked module staging must return None")
def _stage_tracked_module(modules_repo: Path, relative: Path, staged_dir: Path) -> None:
    """Read archive bytes from the authenticated Git object, excluding ignored files."""
    identity = json.loads((REPO_ROOT / "ci/runtime-smoke-fixture.lock.json").read_text(encoding="utf-8"))
    archive_bytes = subprocess.check_output(
        ["git", "-C", str(modules_repo), "archive", "--format=tar", f"{identity['commit']}:{relative.as_posix()}"],
        timeout=30,
    )
    staged_dir.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        archive.extractall(staged_dir, filter="data")


def _build_local_registry(workspace: Path, modules_repo: Path) -> Path:
    registry = workspace / "local-registry"
    modules_dir = registry / "modules"
    staging_dir = registry / "staging" / "packages"
    modules_dir.mkdir(parents=True)
    staging_dir.mkdir(parents=True)
    entries: list[dict[str, Any]] = []

    for module_id in _module_dependency_closure(modules_repo):
        bundle_name = module_id.split("/", 1)[1]
        source_dir = modules_repo / "packages" / bundle_name
        staged_dir = staging_dir / bundle_name
        _stage_tracked_module(modules_repo, source_dir.relative_to(modules_repo), staged_dir)

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
                "download_url": archive_path.relative_to(registry).as_posix(),
                "checksum_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                "tier": manifest_data.get("tier", "official"),
                "publisher": manifest_data.get("publisher", {}),
                "bundle_dependencies": manifest_data.get("bundle_dependencies", []),
                "description": manifest_data.get("description", ""),
            }
        )

    index_path = registry / "index.json"
    index_path.write_text(
        json.dumps({"registry_base_url": str(registry.resolve()), "modules": entries}, indent=2),
        encoding="utf-8",
    )
    return index_path


def _create_runtime_venv(venv_dir: Path) -> Path:
    try:
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    except subprocess.CalledProcessError:
        virtualenv = shutil.which("virtualenv")
        if virtualenv is None:
            raise
        _run(
            [
                virtualenv,
                "--app-data",
                str(venv_dir.parent / "virtualenv-app-data"),
                "--no-periodic-update",
                str(venv_dir),
            ],
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            timeout=120,
        )
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _create_pip_editable_launcher(workspace: Path) -> list[str]:
    venv_dir = workspace / "pip-editable-venv"
    python = _create_runtime_venv(venv_dir)
    _run(
        [str(python), "-m", "pip", "install", "-e", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        timeout=180,
    )
    specfact = venv_dir / ("Scripts/specfact.exe" if os.name == "nt" else "bin/specfact")
    return [str(specfact)]


def _frozen_runtime_env(env: dict[str, str], constraints: Path) -> dict[str, str]:
    locks = (REPO_ROOT / "requirements/ci/locked.txt", REPO_ROOT / "requirements/runtime-smoke/locked.txt")
    pins: list[str] = []
    for line in "\n".join(lock.read_text(encoding="utf-8") for lock in locks).splitlines():
        entry = line.strip().rstrip("\\").strip()
        if not entry or entry.startswith(("#", "--hash=")):
            continue
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*==[^;\s]+(?:\s*;.*)?", entry) is None:
            raise RuntimeError("Frozen smoke requirements must contain exact package pins")
        pins.append(entry)
    if not pins:
        raise RuntimeError("Frozen smoke requirements are empty")
    _write(constraints, "\n".join(pins) + "\n")
    env["PYTHONPATH"] = str(SRC_ROOT)
    env["SPECFACT_CHILD_PYTHONPATH"] = env["PYTHONPATH"]
    env["PIP_CONSTRAINT"] = str(constraints)
    env["PIP_NO_INDEX"] = "1"
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONHOME", None)
    env.pop("SPECFACT_MODULES_ROOTS", None)
    env.pop("SPECFACT_CLI_MODULES_REPO", None)
    return env


def _create_isolated_runtime_launcher(name: str, workspace: Path, modules_repo: Path | None = None) -> list[str]:
    venv_dir = workspace / "runtime-venv"
    python = _create_runtime_venv(venv_dir)
    if name == "direct":
        return [str(python), "-m", "specfact_cli.cli"]
    env = _frozen_runtime_env(os.environ.copy(), workspace / "frozen-runtime-constraints.txt")
    if modules_repo is not None:
        env["SPECFACT_SMOKE_MODULES_REPO"] = str(modules_repo)
    _seed_frozen_module_dependencies(workspace, env)
    _run(
        [str(python), "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=env,
        timeout=180,
    )
    return [str(venv_dir / ("Scripts/specfact.exe" if os.name == "nt" else "bin/specfact"))]


def _launcher_command(name: str, workspace: Path, modules_repo: Path | None = None) -> list[str]:
    if name in {"direct", "console"}:
        return _create_isolated_runtime_launcher(name, workspace, modules_repo)
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
    if name in {"direct", "console"}:
        env = _frozen_runtime_env(env, home / "frozen-runtime-constraints.txt")
        child_bin = home.parent / f"launcher-{name}" / "runtime-venv" / ("Scripts" if os.name == "nt" else "bin")
        parent_prefix = Path(sys.prefix).resolve()
        system_paths = [
            part
            for part in env.get("PATH", os.defpath).split(os.pathsep)
            if part and not Path(part).resolve().is_relative_to(parent_prefix)
        ]
        env["PATH"] = os.pathsep.join([str(child_bin), *system_paths])
        env["PIP_FIND_LINKS"] = str(child_bin.parent.parent / "frozen-wheels")
        env["SPECFACT_SMOKE_MODULES_REPO"] = str(modules_repo)
        env["SPECFACT_MODULES_REPO"] = str(index_path.parent / "staging")
        env["SPECFACT_CLI_MODULES_REPO"] = env["SPECFACT_MODULES_REPO"]
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONHOME", None)
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


@beartype
@ensure(lambda result: len(result) > 0, "frozen marketplace requirements must not be empty")
def _frozen_marketplace_requirements(modules_repo: Path) -> str:
    """Select exact exported hashes for the authenticated manifests' dependency closure."""
    pending: set[str] = set()
    for module_id in _module_dependency_closure(modules_repo):
        manifest_path = modules_repo / "packages" / module_id.split("/", 1)[1] / "module-package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        pending.update(canonicalize_name(Requirement(dep).name) for dep in manifest.get("pip_dependencies", []))
        pending.update(canonicalize_name(dep["name"]) for dep in manifest.get("pip_dependencies_versioned", []))
    selected = _frozen_dependency_closure(pending)
    contents = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in ("requirements/ci/locked.txt", "requirements/runtime-smoke/locked.txt")
    )
    blocks: dict[str, str] = {
        canonicalize_name(match[1]): match[0] + "\n"
        for match in re.finditer(
            r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==[^\n]*(?:\n[ \t]+--hash=sha256:[0-9a-f]{64}[^\n]*)*",
            contents,
        )
    }
    if any(name not in blocks or "--hash=sha256:" not in blocks[name] for name in selected):
        raise RuntimeError("Marketplace closure is missing frozen hashes")
    return "".join(blocks[name] for name in sorted(selected))


@beartype
@ensure(lambda result: len(result) > 0, "frozen dependency closure must not be empty")
def _frozen_dependency_closure(roots: set[str]) -> set[str]:
    """Traverse only package identities present in the committed frozen graph."""
    pending = roots.copy()
    packages = {package["name"]: package for package in tomllib.loads((REPO_ROOT / "uv.lock").read_text())["package"]}
    selected: set[str] = set()
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        if name == "lz4":
            continue  # Sole reviewed auxiliary wheel; not part of the core project graph.
        if name not in packages:
            raise RuntimeError(f"Missing frozen hash graph entry for {name}")
        pending.update(dependency["name"] for dependency in packages[name].get("dependencies", []))
    return selected


def _seed_frozen_module_dependencies(workspace: Path, env: dict[str, str]) -> None:
    """Materialize the reviewed frozen graph inside the workspace-owned child."""
    python = workspace / "runtime-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    seed_env = env.copy()
    seed_env.pop("PIP_NO_INDEX", None)
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to materialize the frozen smoke graph")
    _sync_frozen_child(uv, workspace, python, seed_env)
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            "--require-hashes",
            "--no-deps",
            "--only-binary",
            ":all:",
            "--index-url",
            "https://pypi.org/simple",
            "-r",
            str(REPO_ROOT / "requirements/runtime-smoke/locked.txt"),
        ],
        cwd=REPO_ROOT,
        env=seed_env,
        timeout=180,
    )

    _download_frozen_marketplace_wheels(workspace, python, seed_env)


@beartype
@ensure(lambda result: result is None, "frozen child synchronization must return None")
def _sync_frozen_child(uv: str, workspace: Path, python: Path, seed_env: dict[str, str]) -> None:
    """Copy the complete frozen graph from artifact data into the owned child."""
    cache = subprocess.check_output(
        [uv, "cache", "dir"], cwd=REPO_ROOT, env=os.environ.copy(), text=True, timeout=30
    ).strip()
    if not cache or not Path(cache).is_absolute():
        raise RuntimeError("uv must report an absolute reviewed artifact cache path")
    seed_env["UV_CACHE_DIR"] = cache
    seed_env["UV_PROJECT_ENVIRONMENT"] = str((workspace / "runtime-venv").resolve())
    _run(
        [
            uv,
            "sync",
            "--frozen",
            "--all-extras",
            "--no-install-project",
            "--offline",
            "--link-mode",
            "copy",
            "--python",
            str(python),
        ],
        cwd=REPO_ROOT,
        env=seed_env,
        timeout=180,
    )


@beartype
@ensure(lambda result: result is None, "wheel download must return None")
def _download_frozen_marketplace_wheels(workspace: Path, python: Path, seed_env: dict[str, str]) -> None:
    """Authenticate manifests and download only their exported, hash-verified wheels."""
    modules_repo = _resolve_modules_repo(
        seed_env.get("SPECFACT_SMOKE_MODULES_REPO") or seed_env.get("SPECFACT_MODULES_REPO")
    )
    _verify_smoke_fixture(modules_repo)
    requirements = workspace / "frozen-marketplace-requirements.txt"
    _write(requirements, _frozen_marketplace_requirements(modules_repo))
    wheels = workspace / "frozen-wheels"
    wheels.mkdir()
    seed_env["PIP_CACHE_DIR"] = str(workspace.parents[1] / "frozen-pip-cache")
    seed_env["PIP_DEFAULT_TIMEOUT"] = "60"
    _run(
        [
            str(python),
            "-m",
            "pip",
            "download",
            "--require-hashes",
            "--no-deps",
            "--only-binary",
            ":all:",
            "--index-url",
            "https://pypi.org/simple",
            "--dest",
            str(wheels),
            "-r",
            str(requirements),
        ],
        cwd=REPO_ROOT,
        env=seed_env,
        timeout=180,
    )


def _smoke_launcher(name: str, workspace: Path, demo: Path, index_path: Path, modules_repo: Path) -> None:
    home = workspace / f"home-{name}"
    home.mkdir(parents=True)
    cli = _launcher_command(name, workspace / f"launcher-{name}", modules_repo)
    env = _build_launcher_env(name, home, index_path, modules_repo)

    if name in {"direct", "console"}:
        _write(demo / ".pip-tools.toml", "[tool.pip-tools]\nemit-options = false\n")
    if name == "direct":
        _seed_frozen_module_dependencies(workspace / f"launcher-{name}", env)
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
    _verify_smoke_fixture(modules_repo)
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
