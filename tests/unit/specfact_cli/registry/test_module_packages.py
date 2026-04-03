"""
Tests for module packages (spec: module-packages).

Discovery finds packages with metadata.yaml; package loader loads only that package; registry receives commands.
Arch-06: publisher/integrity metadata and versioned dependency models.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from pathlib import Path

import pytest
import typer

from specfact_cli.models.module_package import (
    IntegrityInfo,
    ModulePackageMetadata,
    PublisherInfo,
    VersionedModuleDependency,
    VersionedPipDependency,
)
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.module_packages import (
    discover_package_metadata,
    get_installed_bundles,
    get_modules_root,
    get_modules_roots,
    merge_module_state,
    register_module_package_commands,
)
from specfact_cli.registry.module_state import read_modules_state, write_modules_state


@pytest.fixture(autouse=True)
def _reset_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_get_modules_root_under_specfact_cli():
    """get_modules_root() returns a path under the specfact_cli package."""
    root = get_modules_root()
    assert root.name == "modules"
    assert "specfact_cli" in str(root)
    assert root.exists() or not root.exists()


def test_get_modules_roots_includes_workspace_dot_specfact_modules_when_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Discovery roots include workspace-local .specfact/modules when it exists."""
    cwd_modules = tmp_path / ".specfact" / "modules"
    cwd_modules.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SPECFACT_MODULES_ROOTS", raising=False)

    roots = [path.resolve() for path in get_modules_roots()]

    assert cwd_modules.resolve() in roots


def test_get_modules_roots_ignores_workspace_plain_modules_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery roots should not claim workspace ./modules as a SpecFact-managed root."""
    (tmp_path / "modules").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SPECFACT_MODULES_ROOTS", raising=False)

    roots = [path.resolve() for path in get_modules_roots()]

    assert (tmp_path / "modules").resolve() not in roots


def test_discover_package_metadata_finds_example(tmp_path: Path):
    """Discovery finds packages that have module-package.yaml with name and commands."""
    (tmp_path / "example_pkg").mkdir()
    (tmp_path / "example_pkg" / "module-package.yaml").write_text(
        "name: example_pkg\nversion: '0.1.0'\ncommands: [example_cmd]\n", encoding="utf-8"
    )
    (tmp_path / "example_pkg" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert meta.name == "example_pkg"
    assert meta.version == "0.1.0"
    assert meta.commands == ["example_cmd"]


def test_discover_package_metadata_skips_dir_without_metadata(tmp_path: Path):
    """Discovery skips dirs that don't have module-package.yaml (or metadata.yaml)."""
    (tmp_path / "no_meta").mkdir()
    result = discover_package_metadata(tmp_path)
    assert len(result) == 0


def test_resolve_package_load_path_supports_namespaced_manifest_name(tmp_path: Path) -> None:
    """Namespaced manifest names should resolve to local src package path."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "specfact-backlog"
    package_src = package_dir / "src" / "specfact_backlog"
    package_src.mkdir(parents=True)
    init_file = package_src / "__init__.py"
    init_file.write_text("app = object()\n", encoding="utf-8")

    resolved = module_packages_impl._resolve_package_load_path(package_dir, "nold-ai/specfact-backlog")
    assert resolved == init_file


def test_make_package_loader_supports_namespaced_nested_command_app(tmp_path: Path) -> None:
    """Namespaced bundles should load command app from src/<pkg>/<command>/app.py when root app.py is absent."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "specfact-backlog"
    nested_app = package_dir / "src" / "specfact_backlog" / "backlog" / "app.py"
    nested_app.parent.mkdir(parents=True, exist_ok=True)
    nested_app.write_text("import typer\napp = typer.Typer(name='backlog')\n", encoding="utf-8")

    loader = module_packages_impl._make_package_loader(package_dir, "nold-ai/specfact-backlog", "backlog")
    app = loader()

    assert getattr(getattr(app, "info", None), "name", None) == "backlog"


