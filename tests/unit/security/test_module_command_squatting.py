"""Regression probes for workspace root-command squatting and core impersonation."""

import shutil
import sys
from collections.abc import Generator, Mapping, Sequence
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from specfact_cli.models.module_package import ModulePackageMetadata, SchemaExtension, ServiceBridgeMetadata
from specfact_cli.registry import CommandRegistry, module_packages as packages
from specfact_cli.registry.bridge_registry import BridgeRegistry
from specfact_cli.registry.extension_registry import ExtensionRegistry
from specfact_cli.registry.metadata import CommandMetadata


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None, None, None]:
    """Isolate real registries, active import roots and synthetic probe modules for each control."""
    CommandRegistry._clear_for_testing()
    yield
    packages._clear_active_module_src_dirs()
    CommandRegistry._clear_for_testing()


def _reset_registration() -> None:
    """Clear both registries and activated package import roots between boundary probes."""
    packages._clear_active_module_src_dirs()
    CommandRegistry._clear_for_testing()


def _workspace_package(tmp_path: Path, category: str | None, command: str) -> tuple[Path, ModulePackageMetadata]:
    """Create a clearly synthetic workspace package whose execution leaves an observable marker."""
    package_dir = tmp_path / ".specfact" / "modules" / "hostile"
    (package_dir / "src").mkdir(parents=True)
    category_line = f"category: {category}\n" if category else ""
    if category and category != "core":
        group = "code" if category == "codebase" else category
        category_line += f"bundle: specfact-{category}\nbundle_group_command: {group}\nbundle_sub_command: {command}\n"
    (package_dir / "module-package.yaml").write_text(
        f"name: hostile\nversion: '0.1.0'\ncommands: [{command}]\nsource: builtin\n{category_line}",
        encoding="utf-8",
    )
    marker = tmp_path / "executed"
    (package_dir / "src" / "app.py").write_text(
        "from pathlib import Path\nimport typer\n"
        f"Path({str(marker)!r}).write_text('executed')\napp = typer.Typer()\n"
        "@app.command()\ndef hostile_command(): pass\n",
        encoding="utf-8",
    )
    discovered = packages.discover_package_metadata(package_dir.parent, source="project")
    assert len(discovered) == 1
    assert discovered[0][1].source == "project", "Manifest source must not override discovery provenance"
    return discovered[0]


def _register_package(
    monkeypatch: pytest.MonkeyPatch,
    package: tuple[Path, ModulePackageMetadata],
    grouped: bool = True,
) -> None:
    """Exercise actual registration with explicit discovery and grouping inputs."""
    monkeypatch.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: [package])
    monkeypatch.setattr(packages, "read_modules_state", dict)
    packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)


def test_workspace_missing_category_cannot_squat_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reject grouped category-less workspace commands before registration or execution."""
    package = _workspace_package(tmp_path, None, "validate")
    _register_package(monkeypatch, package)
    assert "validate" not in CommandRegistry.list_commands()
    assert not (tmp_path / "executed").exists()


def test_workspace_core_category_cannot_extend_permanent_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reserve permanent command authority for real built-ins across both registration modes."""
    safe_app = typer.Typer()

    def safe_loader() -> typer.Typer:
        """Supply a harmless Typer app while observing admission independently from package execution."""
        return safe_app

    for category, grouped in (("core", True), ("core", False), (None, False)):
        with monkeypatch.context() as context:
            probe_root = tmp_path / f"{category}-{grouped}"
            package = _workspace_package(probe_root, category, "init")
            package[1].commands = list(packages.CORE_NAMES)
            for command in packages.CORE_NAMES:
                CommandRegistry.register(command, safe_loader, CommandMetadata(name=command, help="Safe core"))
            _register_package(context, package, grouped)
            for command in packages.CORE_NAMES:
                assert CommandRegistry.get_typer(command) is safe_app
            assert not CommandRegistry._module_entries
            assert not (probe_root / "executed").exists()
        _reset_registration()


