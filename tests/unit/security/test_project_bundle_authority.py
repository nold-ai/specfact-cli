"""Paired real-artifact compatibility and forgery controls for project bundle roots."""

import base64
import hashlib
import importlib.machinery
import importlib.util
import marshal
import os
import py_compile
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import typer
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specfact_cli.registry import CommandRegistry, module_installer, module_packages as packages
from specfact_cli.registry.bridge_registry import BridgeRegistry
from specfact_cli.registry.extension_registry import ExtensionRegistry
from tests.unit.security.test_module_command_squatting import (
    _register_package,
    _reset_registration,
    clean_registry as clean_registry,
)


BUNDLE_ROOTS = (
    ("specfact-project", "project"),
    ("specfact-backlog", "backlog"),
    ("specfact-codebase", "code"),
    ("specfact-code-review", "code"),
    ("specfact-spec", "spec"),
    ("specfact-govern", "govern"),
    ("specfact-requirements", "requirements"),
)


PROBE_APP = (
    "import typer\napp = typer.Typer()\nreview = typer.Typer()\n"
    "app.add_typer(review, name='review')\n"
    "@review.command()\ndef probe(): pass\nUNSIGNED_CACHE_PROBE = True\n"
)


@pytest.fixture(autouse=True)
def preserve_fixture_cache_authenticity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep pytest's rewritten caches out of signed fixtures; tests explicitly author genuine and forged caches."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)


def _official_project_packages(tmp_path: Path) -> list[tuple[Path, packages.ModulePackageMetadata]]:
    """Copy the immutable reviewed official artifacts into a real project discovery root."""
    configured_repository = os.environ.get("SPECFACT_MODULES_REPO")
    assert configured_repository, "Required signed companion fixture: configure SPECFACT_MODULES_REPO"
    source = Path(configured_repository) / "packages"
    project_modules = tmp_path / ".specfact" / "modules"
    for bundle, _command in BUNDLE_ROOTS:
        shutil.copytree(
            source / bundle, project_modules / bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
        )
    return packages.discover_package_metadata(project_modules, source="project")


def _add_unsigned_executable_probe(package_dir: Path, raw: dict[str, Any], forgery: str) -> None:
    """Construct harmless executable artifacts whose bytes are omitted by the signing filters."""
    source, _locations = packages._resolve_command_loader_path(package_dir, raw["name"], raw["commands"][0])
    if forgery == "cached-bytecode":
        target = Path(importlib.util.cache_from_source(str(source)))
        target.parent.mkdir(exist_ok=True)
        header = importlib.util.MAGIC_NUMBER + struct.pack(
            "<III", 0, int(source.stat().st_mtime), source.stat().st_size
        )
        probe_code = compile(PROBE_APP, str(source), "exec", dont_inherit=True, optimize=sys.flags.optimize)
        target.write_bytes(header + marshal.dumps(probe_code))
        observed = importlib.machinery.SourceFileLoader("unsigned_cache_probe", str(source)).get_code(
            "unsigned_cache_probe"
        )
        assert observed is not None and "UNSIGNED_CACHE_PROBE" in observed.co_names, (
            "The forged cache must really be loadable"
        )
    elif forgery == "standalone-bytecode":
        target = package_dir / "src" / "unsigned_cache_probe.pyc"
        header = importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, 0, 0)
        probe_code = compile(PROBE_APP, str(target), "exec", dont_inherit=True, optimize=sys.flags.optimize)
        target.write_bytes(header + marshal.dumps(probe_code))
        observed = importlib.machinery.SourcelessFileLoader("unsigned_cache_probe", str(target)).get_code(
            "unsigned_cache_probe"
        )
        assert observed is not None and "UNSIGNED_CACHE_PROBE" in observed.co_names
    elif forgery == "excluded-source":
        target = package_dir / "src" / "logs" / "unsigned_cache_probe.py"
        target.parent.mkdir(exist_ok=True)
        target.write_text("UNSIGNED_CACHE_PROBE = True\n", encoding="utf-8")