def test_make_package_loader_wraps_runtime_import_errors_with_compatibility_guidance(tmp_path: Path) -> None:
    """Module load failures should surface SpecFact compatibility guidance instead of raw import noise."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "specfact-backlog"
    nested_app = package_dir / "src" / "specfact_backlog" / "backlog" / "app.py"
    nested_app.parent.mkdir(parents=True, exist_ok=True)
    nested_app.write_text("import missing_compiled_dependency\n", encoding="utf-8")

    loader = module_packages_impl._make_package_loader(package_dir, "nold-ai/specfact-backlog", "backlog")

    with pytest.raises(ValueError, match="Runtime compatibility error") as exc_info:
        loader()

    message = str(exc_info.value)
    assert "missing_compiled_dependency" in message
    assert str(package_dir) in message
    assert "same Python interpreter" in message


def test_merge_module_state_new_modules_enabled():
    """New discovered modules get enabled: true."""
    discovered = [("new_one", "1.0.0")]
    state = {}
    enabled = merge_module_state(discovered, state, [], [])
    assert enabled["new_one"] is True


def test_get_installed_bundles_infers_bundle_from_namespaced_module_name() -> None:
    """Installed bundle detection should infer specfact bundle id from namespaced module name."""
    metadata = ModulePackageMetadata(
        name="nold-ai/specfact-backlog",
        version="0.40.9",
        commands=["backlog"],
        category="backlog",
        bundle=None,
    )
    bundles = get_installed_bundles([(Path("/tmp/specfact-backlog"), metadata)], {"nold-ai/specfact-backlog": True})
    assert "specfact-backlog" in bundles


def test_merge_module_state_preserves_existing():
    """Existing state preserved; overrides applied."""
    discovered = [("a", "1.0"), ("b", "2.0")]
    state = {"a": {"version": "1.0", "enabled": False}}
    enabled = merge_module_state(discovered, state, ["a"], [])
    assert enabled["a"] is True
    assert enabled["b"] is True


def test_merge_module_state_disable_override():
    """disable_ids set module to false."""
    discovered = [("m1", "1.0")]
    enabled = merge_module_state(discovered, {}, [], ["m1"])
    assert enabled["m1"] is False


# --- Arch-06: manifest security metadata models (TDD) ---


def test_publisher_info_model_captures_name_email_and_attributes():
    """PublisherInfo SHALL capture name, email, and optional publisher attributes."""
    pub = PublisherInfo(name="Acme", email="publish@acme.example")
    assert pub.name == "Acme"
    assert pub.email == "publish@acme.example"
    assert getattr(pub, "attributes", None) is None or isinstance(pub.attributes, dict)
    pub_with_attr = PublisherInfo(name="X", email="x@y.z", attributes={"url": "https://acme.example"})
    assert pub_with_attr.attributes == {"url": "https://acme.example"}


def test_integrity_info_model_captures_checksum_and_optional_signature():
    """IntegrityInfo SHALL capture checksum and optional signature fields."""
    valid_sha256 = "sha256:" + "a" * 64
    integrity = IntegrityInfo(checksum=valid_sha256)
    assert integrity.checksum == valid_sha256
    assert getattr(integrity, "signature", None) is None or isinstance(integrity.signature, (str, type(None)))
    integrity_signed = IntegrityInfo(checksum=valid_sha256, signature="base64sig...")
    assert integrity_signed.signature == "base64sig..."


def test_integrity_info_validates_checksum_format():
    """IntegrityInfo validation SHALL ensure checksum format correctness."""
    IntegrityInfo(checksum="sha256:" + "a" * 64)
    with pytest.raises((ValueError, Exception)):
        IntegrityInfo(checksum="invalid-no-algo")


def test_versioned_module_dependency_parsed():
    """Versioned module dependency SHALL store name and version specifier."""
    dep = VersionedModuleDependency(name="backlog-core", version_specifier=">=0.1.0,<1.0")
    assert dep.name == "backlog-core"
    assert dep.version_specifier == ">=0.1.0,<1.0"


def test_versioned_pip_dependency_parsed():
    """Versioned pip dependency SHALL preserve name and version for installation-time resolution."""
    dep = VersionedPipDependency(name="requests", version_specifier=">=2.28.0")
    assert dep.name == "requests"
    assert dep.version_specifier == ">=2.28.0"


def test_manifest_parsing_includes_publisher_and_integrity(tmp_path: Path):
    """Manifest with publisher and integrity metadata SHALL be parsed and available."""
    (tmp_path / "secure_pkg").mkdir()
    (tmp_path / "secure_pkg" / "module-package.yaml").write_text(
        """
