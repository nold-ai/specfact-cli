"""Tests for scripts/verify-bundle-published.py gate script."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


def _load_script_module() -> Any:
    """Load scripts/verify-bundle-published.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "verify-bundle-published.py"
    spec = importlib.util.spec_from_file_location("verify_bundle_published", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_index(tmp_path: Path, modules: list[dict[str, Any]] | None = None) -> Path:
    index_path = tmp_path / "index.json"
    payload = {"schema_version": "1.0.0", "modules": modules or []}
    index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return index_path


def test_gate_exits_zero_when_all_bundles_present(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Calling gate with non-empty module list and valid index exits 0."""
    module = _load_script_module()
    index_path = _write_index(
        tmp_path,
        modules=[
            {
                "id": "nold-ai/specfact-project",
                "latest_version": "0.40.0",
                "download_url": "modules/specfact-project-0.40.0.tar.gz",
                "checksum_sha256": "deadbeef",
                "signature_ok": True,
            },
        ],
    )

    # Map module name -> bundle id via explicit mapping to avoid touching real manifests.
    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        assert modules_root.is_dir()
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]

    exit_code = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "PASS" in captured
    assert "specfact-project" in captured


def test_gate_fails_when_registry_index_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Calling gate when index.json is missing exits 1 with an error message."""
    module = _load_script_module()
    missing_index = tmp_path / "missing-index.json"

    exit_code = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(missing_index),
            "--skip-download-check",
        ]
    )
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "Registry index not found" in captured


def test_gate_fails_when_bundle_entry_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Calling gate when a module's bundle has no entry in index.json exits 1."""
    module = _load_script_module()
    index_path = _write_index(tmp_path, modules=[])

    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]

    exit_code = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "MISSING" in captured
    assert "specfact-project" in captured