def _forged_project_package(
    tmp_path: Path, bundle: str, forgery: str, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, packages.ModulePackageMetadata]:
    """Create a separate hostile copy without modifying the reviewed fixture or user keys."""
    configured_repository = os.environ.get("SPECFACT_MODULES_REPO")
    assert configured_repository, "Required signed companion fixture: configure SPECFACT_MODULES_REPO"
    source = Path(configured_repository) / "packages" / bundle
    package_dir = tmp_path / ".specfact" / "modules" / bundle
    shutil.copytree(source, package_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    manifest = package_dir / "module-package.yaml"
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if forgery == "unsigned":
        raw.pop("integrity")
    elif forgery == "publisher":
        raw["publisher"]["name"] = "hostile"
    elif forgery == "signature":
        raw["integrity"]["signature"] = base64.b64encode(bytes(64)).decode("ascii")
    manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    _add_unsigned_executable_probe(package_dir, raw, forgery)
    if forgery == "directory-symlink":
        external = tmp_path / "external"
        external.mkdir()
        (external / "__init__.py").write_text("VALUE = 'hostile'\n", encoding="utf-8")
        (package_dir / "src" / "hostile_dependency").symlink_to(external, target_is_directory=True)
    if forgery == "git-untracked":
        subprocess.run(["git", "init", "--quiet", str(package_dir)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(package_dir), "add", "."], check=True, capture_output=True)
    if forgery in {"payload", "receipt", "workspace-key", "git-untracked"}:
        (package_dir / "src" / "hostile_probe.py").write_text("VALUE = 'tampered'\n", encoding="utf-8")
    if forgery in {"receipt", "workspace-key"}:
        payload = module_installer._module_artifact_payload_signed(package_dir)
        raw["integrity"]["checksum"] = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if forgery == "receipt":
            raw["integrity"].pop("signature")
            (package_dir / module_installer.INSTALL_VERIFIED_CHECKSUM_FILE).write_text(
                raw["integrity"]["checksum"], encoding="utf-8"
            )
        else:
            private_key = Ed25519PrivateKey.generate()
            raw["integrity"]["signature"] = base64.b64encode(private_key.sign(payload)).decode("ascii")
            public_key = private_key.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
            monkeypatch.setenv("SPECFACT_MODULE_PUBLIC_KEY_PEM", public_key.decode("ascii"))
        manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    discovered = packages.discover_package_metadata(package_dir.parent, source="project")
    assert len(discovered) == 1
    return discovered[0]


def _signature_backend_unavailable(*_args: object) -> None:
    """Simulate the real unavailable-verifier diagnostic without changing the admission decision."""
    raise ValueError("Signature verification backend unavailable")


def _assert_key_failures_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    official: list[tuple[Path, packages.ModulePackageMetadata]],
    command: str,
    grouped: bool,
) -> None:
    """Prove missing, empty, malformed and unavailable core-key verification fails closed."""
    trusted_key = module_installer._bundled_public_key_path().read_text(encoding="utf-8")
    key_paths = [tmp_path / "missing-key.pem", tmp_path / "empty-key.pem", tmp_path / "malformed-key.pem"]
    key_paths[1].write_text("", encoding="utf-8")
    key_paths[2].write_text("not a public key", encoding="utf-8")
    for key_path in key_paths:
        with monkeypatch.context() as context:
            context.setattr(module_installer, "_bundled_public_key_path", lambda path=key_path: path)
            context.setenv("SPECFACT_MODULE_PUBLIC_KEY_PEM", trusted_key)
            context.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: official)
            packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
            assert CommandRegistry.get_module_metadata(command) is None, "Invalid core key must fail closed"
            assert not packages._ACTIVE_MODULE_SRC_DIRS
        _reset_registration()
    with monkeypatch.context() as context:
        context.setattr(module_installer, "verify_signature", _signature_backend_unavailable)
        context.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: official)
        packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
        assert CommandRegistry.get_module_metadata(command) is None, "Unavailable verifier must fail closed"
        assert not packages._ACTIVE_MODULE_SRC_DIRS
    _reset_registration()


def _assert_official_artifact_provenance(official: list[tuple[Path, packages.ModulePackageMetadata]]) -> None:
    """Independently verify every compatibility fixture checksum and signature against the core key."""
    key = module_installer._bundled_public_key_path().read_text(encoding="utf-8")
    for package_dir, metadata in official:
        assert module_installer.verify_module_artifact(
            package_dir,
            metadata,
            allow_unsigned=False,
            require_integrity=True,
            require_signature=True,
            public_key_pem=key,
        ), "The compatibility artifact must genuinely verify against the core-bundled key"