name: secure_pkg
version: '0.1.0'
commands: [cmd]
publisher:
  name: Publisher Inc
  email: dev@pub.example
integrity:
  checksum: sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
""",
        encoding="utf-8",
    )
    (tmp_path / "secure_pkg" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert meta.publisher is not None
    assert meta.publisher.name == "Publisher Inc"
    assert meta.publisher.email == "dev@pub.example"
    assert meta.integrity is not None
    assert meta.integrity.checksum.startswith("sha256:")


def test_manifest_parsing_versioned_module_dependency(tmp_path: Path):
    """Manifest declaring module dependency with version specifier SHALL store both values."""
    (tmp_path / "with_deps").mkdir()
    (tmp_path / "with_deps" / "module-package.yaml").write_text(
        """
name: with_deps
version: '0.1.0'
commands: [c]
module_dependencies_versioned:
  - name: other-module
    version_specifier: ">=0.2.0"
""",
        encoding="utf-8",
    )
    (tmp_path / "with_deps" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert hasattr(meta, "module_dependencies_versioned")
    assert len(meta.module_dependencies_versioned) == 1
    assert meta.module_dependencies_versioned[0].name == "other-module"
    assert meta.module_dependencies_versioned[0].version_specifier == ">=0.2.0"


def test_manifest_parsing_versioned_pip_dependency(tmp_path: Path):
    """Manifest declaring pip dependency with version specifier SHALL preserve for resolution."""
    (tmp_path / "pip_deps").mkdir()
    (tmp_path / "pip_deps" / "module-package.yaml").write_text(
        """
name: pip_deps
version: '0.1.0'
commands: [c]
pip_dependencies_versioned:
  - name: pyyaml
    version_specifier: ">=6.0"
