import importlib.util
import marshal
import py_compile
import subprocess
import sys
from pathlib import Path
from shutil import copytree, ignore_patterns

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry import module_installer
from specfact_cli.registry.crypto_validator import verify_signature
from specfact_cli.registry.module_packages import discover_package_metadata


def test_official_archive_is_checked_before_extraction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "project.tar.gz"
    archive.write_bytes(b"unapproved artifact")
    monkeypatch.setattr(module_installer, "_download_archive_with_cache", lambda *_args, **_kwargs: archive)

    def unexpected_extract(_archive: Path, _root: Path) -> None:
        pytest.fail("archive extraction ran before the release cutoff check")

    monkeypatch.setattr(module_installer, "_extract_marketplace_archive", unexpected_extract)
    with pytest.raises(ValueError, match="approved release cutoff"):
        module_installer.install_module(
            "nold-ai/specfact-project",
            module_installer.InstallModuleOptions(version="0.41.27", install_root=tmp_path / "installed"),
        )


def test_official_filesystem_verification_requires_cutoff_bytes(tmp_path: Path) -> None:
    meta = ModulePackageMetadata(name="nold-ai/specfact-project", version="0.41.27", commands=["project"])
    (tmp_path / "module-package.yaml").write_text(
        "name: nold-ai/specfact-project\nversion: 0.41.27\ncommands: [project]\n", encoding="utf-8"
    )
    assert not module_installer.verify_module_artifact(tmp_path, meta, allow_unsigned=True)


def test_cutoff_shipped_module_remains_available(tmp_path: Path) -> None:
    shipped = Path(module_installer.__file__).parents[1] / "modules" / "module_registry"
    installed = tmp_path / "module_registry"
    copytree(shipped, installed)
    meta = discover_package_metadata(tmp_path)[0][1]
    assert module_installer.verify_module_artifact(installed, meta)

    manifest = installed / "module-package.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not module_installer.verify_module_artifact(installed, meta, allow_unsigned=True)


def test_post_cutoff_release_is_rejected_before_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_download(*_args: object, **_kwargs: object) -> Path:
        pytest.fail("a post-cutoff official release should not reach marketplace download")

    monkeypatch.setattr(module_installer, "_download_archive_with_cache", unexpected_download)
    with pytest.raises(ValueError, match="approved release cutoff"):
        module_installer.install_module(
            "nold-ai/specfact-project",
            module_installer.InstallModuleOptions(version="1.0.0", install_root=tmp_path),
        )


def test_retired_public_key_cannot_authorize_a_signature() -> None:
    key = Path(module_installer.__file__).parents[3] / "resources" / "keys" / "module-signing-public.pem"
    with pytest.raises(ValueError, match="signing key is revoked"):
        verify_signature(b"test data", "YQ==", key.read_text(encoding="utf-8"))


def test_bundled_release_accepts_relocated_installer_cache(tmp_path: Path) -> None:
    shipped = Path(module_installer.__file__).parents[1] / "modules" / "module_registry"
    installed = tmp_path / "module_registry"
    copytree(shipped, installed)
    source = installed / "src/app.py"
    pycache = Path(importlib.util.cache_from_source(str(source)))
    compiled_path = tmp_path / "staging/specfact_cli/modules/module_registry/src/app.py"
    py_compile.compile(str(source), dfile=str(compiled_path), doraise=True)
    meta = discover_package_metadata(tmp_path)[0][1]
    assert module_installer.verify_module_artifact(installed, meta)
    pycache.write_bytes(pycache.read_bytes() + b"changed cache")
    assert not module_installer.verify_module_artifact(installed, meta)


def test_bundled_release_accepts_standard_import_cache(tmp_path: Path) -> None:
    shipped = Path(module_installer.__file__).parents[1] / "modules" / "module_registry"
    staging = tmp_path / "staging" / "module_registry"
    copytree(shipped, staging, ignore=ignore_patterns("__pycache__"))
    options = ["-I", "-S"]
    if sys.flags.optimize:
        options.append("-" + "O" * sys.flags.optimize)
    subprocess.run(
        [
            sys.executable,
            *options,
            "-c",
            (
                "import importlib.machinery, sys; "
                + "loader = importlib.machinery.SourceFileLoader('fixture', sys.argv[1]); loader.get_code('fixture')"
            ),
            str(staging / "src/commands.py"),
        ],
        check=True,
        timeout=10,
    )
    installed = tmp_path / "installed" / "module_registry"
    copytree(staging, installed)
    cache = Path(importlib.util.cache_from_source(str(installed / "src/commands.py")))
    assert cache.is_file()
    meta = discover_package_metadata(installed.parent)[0][1]
    assert module_installer.verify_module_artifact(installed, meta)
    cache.write_bytes(cache.read_bytes() + b"changed cache")
    assert not module_installer.verify_module_artifact(installed, meta)


def test_cache_comparison_preserves_literal_byte_values() -> None:
    reference = marshal.dumps(compile(r"value = b'\xda'", "fixture.py", "exec"))
    other = marshal.dumps(compile(r"value = b'\xfa'", "fixture.py", "exec"))
    assert not module_installer._authenticated_cache_body_matches(other, reference)
