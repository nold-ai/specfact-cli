from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry.module_installer import _module_artifact_payload_signed
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
        REPO_ROOT.parents[2] / "specfact-cli-modules",
    ]
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


def _build_local_registry(home_dir: Path) -> Path:
    registry_root = home_dir / ".specfact-local-registry"
    modules_dir = registry_root / "modules"
    staging_dir = registry_root / ".staging"
    modules_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    modules_payload: list[dict[str, object]] = []
    packages_root = MODULES_REPO / "packages"

    for module_id in official_marketplace_module_ids():
        bundle_name = module_id.split("/", 1)[1]
        package_dir = packages_root / bundle_name
        staged_package_dir = staging_dir / bundle_name
        if staged_package_dir.exists():
            shutil.rmtree(staged_package_dir)
        shutil.copytree(package_dir, staged_package_dir)

        staged_manifest_path = staged_package_dir / "module-package.yaml"
        staged_manifest = yaml.safe_load(staged_manifest_path.read_text(encoding="utf-8"))
        assert isinstance(staged_manifest, dict), f"Invalid manifest: {staged_manifest_path}"
        staged_manifest["integrity"] = {
            "checksum": f"sha256:{hashlib.sha256(_module_artifact_payload_signed(staged_package_dir)).hexdigest()}"
        }
        staged_manifest_path.write_text(
            yaml.safe_dump(staged_manifest, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )

        manifest_path = package_dir / "module-package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(manifest, dict), f"Invalid manifest: {manifest_path}"
        manifest_dict = cast(dict[str, Any], manifest)

        version = str(manifest_dict["version"]).strip()
        archive_name = f"{bundle_name}-{version}.tar.gz"
        archive_path = modules_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(staged_package_dir, arcname=bundle_name)

        checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        modules_payload.append(
            {
                "id": module_id,
                "latest_version": version,
                "download_url": f"modules/{archive_name}",
                "checksum_sha256": checksum,
                "tier": manifest_dict.get("tier", "official"),
                "publisher": manifest_dict.get("publisher", {}),
                "bundle_dependencies": manifest_dict.get("bundle_dependencies", []),
                "description": manifest_dict.get("description", ""),
            }
        )

    index_path = registry_root / "index.json"
    index_path.write_text(json.dumps({"modules": modules_payload}, indent=2), encoding="utf-8")
    return index_path


def _seed_marketplace_modules(home_dir: Path) -> None:
    modules_root = home_dir / ".specfact" / "modules"
    modules_root.mkdir(parents=True, exist_ok=True)
    packages_root = MODULES_REPO / "packages"

    for module_id in official_marketplace_module_ids():
        bundle_name = module_id.split("/", 1)[1]
        package_dir = packages_root / bundle_name
        installed_dir = modules_root / bundle_name
        if installed_dir.exists():
            shutil.rmtree(installed_dir)
        shutil.copytree(package_dir, installed_dir)

        manifest_path = installed_dir / "module-package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(manifest, dict), f"Invalid manifest: {manifest_path}"
        manifest["integrity"] = {
            "checksum": f"sha256:{hashlib.sha256(_module_artifact_payload_signed(installed_dir)).hexdigest()}"
        }
        manifest_path.write_text(
            yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
        (installed_dir / ".specfact-registry-id").write_text(module_id, encoding="utf-8")


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
    env["SPECFACT_REGISTRY_INDEX_URL"] = _build_local_registry(home_dir).resolve().as_uri()
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


def _run_help_case(
    case: CommandAuditCase, home_dir: Path, env: dict[str, str], monkeypatch: pytest.MonkeyPatch
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


@pytest.mark.timeout(300)
def test_command_audit_help_cases_execute_cleanly_in_temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    env = _subprocess_env(home_dir)
    _seed_marketplace_modules(home_dir)

    failures: list[str] = []
    for case in build_command_audit_cases():
        if case.mode == "help-only":
            return_code, merged_output = _run_help_case(case, home_dir, env, monkeypatch)
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