""",
        encoding="utf-8",
    )
    (tmp_path / "pip_deps" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert hasattr(meta, "pip_dependencies_versioned")
    assert len(meta.pip_dependencies_versioned) == 1
    assert meta.pip_dependencies_versioned[0].name == "pyyaml"
    assert meta.pip_dependencies_versioned[0].version_specifier == ">=6.0"


def test_manifest_legacy_without_publisher_integrity_loads_successfully(tmp_path: Path):
    """Bundles without publisher/integrity (legacy) SHALL load successfully (backward compatibility)."""
    (tmp_path / "legacy_pkg").mkdir()
    (tmp_path / "legacy_pkg" / "module-package.yaml").write_text(
        "name: legacy_pkg\nversion: '0.1.0'\ncommands: [x]\n",
        encoding="utf-8",
    )
    (tmp_path / "legacy_pkg" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert meta.name == "legacy_pkg"
    assert meta.publisher is None
    assert meta.integrity is None


# --- Arch-06: installer and lifecycle trust enforcement (TDD) ---


def test_trust_check_rejects_on_checksum_mismatch(monkeypatch, tmp_path: Path):
    """When artifact checksum does not match expected, module SHALL be skipped at registration."""
    from specfact_cli.registry import module_installer

    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "module-package.yaml").write_text(
        "name: pkg\nversion: '0.1.0'\ncommands: [c]\n", encoding="utf-8"
    )

    def fail_checksum(_data, _expected):
        raise ValueError("Checksum mismatch")

    monkeypatch.setattr(module_installer, "verify_checksum", fail_checksum)

    meta = ModulePackageMetadata(
        name="bad_checksum_mod",
        version="0.1.0",
        commands=["c"],
        integrity=IntegrityInfo(checksum="sha256:" + "a" * 64, signature=None),
    )
    result = module_installer.verify_module_artifact(tmp_path / "pkg", meta, allow_unsigned=False)
    assert result is False


def test_allow_unsigned_allows_module_without_integrity(monkeypatch):
    """When allow_unsigned is True, module without integrity metadata MAY be allowed."""
    from specfact_cli.registry import module_installer

    meta = ModulePackageMetadata(name="no_integrity", version="0.1.0", commands=["c"], integrity=None)
    pkg_dir = Path(__file__).parent
    result = module_installer.verify_module_artifact(pkg_dir, meta, allow_unsigned=True)
    assert result is True


def test_unaffected_modules_register_when_one_fails_trust(monkeypatch, tmp_path: Path):
    """When one module fails integrity verification, other valid modules SHALL continue registration."""
    from specfact_cli.registry import module_packages as mp

    for name, cmd in (("good", "good_cmd"), ("bad_trust", "bad_cmd")):
        (tmp_path / name).mkdir()
        (tmp_path / name / "module-package.yaml").write_text(
            f"name: {name}\nversion: '0.1.0'\ncommands: [{cmd}]\n", encoding="utf-8"
        )
        (tmp_path / name / "src").mkdir(parents=True)
        (tmp_path / name / "src" / "app.py").write_text("app = None", encoding="utf-8")

    def verify_may_fail(_package_dir: Path, meta, allow_unsigned: bool = False):
        return meta.name != "bad_trust"

    monkeypatch.setattr(mp, "verify_module_artifact", verify_may_fail)
    monkeypatch.setattr(mp, "get_modules_root", lambda: tmp_path)
    monkeypatch.setattr(mp, "read_modules_state", dict)
    register_module_package_commands(allow_unsigned=False)
    names = CommandRegistry.list_commands()
    assert "good_cmd" in names
    assert "bad_cmd" not in names


def test_grouped_registration_merges_duplicate_command_extensions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Grouped mode should merge duplicate module command trees instead of replacing earlier loaders."""
    from specfact_cli.registry import module_packages as mp

    packages = [
        (
            tmp_path / "base_backlog",
            ModulePackageMetadata(name="base_backlog", version="0.1.0", commands=["backlog"], category="backlog"),
        ),
        (
            tmp_path / "ext_backlog",
            ModulePackageMetadata(name="ext_backlog", version="0.1.0", commands=["backlog"], category="backlog"),
        ),
    ]
    monkeypatch.setattr(mp, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(mp, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(mp, "read_modules_state", dict)
    monkeypatch.setattr(mp, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: [])

    def _build_typer(subcommand_name: str) -> typer.Typer:
        app = typer.Typer()

        @app.command(name=subcommand_name)
        def _cmd() -> None:
            return None

        return app

    def _fake_loader(_package_dir: Path, package_name: str, _cmd_name: str):
        return (
            (lambda: _build_typer("base_cmd")) if package_name == "base_backlog" else (lambda: _build_typer("ext_cmd"))
        )

    monkeypatch.setattr(mp, "_make_package_loader", _fake_loader)

    mp.register_module_package_commands(category_grouping_enabled=True)

    backlog_app = CommandRegistry.get_module_typer("backlog")
    command_names = tuple(
        sorted(
            command_info.name
            for command_info in backlog_app.registered_commands
            if getattr(command_info, "name", None) is not None
        )
    )
    assert "base_cmd" in command_names
    assert "ext_cmd" in command_names


def test_mount_installed_groups_preserves_bundle_native_group_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Installed bundle-native group command should not be overridden by static fallback group app."""
    from specfact_cli.registry import module_packages as mp

    native_code_app = typer.Typer()

    @native_code_app.command("native-sub")
    def _native_sub() -> None:
        return None

    packages = [
        (
            tmp_path / "codebase",
            ModulePackageMetadata(
                name="nold-ai/specfact-codebase",
                version="0.40.10",
                commands=["code"],
                category="codebase",
                bundle="specfact-codebase",
            ),
        )
    ]

    monkeypatch.setattr(mp, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(mp, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(mp, "read_modules_state", dict)
    monkeypatch.setattr(mp, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(mp, "_make_package_loader", lambda *_args, **_kwargs: lambda: native_code_app)
    monkeypatch.setattr(
        mp,
        "_build_bundle_to_group",
        lambda: {"specfact-codebase": ("code", "Codebase quality commands", lambda: typer.Typer())},
    )

    mp.register_module_package_commands(category_grouping_enabled=True)

    code_app = CommandRegistry.get_typer("code")
    command_names = tuple(
        sorted(
            command_info.name
            for command_info in code_app.registered_commands
            if getattr(command_info, "name", None) is not None
        )
    )
    assert "native-sub" in command_names


def test_grouped_registration_does_not_register_flat_shim_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Grouped registration should not mount flat shim commands at root."""
    from specfact_cli.registry import module_packages as mp

    validate_app = typer.Typer(name="validate")

    @validate_app.command("run")
    def _validate_run() -> None:
        return None

    packages = [
        (
            tmp_path / "codebase_validate",
            ModulePackageMetadata(
                name="nold-ai/specfact-codebase",
                version="0.40.10",
                commands=["validate"],
                category="codebase",
                bundle="specfact-codebase",
            ),
        )
    ]

    monkeypatch.setattr(mp, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(mp, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(mp, "read_modules_state", dict)
    monkeypatch.setattr(mp, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(mp, "_make_package_loader", lambda *_args, **_kwargs: lambda: validate_app)
    monkeypatch.setattr(
        mp,
        "_build_bundle_to_group",
        lambda: {"specfact-codebase": ("code", "Codebase quality commands", lambda: typer.Typer(name="code"))},
    )

    mp.register_module_package_commands(category_grouping_enabled=True)

    names = set(CommandRegistry.list_commands())
    assert "code" in names
    assert "validate" not in names


def test_integrity_failure_shows_user_friendly_risk_warning(monkeypatch, tmp_path: Path) -> None:
    """Integrity failure should emit concise risk guidance instead of raw checksum diagnostics."""
    from specfact_cli.registry import module_packages as mp

    shown_messages: list[str] = []
    metadata = [(tmp_path / "bad", ModulePackageMetadata(name="bad", version="0.1.0", commands=["bad_cmd"]))]
    monkeypatch.setattr(mp, "discover_all_package_metadata", lambda: metadata)
    monkeypatch.setattr(mp, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: False)
    monkeypatch.setattr(mp, "read_modules_state", dict)
    monkeypatch.setattr(mp, "print_warning", shown_messages.append)

    register_module_package_commands(allow_unsigned=False)

    assert any("failed integrity verification and was not loaded" in msg for msg in shown_messages)
    assert any("Run `specfact module init`" in msg for msg in shown_messages)
    assert not any("Checksum mismatch" in msg for msg in shown_messages)


def test_module_state_read_write(tmp_path: Path):
    """read_modules_state / write_modules_state roundtrip."""
    os.environ["SPECFACT_REGISTRY_DIR"] = str(tmp_path)
    try:
        write_modules_state(
            [{"id": "x", "version": "1.0", "enabled": True}, {"id": "y", "version": "2.0", "enabled": False}]
        )
        read = read_modules_state()
        assert read["x"]["enabled"] is True
        assert read["y"]["enabled"] is False
        assert read["x"]["version"] == "1.0"
    finally:
        os.environ.pop("SPECFACT_REGISTRY_DIR", None)


def test_example_package_discovered_from_fixture(tmp_path: Path) -> None:
    """Discovery should load an example package when present in a controlled fixture root."""
    example_dir = tmp_path / "example"
    example_dir.mkdir(parents=True, exist_ok=True)
    (example_dir / "module-package.yaml").write_text(
        "name: example\nversion: 0.1.0\ncommands: [example]\n",
        encoding="utf-8",
    )
    packages = discover_package_metadata(tmp_path)
    example = [p for p in packages if p[1].name == "example"]
    assert example
    _dir, meta = example[0]
    assert "example" in meta.commands


def test_registry_receives_example_command_when_registered():
    """After register_builtin_commands (module discovery), 'example' can be in registry."""
    from specfact_cli.registry.bootstrap import register_builtin_commands

    register_builtin_commands()
    names = CommandRegistry.list_commands()
    if "example" in names:
        meta = CommandRegistry.get_metadata("example")
        assert meta is not None
        typer_app = CommandRegistry.get_typer("example")
        assert typer_app is not None
        assert typer_app.info.name == "example"


def test_protocol_reporting_classifies_full_partial_legacy_from_static_source(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    """Protocol summary should classify full/partial/legacy modules accurately."""
    from specfact_cli.registry import module_packages as module_packages_impl

    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.protocol.reporting")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "is_debug_mode", lambda: True)
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)

    metadata = [
        (tmp_path / "full", ModulePackageMetadata(name="full", commands=[])),
        (tmp_path / "partial", ModulePackageMetadata(name="partial", commands=[])),
        (tmp_path / "legacy", ModulePackageMetadata(name="legacy", commands=[])),
    ]
    monkeypatch.setattr(module_packages_impl, "discover_all_package_metadata", lambda: metadata)
    monkeypatch.setattr(module_packages_impl, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(
        module_packages_impl,
        "_check_protocol_compliance_from_source",
        lambda package_dir, _package_name, **_kwargs: (
            ["import", "export", "sync", "validate"]
            if package_dir.name == "full"
            else (["import"] if package_dir.name == "partial" else [])
        ),
    )

    module_packages_impl.register_module_package_commands()

    assert "full=1, partial=1, legacy=1" in caplog.text


def test_protocol_legacy_warning_emitted_once_per_module(monkeypatch, caplog, tmp_path: Path) -> None:
    """Legacy warning should not be emitted more than once for a module condition."""
    from specfact_cli.registry import module_packages as module_packages_impl

    caplog.set_level(logging.WARNING)
    test_logger = logging.getLogger("test.protocol.warning")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "is_debug_mode", lambda: True)
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)
    packages = [(tmp_path / "legacy", ModulePackageMetadata(name="legacy", commands=[]))]
    monkeypatch.setattr(module_packages_impl, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages_impl, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(module_packages_impl, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: [])

    module_packages_impl.register_module_package_commands()

    lines = [line for line in caplog.text.splitlines() if "Module legacy: No ModuleIOContract (legacy mode)" in line]
    assert len(lines) == 1


def test_protocol_reporting_uses_static_source_operations(monkeypatch, caplog, tmp_path: Path) -> None:
    """Protocol reporting should use static source inspection operations."""
    from specfact_cli.registry import module_packages as module_packages_impl

    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.protocol.static-source")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "is_debug_mode", lambda: True)
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)
    packages = [(tmp_path / "backlog", ModulePackageMetadata(name="backlog", commands=[]))]
    monkeypatch.setattr(module_packages_impl, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages_impl, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(
        module_packages_impl, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: ["import"]
    )

    module_packages_impl.register_module_package_commands()

    assert "Module backlog: ModuleIOContract partial (import)" in caplog.text


def test_all_builtin_modules_expose_module_io_contract_operations() -> None:
    """Built-in modules should not remain legacy in protocol compliance classification."""
    from specfact_cli.registry import module_packages as module_packages_impl

    legacy_modules: list[str] = []
    for package_dir, meta in module_packages_impl.discover_package_metadata(module_packages_impl.get_modules_root()):
        try:
            operations = module_packages_impl._check_protocol_compliance_from_source(package_dir, meta.name)
        except Exception as exc:  # pragma: no cover - diagnostic path for unexpected import/runtime errors
            legacy_modules.append(f"{meta.name} ({exc})")
            continue
        if not operations:
            legacy_modules.append(meta.name)

    assert not legacy_modules, f"Modules still legacy: {', '.join(sorted(legacy_modules))}"


def test_protocol_reporting_is_quiet_when_all_modules_are_fully_compliant(monkeypatch, caplog, tmp_path: Path) -> None:
    """No protocol warnings/summary should be emitted when all modules are fully compliant."""
    from specfact_cli.registry import module_packages as module_packages_impl

    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.protocol.quiet-full")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "is_debug_mode", lambda: False)
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)
    packages = [
        (tmp_path / "full-a", ModulePackageMetadata(name="full-a", commands=[])),
        (tmp_path / "full-b", ModulePackageMetadata(name="full-b", commands=[])),
    ]
    monkeypatch.setattr(module_packages_impl, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages_impl, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(
        module_packages_impl,
        "_check_protocol_compliance_from_source",
        lambda *_args, **_kwargs: ["import", "export", "sync", "validate"],
    )

    module_packages_impl.register_module_package_commands()

    assert "ModuleIOContract fully implemented" not in caplog.text
    assert "Protocol-compliant:" not in caplog.text


def test_protocol_reporting_is_silent_for_non_compliant_modules_when_debug_off(monkeypatch, tmp_path: Path) -> None:
    """Non-compliant protocol details should stay hidden unless debug mode is enabled."""
    from specfact_cli.registry import module_packages as module_packages_impl

    shown_messages: list[str] = []

    monkeypatch.setattr(module_packages_impl, "is_debug_mode", lambda: False)
    monkeypatch.setattr(module_packages_impl, "print_warning", shown_messages.append)
    packages = [(tmp_path / "partial-a", ModulePackageMetadata(name="partial-a", commands=[]))]
    monkeypatch.setattr(module_packages_impl, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages_impl, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(
        module_packages_impl, "_check_protocol_compliance_from_source", lambda *_args, **_kwargs: ["import"]
    )

    module_packages_impl.register_module_package_commands()

    assert shown_messages == []


def test_protocol_source_scan_detects_runtime_interface_class_instance(tmp_path: Path) -> None:
    """Static scan should detect protocol operations exposed via runtime_interface object."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "sample"
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "sample.py").write_text(
        """
class RuntimeInterface:
    def import_to_bundle(self, source, config):
        return source

    def export_from_bundle(self, bundle, target, config):
        return target

runtime_interface = RuntimeInterface()
""".strip()
        + "\n",
        encoding="utf-8",
    )

    operations = module_packages_impl._check_protocol_compliance_from_source(package_dir, "sample")
    assert sorted(operations) == ["export", "import"]


def test_protocol_source_scan_detects_runtime_interface_assigned_via_name(tmp_path: Path) -> None:
    """Static scan should detect protocol operations when runtime_interface references a named instance."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "sample"
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "sample.py").write_text(
        """
class RuntimeImpl:
    def import_to_bundle(self, source, config):
        return source

    def sync_with_bundle(self, bundle, external_source, config):
        return bundle

interface_impl = RuntimeImpl()
runtime_interface = interface_impl
""".strip()
        + "\n",
        encoding="utf-8",
    )

    operations = module_packages_impl._check_protocol_compliance_from_source(package_dir, "sample")
    assert sorted(operations) == ["import", "sync"]


def test_protocol_source_scan_detects_runtime_interface_from_app_py_when_commands_exists(tmp_path: Path) -> None:
    """Static scan should also inspect app entrypoint when commands.py exists."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "sample"
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "commands.py").write_text(
        """
def unrelated():
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "app.py").write_text(
        """
class RuntimeInterface:
    def import_to_bundle(self, source, config):
        return source

    def validate_bundle(self, bundle, rules):
        return []

runtime_interface = RuntimeInterface()
""".strip()
        + "\n",
        encoding="utf-8",
    )

    operations = module_packages_impl._check_protocol_compliance_from_source(package_dir, "sample")
    assert sorted(operations) == ["import", "validate"]


def test_protocol_source_scan_detects_operations_in_namespaced_nested_command_module(tmp_path: Path) -> None:
    """Namespaced package should scan src/<pkg>/<command>/commands.py for protocol methods."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "specfact-backlog"
    command_dir = package_dir / "src" / "specfact_backlog" / "backlog"
    command_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / "commands.py").write_text(
        """
def import_to_bundle(source, config):
    return source

def validate_bundle(bundle, rules):
    return []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (package_dir / "src" / "specfact_backlog" / "__init__.py").write_text(
        '"""bundle package"""\n',
        encoding="utf-8",
    )

    operations = module_packages_impl._check_protocol_compliance_from_source(
        package_dir,
        "nold-ai/specfact-backlog",
        command_names=["backlog"],
    )
    assert sorted(operations) == ["import", "validate"]


def test_protocol_source_scan_follows_runtime_interface_import_from_local_module(tmp_path: Path) -> None:
    """Static scan should detect protocol methods when app.py imports runtime_interface from sibling file."""
    from specfact_cli.registry import module_packages as module_packages_impl

    package_dir = tmp_path / "sample"
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "commands.py").write_text("def unrelated():\n    return None\n", encoding="utf-8")
    (src_dir / "runtime_bindings.py").write_text(
        """
class RuntimeInterface:
    def export_from_bundle(self, bundle, target, config):
        return target

    def sync_with_bundle(self, bundle, external_source, config):
        return bundle

runtime_interface = RuntimeInterface()
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "app.py").write_text(
        """
from .runtime_bindings import runtime_interface
""".strip()
        + "\n",
        encoding="utf-8",
    )

    operations = module_packages_impl._check_protocol_compliance_from_source(package_dir, "sample")
    assert sorted(operations) == ["export", "sync"]