def test_external_core_claim_rejected_even_with_forged_source_and_builtin_symlink(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Reject external resolved paths despite forged built-in labels or escaping symlinks."""
    for grouped in (True, False):
        with monkeypatch.context() as context:
            probe_root = tmp_path / str(grouped)
            package_dir, metadata = _workspace_package(probe_root, "core", "upgrade")
            metadata.source = "builtin"
            builtin_root = probe_root / "builtin"
            builtin_root.mkdir()
            symlink = builtin_root / "upgrade"
            symlink.symlink_to(package_dir, target_is_directory=True)

            def probe_builtin_root(root: Path = builtin_root) -> Path:
                """Observe built-in root lookup while verifying configured discovery authority."""
                return root.resolve()

            context.setattr(packages, "get_modules_root", probe_builtin_root)
            _register_package(context, (symlink, metadata), grouped)
            assert "upgrade" not in CommandRegistry.list_commands()
            assert not CommandRegistry._module_entries
            assert not (probe_root / "executed").exists()
        _reset_registration()


def test_explicit_legacy_workspace_registration_remains_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Keep explicit unreserved workspace legacy commands after grouped denial is proved."""
    package = _workspace_package(tmp_path, None, "legacy")
    _register_package(monkeypatch, package)
    assert "legacy" not in CommandRegistry.list_commands()
    assert not (tmp_path / "executed").exists()
    _reset_registration()
    _register_package(monkeypatch, package, grouped=False)
    assert "legacy" in CommandRegistry.list_commands()
    CommandRegistry.get_typer("legacy")
    assert (tmp_path / "executed").read_text() == "executed"


def test_non_workspace_legacy_registration_remains_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Preserve supported unreserved user, marketplace and custom legacy commands."""
    project = _workspace_package(tmp_path / "project", None, "legacy")
    _register_package(monkeypatch, project)
    assert "legacy" not in CommandRegistry.list_commands()
    _reset_registration()
    for source in ("user", "marketplace", "custom"):
        with monkeypatch.context() as context:
            package_dir, metadata = _workspace_package(tmp_path / source, None, "legacy")
            metadata.source = source
            _register_package(context, (package_dir, metadata))
            assert "legacy" in CommandRegistry.list_commands()
            assert isinstance(CommandRegistry.get_typer("legacy"), typer.Typer)
            assert (tmp_path / source / "executed").read_text() == "executed"
        _reset_registration()


def test_real_builtin_core_registration_remains_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Deny the external core claim while preserving loadable real built-in initialization."""
    hostile = _workspace_package(tmp_path, "core", "init")
    _register_package(monkeypatch, hostile)
    assert "init" not in CommandRegistry.list_commands()
    _reset_registration()
    discovered = packages.discover_package_metadata(packages.get_modules_root(), source="builtin")
    package = next(item for item in discovered if item[1].name == "init")
    _register_package(monkeypatch, package)
    assert "init" in CommandRegistry.list_commands()
    assert isinstance(CommandRegistry.get_typer("init"), typer.Typer)


def _assert_installed_category_root_unchanged(
    context: pytest.MonkeyPatch, package: tuple[Path, ModulePackageMetadata], grouped: bool
) -> None:
    """Observe exact installed root/module loader identities before and after a hostile claim."""
    package_dir, metadata = package
    command = metadata.commands[0]
    safe_app = typer.Typer()

    def sentinel_loader(app: typer.Typer = safe_app) -> typer.Typer:
        """Return the installed root app without running workspace code."""
        return app

    sentinel_metadata = CommandMetadata(name=command, help="Installed category sentinel")
    CommandRegistry.register(command, sentinel_loader, sentinel_metadata)
    CommandRegistry.register_module(command, sentinel_loader, sentinel_metadata)
    _register_package(context, (package_dir, metadata), grouped)
    for entries in (CommandRegistry._entries, CommandRegistry._module_entries):
        entry = next(entry for entry in entries if entry.get("name") == command)
        assert entry.get("loader") is sentinel_loader, "Workspace must not replace or wrap installed loaders"
        assert entry.get("metadata") is sentinel_metadata
    assert CommandRegistry.get_typer(command) is safe_app
    assert CommandRegistry.get_module_typer(command) is safe_app
    assert (package_dir / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
    assert not (package_dir.parents[2] / "executed").exists()


def test_workspace_cannot_supply_official_category_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reject every official workspace category-root claim before any registration side effect."""
    roots = (
        ("specfact-project", "project"),
        ("specfact-backlog", "backlog"),
        ("specfact-codebase", "code"),
        ("specfact-spec", "spec"),
        ("specfact-govern", "govern"),
        ("specfact-requirements", "requirements"),
    )
    for bundle, command in roots:
        category = bundle.removeprefix("specfact-")
        for declared_category, grouped in ((category, True), (category, False), (None, False)):
            with monkeypatch.context() as context:
                probe_root = tmp_path / command / f"{declared_category}-{grouped}"
                package_dir, metadata = _workspace_package(probe_root, declared_category, command)
                _assert_installed_category_root_unchanged(context, (package_dir, metadata), grouped)
                _reset_registration()
                _register_package(context, (package_dir, metadata), grouped)
                assert command not in CommandRegistry.list_commands()
                assert not CommandRegistry._module_entries
            _reset_registration()


def _configure_hostile_side_effects(
    monkeypatch: pytest.MonkeyPatch, package: tuple[Path, ModulePackageMetadata], marker: Path
) -> tuple[ExtensionRegistry, BridgeRegistry]:
    """Supply valid real schema/bridge declarations and isolated observable registries."""
    hostile, hostile_meta = package
    bridge_name = "specfact_squatting_bridge_probe"
    (hostile / "src" / f"{bridge_name}.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('hostile-bridge')\n"
        "class Converter:\n"
        "    def to_bundle(self, external_data): return dict(external_data)\n"
        "    def from_bundle(self, bundle_data): return dict(bundle_data)\n"
    )
    hostile_meta.schema_extensions = [SchemaExtension(target="Feature", field="workspace_probe", type_hint="str")]
    hostile_meta.service_bridges = [
        ServiceBridgeMetadata(id="workspace-probe", converter_class=f"{bridge_name}.Converter")
    ]
    extensions = ExtensionRegistry()
    bridges = BridgeRegistry()
    monkeypatch.setattr(packages, "get_extension_registry", lambda: extensions)
    monkeypatch.setattr(packages, "BRIDGE_REGISTRY", bridges)
    return extensions, bridges


def test_rejected_workspace_cannot_shadow_eligible_package_imports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Load the approved dependency without activating or executing rejected workspace sources."""
    hostile, hostile_meta = _workspace_package(tmp_path, None, "validate")
    marker = tmp_path / "shadow-executed"
    bridge_name = "specfact_squatting_bridge_probe"
    extensions, bridges = _configure_hostile_side_effects(monkeypatch, (hostile, hostile_meta), marker)
    before_extensions = extensions.list_all()
    before_bridges = bridges.as_mapping()
    dependency_name = "specfact_squatting_probe_dependency"
    (hostile / "src" / f"{dependency_name}.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('hostile')\nVALUE = 'hostile'\n"
    )
    trusted = tmp_path / ".specfact" / "modules" / "trusted"
    (trusted / "src").mkdir(parents=True)
    dependency_root = tmp_path / "approved-dependency"
    dependency_root.mkdir()
    (dependency_root / f"{dependency_name}.py").write_text("VALUE = 'approved'\n")
    monkeypatch.setattr(sys, "path", [str(dependency_root), *sys.path])
    (trusted / "src" / "app.py").write_text(
        f"import {dependency_name} as dependency\nimport typer\n"
        "assert dependency.VALUE == 'approved'\napp = typer.Typer()\n"
    )
    metadata = ModulePackageMetadata(name="trusted", version="0.1.0", commands=["trusted"], source="user")
    monkeypatch.setattr(
        packages, "discover_all_package_metadata", lambda **_kwargs: [(trusted, metadata), (hostile, hostile_meta)]
    )
    monkeypatch.setattr(packages, "read_modules_state", dict)
    try:
        packages.register_module_package_commands(allow_unsigned=True)
        assert extensions.list_all() == before_extensions, "Rejected metadata must not register schema extensions"
        assert bridges.as_mapping() == before_bridges, "Rejected metadata must not instantiate service bridges"
        assert isinstance(CommandRegistry.get_typer("trusted"), typer.Typer)
        assert not marker.exists()
        assert (hostile / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
    finally:
        sys.modules.pop(dependency_name, None)
        sys.modules.pop(bridge_name, None)


def test_explicit_repository_root_preserves_builtin_authority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Preserve contained built-in authority from an operator-configured checkout."""
    effective_root = tmp_path / "checkout" / "src" / "specfact_cli" / "modules"
    shutil.copytree(packages.get_modules_root() / "init", effective_root / "init")
    monkeypatch.setenv("SPECFACT_REPO_ROOT", str(tmp_path / "checkout"))
    assert packages.get_modules_root() == effective_root
    hostile_dir, hostile_meta = _workspace_package(tmp_path / "external", "core", "upgrade")
    hostile_meta.source = "builtin"
    escaped = effective_root / "upgrade"
    escaped.symlink_to(hostile_dir, target_is_directory=True)
    _register_package(monkeypatch, (escaped, hostile_meta))
    assert "upgrade" not in CommandRegistry.list_commands()
    _reset_registration()
    discovered = packages.discover_package_metadata(effective_root, source="builtin")
    _register_package(monkeypatch, next(item for item in discovered if item[1].name == "init"))
    assert "init" in CommandRegistry.list_commands()
    assert isinstance(CommandRegistry.get_typer("init"), typer.Typer)


def test_spec_api_routing_preserves_reserved_workspace_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reserve the legacy flat root and execute an eligible spec bundle through its api route."""
    hostile = _workspace_package(tmp_path / "workspace", None, "spec")
    _register_package(monkeypatch, hostile, grouped=False)
    assert "spec" not in CommandRegistry.list_commands()
    assert not (tmp_path / "workspace" / "executed").exists()
    _reset_registration()
    package_dir, metadata = _workspace_package(tmp_path / "eligible", "spec", "spec")
    metadata.source = "user"
    metadata.bundle_sub_command = "api"
    (package_dir / "src" / "app.py").write_text(
        "import typer\napp = typer.Typer()\napi = typer.Typer()\napp.add_typer(api, name='api')\n"
        "@api.command()\ndef validate(): typer.echo('safe-api-route')\n"
    )
    _register_package(monkeypatch, (package_dir, metadata), grouped=False)
    spec_app = CommandRegistry.get_typer("spec")
    result = CliRunner().invoke(spec_app, ["api", "validate"])
    assert result.exit_code == 0, result.output
    assert "safe-api-route" in result.output


@pytest.mark.parametrize(
    "command", ["init", "module", "upgrade", "project", "backlog", "code", "spec", "govern", "requirements"]
)
def test_reserved_flat_claim_is_denied(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command: str) -> None:
    """Each reserved flat name independently proves rejection in explicit legacy mode."""
    package_dir, metadata = _workspace_package(tmp_path, None, command)
    _register_package(monkeypatch, (package_dir, metadata), grouped=False)
    assert command not in CommandRegistry.list_commands()
    assert not CommandRegistry._module_entries
    assert (package_dir / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
    assert not (tmp_path / "executed").exists()


def test_workspace_eligibility_does_not_import_category_builders(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Admission checks must not initialize category apps for a rejected package."""
    import builtins

    original_import = builtins.__import__
    imported_groups: list[str] = []

    def observed_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> object:
        """Observe category-builder imports during the actual eligibility probe."""
        if name.startswith("specfact_cli.groups."):
            imported_groups.append(name)
        return original_import(name, globals, locals, fromlist, level)

    package_dir, metadata = _workspace_package(tmp_path, None, "project")
    monkeypatch.setattr(builtins, "__import__", observed_import)
    _register_package(monkeypatch, (package_dir, metadata))
    assert not imported_groups, "Rejected admission must not import category builders"
    assert "project" not in CommandRegistry.list_commands()
    assert not CommandRegistry._module_entries
    assert (package_dir / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
    assert not (tmp_path / "executed").exists()


@pytest.mark.parametrize("grouped", [True, False])
@pytest.mark.parametrize("existing_root", [False, True])
def test_workspace_bundle_member_cannot_induce_category_mount(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, grouped: bool, existing_root: bool
) -> None:
    """Deny actual bundle-driven mounts and harmless member execution before root replacement."""
    package = _workspace_package(tmp_path, "project", "plan")
    safe_app = typer.Typer()

    def safe_loader() -> typer.Typer:
        """Preserve the existing unextended root app as a separate compatibility sentinel."""
        return safe_app

    if existing_root:
        CommandRegistry.register("project", safe_loader, CommandMetadata(name="project", help="Safe project"))
    _register_package(monkeypatch, package, grouped)
    if "project" in CommandRegistry.list_commands():
        CommandRegistry.get_typer("project")
    assert not (tmp_path / "executed").exists(), "Unsigned member code executed through the induced project root"
    assert CommandRegistry.get_module_metadata("plan") is None
    assert not packages._ACTIVE_MODULE_SRC_DIRS
    if existing_root:
        assert CommandRegistry.get_typer("project") is safe_app
    else:
        assert "project" not in CommandRegistry.list_commands()


@pytest.mark.parametrize("grouped", [True, False])
def test_workspace_core_member_cannot_extend_existing_category(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, grouped: bool
) -> None:
    """Protect an actual category builder from cross-category injection into an existing member loader."""
    from specfact_cli.groups.project_group import build_app

    package = _workspace_package(tmp_path, "core", "plan")
    safe_app = typer.Typer()

    def safe_loader() -> typer.Typer:
        """Supply a legitimate member whose identity must survive hostile registration."""
        return safe_app

    CommandRegistry.register_module("plan", safe_loader, CommandMetadata(name="plan", help="Safe plan"))
    CommandRegistry.register("project", build_app, CommandMetadata(name="project", help="Safe project"))
    _register_package(monkeypatch, package, grouped)
    CommandRegistry.get_typer("project")
    assert not (tmp_path / "executed").exists(), "Cross-category member executed through the existing project root"
    assert CommandRegistry.get_module_typer("plan") is safe_app
    assert (package[0] / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS


@pytest.mark.parametrize("claim", ["bundle", "name"])
def test_workspace_legacy_alias_cannot_mount_category(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, claim: str
) -> None:
    """Reject explicit and namespaced bundle aliases even when legacy flat mounting is enabled."""
    package_dir, metadata = _workspace_package(tmp_path, None, "unreserved")
    if claim == "bundle":
        metadata.bundle = "specfact-project"
    else:
        metadata.name = "hostile/specfact-project"
    _register_package(monkeypatch, (package_dir, metadata), grouped=False)
    assert "project" not in CommandRegistry.list_commands(), "Unverified legacy alias induced a reserved root"
    assert not packages._ACTIVE_MODULE_SRC_DIRS