def test_gate_fails_when_signature_verification_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Signature failure for a bundle entry should cause exit 1 and mention SIGNATURE INVALID."""
    module = _load_script_module()
    index_path = _write_index(
        tmp_path,
        modules=[
            {
                "id": "nold-ai/specfact-project",
                "latest_version": "0.40.0",
                "download_url": "modules/specfact-project-0.40.0.tar.gz",
                "checksum_sha256": "deadbeef",
                "signature_ok": False,
            },
        ],
    )

    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]

    exit_code = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "SIGNATURE INVALID" in captured


def test_empty_module_list_violates_precondition(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Calling gate with empty module list should violate precondition and exit 1."""
    module = _load_script_module()
    index_path = _write_index(tmp_path, modules=[])

    exit_code = module.main(
        [
            "--modules",
            "",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "precondition" in captured.lower()


def test_load_module_bundle_mapping_reads_bundle_field(tmp_path: Path) -> None:
    """Gate reads bundle field from module-package.yaml per module name."""
    module = _load_script_module()
    modules_root = tmp_path / "src" / "specfact_cli" / "modules"
    project_dir = modules_root / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    manifest = project_dir / "module-package.yaml"
    manifest.write_text(
        "\n".join(
            [
                "name: nold-ai/specfact-project",
                "bundle: specfact-project",
                "",
            ]
        ),
        encoding="utf-8",
    )

    mapping = module.load_module_bundle_mapping(["project"], modules_root)
    assert mapping == {"project": "specfact-project"}


def test_skip_download_check_flag_avoids_http_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--skip-download-check flag suppresses download URL verification."""
    module = _load_script_module()
    index_path = _write_index(
        tmp_path,
        modules=[
            {
                "id": "nold-ai/specfact-project",
                "latest_version": "0.40.0",
                "download_url": "https://example.invalid/specfact-project-0.40.0.tar.gz",
                "checksum_sha256": "deadbeef",
                "signature_ok": True,
            },
        ],
    )

    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]

    called: list[str] = []

    def _fake_download(url: str) -> bool:
        called.append(url)
        return True

    module.verify_bundle_download_url = _fake_download  # type: ignore[attr-defined]

    exit_code = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )

    assert exit_code == 0
    assert not called


def test_verify_bundle_published_is_decorated_with_contracts() -> None:
    """verify_bundle_published must have @require and @beartype decorators."""
    module = _load_script_module()

    import inspect

    src = inspect.getsource(module.verify_bundle_published)
    assert "@beartype" in src
    assert "@require" in src


def test_gate_is_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Running gate twice with same inputs should yield same exit code and output."""
    module = _load_script_module()
    index_path = _write_index(
        tmp_path,
        modules=[
            {
                "id": "nold-ai/specfact-project",
                "latest_version": "0.40.0",
                "download_url": "modules/specfact-project-0.40.0.tar.gz",
                "checksum_sha256": "deadbeef",
                "signature_ok": True,
            },
        ],
    )

    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]

    first_exit = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    first_output = capsys.readouterr().out

    second_exit = module.main(
        [
            "--modules",
            "project",
            "--registry-index",
            str(index_path),
            "--skip-download-check",
        ]
    )
    second_output = capsys.readouterr().out

    assert first_exit == second_exit == 0
    assert first_output == second_output


def test_resolve_registry_index_uses_specfact_modules_repo_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When SPECFACT_MODULES_REPO is set, _resolve_registry_index_path returns <path>/registry/index.json."""
    module = _load_script_module()
    modules_repo = tmp_path / "specfact-cli-modules"
    registry_dir = modules_repo / "registry"
    registry_dir.mkdir(parents=True)
    (registry_dir / "index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(modules_repo))
    index_path = module._resolve_registry_index_path()
    assert index_path == modules_repo / "registry" / "index.json"
    assert index_path.exists()


def test_resolve_registry_index_uses_worktree_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When SPECFACT_REPO_ROOT points at a worktree root, resolver finds sibling specfact-cli-modules."""
    module = _load_script_module()
    worktree_root = tmp_path / "specfact-cli-worktrees" / "feature" / "branch"
    worktree_root.mkdir(parents=True)
    sibling = tmp_path / "specfact-cli-modules"
    (sibling / "registry").mkdir(parents=True)
    (sibling / "registry" / "index.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("SPECFACT_MODULES_REPO", raising=False)
    monkeypatch.setenv("SPECFACT_REPO_ROOT", str(worktree_root))
    index_path = module._resolve_registry_index_path()
    assert index_path == sibling / "registry" / "index.json"
    assert index_path.exists()


def test_check_bundle_in_registry_rejects_missing_required_fields(tmp_path: Path) -> None:
    """Gate should fail entry validation when required bundle fields are missing."""
    module = _load_script_module()
    index_payload = {"modules": []}
    entry = {"id": "nold-ai/specfact-project", "latest_version": "0.40.0"}

    result = module.check_bundle_in_registry(
        module_name="project",
        bundle_id="specfact-project",
        entry=entry,
        index_payload=index_payload,
        index_path=tmp_path / "index.json",
        skip_download_check=True,
    )

    assert result.status == "FAIL"
    assert "missing required fields" in result.message.lower()


def test_verify_bundle_published_uses_artifact_signature_validation(tmp_path: Path) -> None:
    """Real artifact signature validation result should drive SIGNATURE INVALID state."""
    module = _load_script_module()
    index_path = _write_index(
        tmp_path,
        modules=[
            {
                "id": "nold-ai/specfact-project",
                "latest_version": "0.40.0",
                "download_url": "modules/specfact-project-0.40.0.tar.gz",
                "checksum_sha256": "deadbeef",
                "signature_url": "signatures/specfact-project-0.40.0.tar.sig",
                "tier": "official",
                "signature_ok": True,
            },
        ],
    )

    def _fake_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
        return dict.fromkeys(module_names, "specfact-project")

    module.load_module_bundle_mapping = _fake_mapping  # type: ignore[attr-defined]
    module.verify_bundle_signature = lambda *_args, **_kwargs: False  # type: ignore[attr-defined]

    results = module.verify_bundle_published(
        module_names=["project"],
        index_path=index_path,
        skip_download_check=True,
    )

    assert len(results) == 1
    assert results[0].status == "FAIL"
    assert results[0].message == "SIGNATURE INVALID"