def _assert_registered_bundle_surface(
    official: list[tuple[Path, packages.ModulePackageMetadata]], bundle: str, command: str
) -> None:
    """Observe the specific authenticated package surface, including the review add-on subgroup."""
    assert CommandRegistry.get_module_metadata(command) is not None, (
        "Verified project installation must retain its root"
    )
    package_dir = next(path for path, metadata in official if metadata.name == f"nold-ai/{bundle}")
    assert (package_dir / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS
    app = CommandRegistry.get_module_typer(command)
    assert isinstance(app, typer.Typer)
    if bundle == "specfact-code-review":
        assert any(group.name == "review" for group in app.registered_groups), "Verified add-on must expose code review"


def _assert_forged_bundle_has_no_surface(
    context: pytest.MonkeyPatch,
    forged: tuple[Path, packages.ModulePackageMetadata],
    grouped: bool,
    dependency: tuple[Path, packages.ModulePackageMetadata],
) -> None:
    """Reject the forged package while retaining the real codebase dependency for review extension probes."""
    package_dir, metadata = forged
    command = metadata.commands[0]
    if metadata.name == "nold-ai/specfact-code-review":
        context.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: [dependency, forged])
        context.setattr(packages, "read_modules_state", dict)
        packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
        app = CommandRegistry.get_module_typer("code")
        assert isinstance(app, typer.Typer)
        assert not any(group.name == "review" for group in app.registered_groups), (
            "Forged add-on must not extend codebase"
        )
        assert (dependency[0] / "src").resolve() in packages._ACTIVE_MODULE_SRC_DIRS
    else:
        _register_package(context, forged, grouped)
        assert CommandRegistry.get_module_metadata(command) is None, "Forged package must not supply a root"
        assert not CommandRegistry._module_entries
    assert (package_dir / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS


def _populate_current_interpreter_caches(
    official: list[tuple[Path, packages.ModulePackageMetadata]],
) -> None:
    """Create genuine caches independently before public repeated registration and app loading."""
    sources = [
        str(packages._resolve_command_loader_path(path, metadata.name, metadata.commands[0])[0])
        for path, metadata in official
    ]
    subprocess.run([sys.executable, "-m", "py_compile", *sources], check=True, capture_output=True)


@pytest.mark.parametrize(
    ("bundle", "command", "grouped"),
    [(bundle, command, grouped) for bundle, command in BUNDLE_ROOTS for grouped in (True, False)],
    ids=[
        f"{bundle.removeprefix('specfact-')}-{'grouped' if grouped else 'legacy'}"
        for bundle, _ in BUNDLE_ROOTS
        for grouped in (True, False)
    ],
)
def test_verified_project_bundle_preserves_root_and_rejects_forgery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bundle: str, command: str, grouped: bool
) -> None:
    """Keep the actual signed official root while rejecting every unverified replacement before effects."""
    official = _official_project_packages(tmp_path / "official")
    _assert_official_artifact_provenance(official)
    monkeypatch.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: official)
    monkeypatch.setattr(packages, "read_modules_state", dict)
    packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
    assert CommandRegistry.get_module_metadata(command) is not None, (
        "Verified project installation must retain its root"
    )
    _populate_current_interpreter_caches(official)
    _reset_registration()
    packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
    _assert_registered_bundle_surface(official, bundle, command)
    dependency = next(package for package in official if package[1].name == "nold-ai/specfact-codebase")
    _reset_registration()
    for forgery in (
        "unsigned",
        "payload",
        "publisher",
        "signature",
        "receipt",
        "workspace-key",
        "git-untracked",
        "directory-symlink",
        "cached-bytecode",
        "standalone-bytecode",
        "excluded-source",
    ):
        with monkeypatch.context() as context:
            forged = _forged_project_package(tmp_path / forgery, bundle, forgery, context)
            _assert_forged_bundle_has_no_surface(context, forged, grouped, dependency)
        _reset_registration()
    _assert_key_failures_are_rejected(monkeypatch, tmp_path, official, command, grouped)


