"""E2E tests for bundle extraction publish/install flows."""

from __future__ import annotations

import importlib.util
import json
import tarfile
from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "publish-module.py"


def _load_publish_module():
    spec = importlib.util.spec_from_file_location("publish_module_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load publish-module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_bundle_package(tmp_path: Path, bundle_name: str, version: str = "0.39.0") -> Path:
    bundle_dir = tmp_path / "packages" / bundle_name
    src_dir = bundle_dir / "src" / bundle_name.replace("-", "_")
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    (bundle_dir / "module-package.yaml").write_text(
        "\n".join(
            [
                f"name: nold-ai/{bundle_name}",
                f"version: {version}",
                "commands: [code]",
                "tier: official",
                "publisher: nold-ai",
                "bundle_dependencies: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_dir


def test_module_install_codebase_and_code_analyze_help_resolves(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        lambda *_, **__: tmp_path / ".specfact" / "modules" / "specfact-codebase",
    )
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)

    install_result = runner.invoke(
        app,
        [
            "module",
            "install",
            "nold-ai/specfact-codebase",
            "--source",
            "marketplace",
            "--scope",
            "project",
            "--repo",
            str(tmp_path),
        ],
    )
    assert install_result.exit_code == 0

    code_help = runner.invoke(app, ["code", "analyze", "--help"])
    assert code_help.exit_code == 0
    assert "analyze" in (code_help.stdout or "").lower()


def test_publish_install_verify_roundtrip_for_specfact_codebase(monkeypatch, tmp_path: Path) -> None:
    publish = _load_publish_module()
    registry_dir = tmp_path / "registry"
    (registry_dir / "modules").mkdir(parents=True, exist_ok=True)
    (registry_dir / "signatures").mkdir(parents=True, exist_ok=True)
    (registry_dir / "index.json").write_text(json.dumps({"modules": []}, indent=2) + "\n", encoding="utf-8")

    packages_root = tmp_path / "packages"
    _create_bundle_package(tmp_path, "specfact-codebase")
    key_file = tmp_path / "private.pem"
    key_file.write_text("dummy-private-key", encoding="utf-8")

    monkeypatch.setattr(publish, "BUNDLE_PACKAGES_ROOT", packages_root)
    publish.publish_bundle("specfact-codebase", key_file, registry_dir)

    index = json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))
    entry = next(item for item in index["modules"] if item["id"] == "nold-ai/specfact-codebase")
    tarball = registry_dir / "modules" / Path(entry["download_url"]).name
    assert tarball.exists()

    monkeypatch.setattr("specfact_cli.registry.module_installer.resolve_dependencies", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "specfact_cli.registry.module_installer.install_resolved_pip_requirements", lambda *_a, **_k: None
    )
    monkeypatch.setattr("specfact_cli.registry.module_installer.verify_module_artifact", lambda *_a, **_k: True)
    monkeypatch.setattr("specfact_cli.registry.module_installer.ensure_publisher_trusted", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.registry.module_installer.assert_module_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr("specfact_cli.registry.module_installer.download_module", lambda *_a, **_k: tarball)

    from specfact_cli.registry.module_installer import install_module

    install_root = tmp_path / ".specfact" / "modules"
    installed_path = install_module("nold-ai/specfact-codebase", install_root=install_root)
    assert (installed_path / "module-package.yaml").exists()

    signature_file = next((registry_dir / "signatures").glob("*.sig"))
    manifest = {
        "name": "nold-ai/specfact-codebase",
        "version": entry["latest_version"],
    }
    assert publish.verify_bundle(tarball, signature_file, manifest) is True

    with tarfile.open(tarball, "r:gz") as archive:
        names = [member.name for member in archive.getmembers()]
    assert names