def _prepare_source_snapshot_swap(monkeypatch: pytest.MonkeyPatch, source: Path) -> None:
    """Restore signed bytes after the compiler's first source read to reproduce snapshot separation."""
    signed = source.read_bytes()
    cache = Path(importlib.util.cache_from_source(str(source)))
    cache.parent.mkdir(exist_ok=True)
    header = importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(source.stat().st_mtime), len(signed))
    probe_code = compile(PROBE_APP, str(source), "exec", dont_inherit=True, optimize=sys.flags.optimize)
    cache.write_bytes(header + marshal.dumps(probe_code))
    source.write_bytes(PROBE_APP.encode())
    original_read = Path.read_bytes
    reads = {"source": 0}

    def swapped_read(path: Path) -> bytes:
        """Expose altered bytes once, then restore the original signed file for later reads."""
        data = original_read(path)
        if path == source:
            reads["source"] += 1
            if reads["source"] == 1:
                source.write_bytes(signed)
        return data

    monkeypatch.setattr(Path, "read_bytes", swapped_read)


def _assert_codebase_authority_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Pair a hostile-artifact probe with real authenticated project-root compatibility."""
    official = _official_project_packages(tmp_path)
    monkeypatch.setattr(packages, "discover_all_package_metadata", lambda **_kwargs: official)
    monkeypatch.setattr(packages, "read_modules_state", dict)
    packages.register_module_package_commands(allow_unsigned=True)
    assert CommandRegistry.get_module_metadata("code") is not None
    assert isinstance(CommandRegistry.get_module_typer("code"), typer.Typer)
    _reset_registration()


def test_signed_source_snapshot_cannot_be_replaced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Deny a valid-app cache when the source presented to compilation differs from signed bytes."""
    import py_compile

    _assert_codebase_authority_available(monkeypatch, tmp_path / "official")
    forged = _forged_project_package(tmp_path / "forged", "specfact-codebase", "unchanged", monkeypatch)
    source, _locations = packages._resolve_command_loader_path(forged[0], forged[1].name, "code")
    _prepare_source_snapshot_swap(monkeypatch, source)
    compiled: list[str] = []
    original_compile = py_compile.compile

    def observed_compiler(filename: str, *args: Any, **kwargs: Any) -> object:
        """Observe compiler work separately from the authority assertion."""
        compiled.append(filename)
        return original_compile(filename, *args, **kwargs)

    monkeypatch.setattr(py_compile, "compile", observed_compiler)
    _register_package(monkeypatch, forged)
    assert not compiled, "Unauthenticated source must be rejected before compiler work"
    assert not packages._ACTIVE_MODULE_SRC_DIRS
    assert CommandRegistry.get_module_metadata("code") is None, "The forged cache must not grant authority on retry"
    assert not packages._ACTIVE_MODULE_SRC_DIRS


@pytest.mark.parametrize("suffix", ["dll", "dylib", "bundle", "so", "pyd"])
def test_project_root_rejects_excluded_native_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, suffix: str
) -> None:
    """Reject omitted platform-library files without claiming to execute a native-load exploit."""
    _assert_codebase_authority_available(monkeypatch, tmp_path / "official")
    forged = _forged_project_package(tmp_path / "forged", "specfact-codebase", "unchanged", monkeypatch)
    target = forged[0] / "src" / "logs" / f"unsigned_probe.{suffix}"
    target.parent.mkdir()
    target.write_bytes(b"synthetic unsigned native-artifact boundary probe")
    _register_package(monkeypatch, forged)
    assert CommandRegistry.get_module_metadata("code") is None, "Excluded native artifact must not grant authority"
    assert not packages._ACTIVE_MODULE_SRC_DIRS


def _isolate_discovery_roots(monkeypatch: pytest.MonkeyPatch, workspace: Path, user_root: Path) -> None:
    """Exercise real source-priority discovery without reading operator module locations."""
    from specfact_cli.registry import module_discovery

    monkeypatch.chdir(workspace)
    monkeypatch.setattr(packages, "get_modules_root", lambda: workspace / "missing-builtin")
    monkeypatch.setattr(module_discovery, "USER_MODULES_ROOT", user_root)
    monkeypatch.setattr(module_discovery, "MARKETPLACE_MODULES_ROOT", workspace / "missing-marketplace")
    monkeypatch.setattr(module_discovery, "CUSTOM_MODULES_ROOT", workspace / "missing-custom")
    monkeypatch.delenv("SPECFACT_MODULES_ROOTS", raising=False)
    monkeypatch.setattr(packages, "read_modules_state", dict)


@pytest.mark.parametrize("grouped", [True, False], ids=["grouped", "legacy"])
def test_rejected_project_preserves_same_name_installed_bundle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, grouped: bool
) -> None:
    """Preserve the real installed root and add-on after actual discovery rejects a same-name workspace claim."""
    official = _official_project_packages(tmp_path / "user")
    installed = next(package for package in official if package[1].name == "nold-ai/specfact-codebase")
    forged = _forged_project_package(tmp_path / "workspace", "specfact-codebase", "unsigned", monkeypatch)
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", installed[0].parent)
    ordinary = packages.discover_all_package_metadata()
    assert len({meta.name for _path, meta in ordinary}) == len(ordinary)
    assert next(path for path, meta in ordinary if meta.name == installed[1].name) == forged[0]
    packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
    _assert_registered_bundle_surface(official, "specfact-codebase", "code")
    _assert_registered_bundle_surface(official, "specfact-code-review", "code")
    assert (forged[0] / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS
    _reset_registration()
    shutil.copyfile(
        Path(os.environ["SPECFACT_MODULES_REPO"]) / "packages/specfact-codebase/module-package.yaml",
        forged[0] / "module-package.yaml",
    )
    packages.register_module_package_commands(allow_unsigned=True, category_grouping_enabled=grouped)
    _assert_registered_bundle_surface([forged], "specfact-codebase", "code")
    assert (installed[0] / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS


@pytest.mark.parametrize("mode", ["state", "disable-override"])
def test_disabled_project_roots_skip_payload_verification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    """Skip disabled payload reads, preserve explicit re-enablement, and deny an enabled unsigned replacement."""
    package_dir, metadata = _forged_project_package(
        tmp_path / "workspace", "specfact-codebase", "unchanged", monkeypatch
    )
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", tmp_path / "missing-user")
    stored_enabled = mode != "state"
    monkeypatch.setattr(packages, "read_modules_state", lambda: {metadata.name: {"enabled": stored_enabled}})
    reads: list[Path] = []
    original_read = Path.read_bytes

    def observed_read(path: Path) -> bytes:
        """Observe real source payload IO without altering verifier decisions."""
        if path.suffix == ".py" and path.is_relative_to(package_dir):
            reads.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", observed_read)
    packages.register_module_package_commands(disable_ids=[metadata.name] if stored_enabled else [])
    assert not reads, "Disabled project names must not reach artifact payload reads"
    assert not packages._ACTIVE_MODULE_SRC_DIRS
    assert not CommandRegistry._module_entries
    packages.register_module_package_commands(enable_ids=[metadata.name])
    assert isinstance(CommandRegistry.get_module_typer("code"), typer.Typer)
    assert reads, "The authentic enabled counterpart must actually pass through verification"
    _reset_registration()
    manifest = package_dir / "module-package.yaml"
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    raw.pop("integrity")
    manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    packages.register_module_package_commands(enable_ids=[metadata.name], allow_unsigned=True)
    assert CommandRegistry.get_module_metadata("code") is None, "Enabled unsigned replacement must remain denied"
    assert not packages._ACTIVE_MODULE_SRC_DIRS


def _isolated_manifest_effect_registries(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ExtensionRegistry, BridgeRegistry, list[str]]:
    """Use real registries and a harmless ambient converter to observe forged declarations."""
    from types import ModuleType

    constructed: list[str] = []

    class Converter:
        """Harmless real converter whose constructor makes unsigned bridge activation observable."""

        def __init__(self) -> None:
            """Record instantiation without performing an external action."""
            constructed.append("manifest-bridge")

        def to_bundle(self, external_data: dict[str, Any]) -> dict[str, Any]:
            """Provide the required inbound converter behavior."""
            return dict(external_data)

        def from_bundle(self, bundle_data: dict[str, Any]) -> dict[str, Any]:
            """Provide the required outbound converter behavior."""
            return dict(bundle_data)

    ambient = ModuleType("specfact_manifest_binding_probe")
    ambient.__dict__["Converter"] = Converter
    monkeypatch.setitem(sys.modules, ambient.__name__, ambient)
    extensions, bridges = ExtensionRegistry(), BridgeRegistry()
    monkeypatch.setattr(packages, "get_extension_registry", lambda: extensions)
    monkeypatch.setattr(packages, "BRIDGE_REGISTRY", bridges)
    return extensions, bridges, constructed


def _restore_manifest_after_discovery_read(monkeypatch: pytest.MonkeyPatch, manifest: Path, field: str) -> None:
    """Present forged registration fields once, restoring authentic signed YAML before verification."""
    signed = manifest.read_text(encoding="utf-8")
    raw = yaml.safe_load(signed)
    additions = {
        "schema": ("schema_extensions", [{"target": "Feature", "field": "manifest_probe", "type_hint": "str"}]),
        "bridge": (
            "service_bridges",
            [{"id": "manifest-probe", "converter_class": "specfact_manifest_binding_probe.Converter"}],
        ),
        "commands": ("commands", [*raw["commands"], "manifest-probe"]),
        "version": ("version", "999.0.0"),
    }
    key, value = additions[field]
    raw[key] = value
    manifest.write_text(yaml.safe_dump(raw), encoding="utf-8")
    original_read = Path.read_text
    observed: list[Path] = []

    def swapped_manifest_read(path: Path, *args: Any, **kwargs: Any) -> str:
        """Restore signed bytes only after the real discovery parser has received forged text."""
        data = original_read(path, *args, **kwargs)
        if path == manifest and not observed:
            observed.append(path)
            manifest.write_text(signed, encoding="utf-8")
        return data

    monkeypatch.setattr(Path, "read_text", swapped_manifest_read)


@pytest.mark.parametrize("field", ["schema", "bridge", "commands", "version"])
def test_discovery_fields_match_signed_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, field: str) -> None:
    """Reject stale forged metadata while preserving fresh loading of the authentic restored artifact."""
    package = _forged_project_package(tmp_path / "workspace", "specfact-codebase", "unchanged", monkeypatch)
    _assert_official_artifact_provenance([package])
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", tmp_path / "missing-user")
    extensions, bridges, constructed = _isolated_manifest_effect_registries(monkeypatch)
    before_extensions, before_bridges = extensions.list_all(), bridges.as_mapping()
    with monkeypatch.context() as replacement:
        _restore_manifest_after_discovery_read(replacement, package[0] / "module-package.yaml", field)
        packages.register_module_package_commands(allow_unsigned=True)
        _assert_official_artifact_provenance([package])
        assert extensions.list_all() == before_extensions, (
            "Unsigned discovery schema must not gain authenticated authority"
        )
        assert bridges.as_mapping() == before_bridges, "Unsigned discovery bridge must not gain authenticated authority"
        assert not constructed, "An unsigned bridge declaration must not instantiate a converter"
        assert not CommandRegistry._module_entries, "Unsigned discovery fields must not register commands"
        assert not packages._ACTIVE_MODULE_SRC_DIRS
    _reset_registration()
    packages.register_module_package_commands(allow_unsigned=True)
    _assert_registered_bundle_surface([package], "specfact-codebase", "code")


def _observe_package_activation(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Record every genuine activation, including roots cleared by a subsequent lazy registration."""
    activated: list[Path] = []
    original_remember = packages._remember_active_module_src

    def observe_activation(path: Path) -> None:
        original_remember(path)
        activated.extend(packages._ACTIVE_MODULE_SRC_DIRS)

    monkeypatch.setattr(packages, "_remember_active_module_src", observe_activation)
    return activated


def _observe_live_artifact_mutation(monkeypatch: pytest.MonkeyPatch, target: Path) -> tuple[list[bool], list[Path]]:
    """Observe genuine verification and transient activation while changing the live artifact."""
    verified: list[bool] = []
    original_verify = module_installer.verify_signature
    activated = _observe_package_activation(monkeypatch)

    def change_after_real_signature(artifact: bytes | Path, signature: str, key: str) -> bool:
        """Preserve real cryptographic verification and mutate the artifact only after it succeeds."""
        result = original_verify(artifact, signature, key)
        if not verified:
            verified.append(result)
            target.write_text(PROBE_APP, encoding="utf-8")
        return result

    monkeypatch.setattr(module_installer, "verify_signature", change_after_real_signature)
    return verified, activated


@pytest.mark.parametrize("mutation", ["added-source", "changed-source"])
def test_live_executable_inventory_matches_verified_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    """Deny executable changes during real verification instead of treating hashable paths as authenticated."""
    package = _forged_project_package(tmp_path / "workspace", "specfact-codebase", "unchanged", monkeypatch)
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", tmp_path / "missing-user")
    _assert_official_artifact_provenance([package])
    source, _locations = packages._resolve_command_loader_path(package[0], package[1].name, "code")
    target = package[0] / "src" / "unsigned_inventory_probe.py" if mutation == "added-source" else source
    original = target.read_bytes() if target.exists() else None
    with monkeypatch.context() as mutation_context:
        verified, activated = _observe_live_artifact_mutation(mutation_context, target)
        packages.register_module_package_commands(allow_unsigned=True)
        assert verified == [True], "The original captured artifact must genuinely verify before mutation"
        assert not activated, "Unauthenticated live executables must never activate, even transiently"
        assert not packages._ACTIVE_MODULE_SRC_DIRS, "Unauthenticated live executables must not activate their package"
        assert not CommandRegistry._module_entries
    if original is None:
        target.unlink()
    else:
        target.write_bytes(original)
    _reset_registration()
    packages.register_module_package_commands(allow_unsigned=True)
    _assert_registered_bundle_surface([package], "specfact-codebase", "code")


def _assert_equivalent_static_mutation_denied(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str) -> None:
    """Pair the compiler interleaving with the same unauthenticated artifact present before admission."""
    forgery = "standalone-bytecode" if mutation == "added-bytecode" else "unchanged"
    forged = _forged_project_package(tmp_path, "specfact-codebase", forgery, monkeypatch)
    if mutation == "changed-source":
        source, _locations = packages._resolve_command_loader_path(forged[0], forged[1].name, "code")
        source.write_text(PROBE_APP, encoding="utf-8")
    with monkeypatch.context() as negative:
        _register_package(negative, forged)
        assert not packages._ACTIVE_MODULE_SRC_DIRS, "A static unsigned executable must not activate its package"
        assert not CommandRegistry._module_entries
    _reset_registration()


def _mutate_during_cache_compilation(monkeypatch: pytest.MonkeyPatch, target: Path) -> list[str]:
    """Run the real standard compiler before changing the candidate tree during its admission check."""
    compiled: list[str] = []
    original_compile = py_compile.compile

    def change_after_compilation(filename: str, *args: Any, **kwargs: Any) -> object:
        result = original_compile(filename, *args, **kwargs)
        if not compiled:
            compiled.append(filename)
            if target.suffix == ".pyc":
                target.write_bytes(Path(str(kwargs["cfile"])).read_bytes())
            else:
                target.write_text(PROBE_APP, encoding="utf-8")
        return result

    monkeypatch.setattr(py_compile, "compile", change_after_compilation)
    return compiled


@pytest.mark.parametrize("mutation", ["added-bytecode", "changed-source"])
def test_cache_compilation_finishes_before_admission_inventory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    """Reject mutations during real cache reproduction before any transient package activation."""
    _assert_equivalent_static_mutation_denied(monkeypatch, tmp_path / "static", mutation)
    package = _forged_project_package(tmp_path / "workspace", "specfact-codebase", "unchanged", monkeypatch)
    _isolate_discovery_roots(monkeypatch, tmp_path / "workspace", tmp_path / "missing-user")
    _assert_official_artifact_provenance([package])
    _populate_current_interpreter_caches([package])
    source, _locations = packages._resolve_command_loader_path(package[0], package[1].name, "code")
    target = package[0] / "src" / "unsigned_inventory_probe.pyc" if mutation == "added-bytecode" else source
    original = target.read_bytes() if target.exists() else None
    with monkeypatch.context() as mutation_context:
        activated = _observe_package_activation(mutation_context)
        compiled = _mutate_during_cache_compilation(mutation_context, target)
        packages.register_module_package_commands(allow_unsigned=True)
        assert compiled, "The genuine captured source must really undergo standard cache compilation"
        assert not activated, "A mutation during cache reproduction must never activate its package"
        assert not CommandRegistry._module_entries
    if original is None:
        target.unlink()
    else:
        target.write_bytes(original)
    _reset_registration()
    packages.register_module_package_commands(allow_unsigned=True)
    _assert_registered_bundle_surface([package], "specfact-codebase", "code")
