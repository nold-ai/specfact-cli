#!/usr/bin/env python3
"""Fail closed when core documentation drifts from official module ownership."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml
from beartype import beartype
from icontract import ensure, require


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATHS = (
    "README.md",
    "docs/getting-started/installation.md",
    "docs/module-system/marketplace.md",
    "docs/reference/commands.md",
    "docs/reference/module-categories.md",
    "docs/reference/directory-structure.md",
)
OWNERSHIP_PATHS = (
    "docs/architecture/overview.md",
    "docs/architecture/implementation-status.md",
)


@dataclass(frozen=True)
class OfficialModule:
    """Official module package identity and its public command roots."""

    package_id: str
    command_roots: tuple[str, ...]


def _require_modules_source(modules_root: Path) -> tuple[Path, Path]:
    """Return required source paths or explain the incomplete checkout."""
    packages_path = modules_root / "packages"
    registry_path = modules_root / "registry" / "index.json"
    if not packages_path.is_dir() or not registry_path.is_file():
        raise ValueError(f"Modules source must contain packages/ and registry/index.json: {modules_root}")
    return packages_path, registry_path


def _is_official_nold_module(data: Mapping[str, object]) -> bool:
    """Return whether a manifest or registry record belongs to the official publisher."""
    publisher = data.get("publisher")
    if not isinstance(publisher, Mapping):
        return False
    publisher_record = cast(Mapping[str, object], publisher)
    return data.get("tier") == "official" and publisher_record.get("name") == "nold-ai"


def _read_yaml_mapping(path: Path) -> dict[str, object]:
    """Read a manifest as a mapping or reject malformed official metadata."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid module manifest: {path}")
    return cast(dict[str, object], data)


def _official_manifest(path: Path) -> OfficialModule | None:
    """Return one official manifest entry, ignoring third-party package metadata."""
    data = _read_yaml_mapping(path)
    if not _is_official_nold_module(data):
        return None
    package_id = data.get("name")
    commands = data.get("commands")
    group_command = data.get("bundle_group_command")
    if (
        not isinstance(package_id, str)
        or not isinstance(commands, list)
        or not all(isinstance(item, str) for item in commands)
    ):
        raise ValueError(f"Invalid official module manifest: {path}")
    roots = (group_command,) if isinstance(group_command, str) and group_command else tuple(commands)
    return OfficialModule(package_id, roots)


def _manifest_inventory(packages_path: Path) -> dict[str, OfficialModule]:
    """Collect the source-authoritative official module records."""
    manifests: dict[str, OfficialModule] = {}
    for path in sorted(packages_path.glob("*/module-package.yaml")):
        module = _official_manifest(path)
        if module is None:
            continue
        if module.package_id in manifests:
            raise ValueError(f"Duplicate official module manifest: {module.package_id} ({path})")
        manifests[module.package_id] = module
    return manifests


def _registry_inventory(registry_path: Path) -> set[str]:
    """Collect official package IDs from the marketplace registry."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError(f"Invalid marketplace registry: {registry_path}")
    entries = cast(dict[str, object], registry).get("modules")
    if not isinstance(entries, list):
        raise ValueError(f"Invalid marketplace registry: {registry_path}")
    registry_ids: set[str] = set()
    for item in entries:
        if not isinstance(item, Mapping):
            continue
        record = cast(Mapping[str, object], item)
        package_id = record.get("id")
        if _is_official_nold_module(record) and isinstance(package_id, str):
            registry_ids.add(package_id)
    return registry_ids


@beartype
@require(lambda modules_root: modules_root is not None)
@ensure(lambda result: all(isinstance(package_id, str) for package_id in result))
def discover_official_modules(modules_root: Path) -> dict[str, OfficialModule]:
    """Load official packages from manifests and require registry agreement."""
    packages_path, registry_path = _require_modules_source(modules_root)
    manifests = _manifest_inventory(packages_path)
    registry_ids = _registry_inventory(registry_path)
    if not manifests:
        raise ValueError(f"No official module manifests found under {modules_root}")
    if set(manifests) != registry_ids:
        raise ValueError(
            "Official module manifests and marketplace registry disagree: "
            f"manifests={sorted(manifests)}, registry={sorted(registry_ids)}"
        )
    return manifests


def _catalogue_findings(core_root: Path, package_ids: list[str]) -> list[str]:
    """Return catalogue omissions for each official package."""
    findings: list[str] = []
    for relative_path in CATALOGUE_PATHS:
        content = (core_root / relative_path).read_text(encoding="utf-8")
        for package_id in package_ids:
            package_name = package_id.rsplit("/", maxsplit=1)[-1]
            has_explicit_id = package_id in content
            has_noncanonical_only = f"removed {package_name}" in content.lower()
            if not has_explicit_id and (package_name not in content or has_noncanonical_only):
                findings.append(f"{relative_path}: missing official package {package_id}")
    return findings


def _has_command_root(record: object, package_id: str, root: str) -> bool:
    """Return whether one generated command record has the expected ownership."""
    if not isinstance(record, Mapping):
        return False
    command_record = cast(Mapping[str, object], record)
    command = command_record.get("command")
    return (
        command_record.get("owner_package") == package_id
        and isinstance(command, str)
        and command.split()[1:2] == [root]
    )


def _command_inventory_findings(core_root: Path, inventory: dict[str, OfficialModule]) -> list[str]:
    """Return missing grouped roots from the generated command inventory."""
    generated_path = core_root / "docs/reference/commands.generated.json"
    generated = json.loads(generated_path.read_text(encoding="utf-8"))
    records = generated if isinstance(generated, list) else []
    findings: list[str] = []
    for package_id, module in sorted(inventory.items()):
        for root in module.command_roots:
            if not any(_has_command_root(record, package_id, root) for record in records):
                findings.append(f"{generated_path.relative_to(core_root)}: missing {package_id} command root {root}")
    return findings


def _ownership_conflicts(content: str, package_id: str, module: OfficialModule) -> list[str]:
    """Return conflicting ownership claims for one official module."""
    return [
        package_id
        for root in module.command_roots
        if f"specfact {root} ... are not canonical" in content or f"specfact {root} ... is not canonical" in content
    ]


def _ownership_findings(core_root: Path, inventory: dict[str, OfficialModule]) -> list[str]:
    """Return core ownership claims that contradict installed grouped commands."""
    findings: list[str] = []
    for relative_path in OWNERSHIP_PATHS:
        content = (core_root / relative_path).read_text(encoding="utf-8")
        if "https://modules.specfact.io/" not in content:
            findings.append(f"{relative_path}: missing canonical modules documentation handoff")
        for package_id, module in sorted(inventory.items()):
            for conflicting_package in _ownership_conflicts(content, package_id, module):
                findings.append(
                    f"{relative_path}: incorrectly rejects installed {conflicting_package} command ownership"
                )
    return findings


@beartype
@require(lambda core_root, modules_root: core_root is not None and modules_root is not None)
@ensure(lambda result: all(isinstance(finding, str) for finding in result))
def validate_documentation_accountability(core_root: Path, modules_root: Path) -> list[str]:
    """Return deterministic ownership and catalogue findings for the core docs."""
    inventory = discover_official_modules(modules_root)
    package_ids = sorted(inventory)
    return [
        *_catalogue_findings(core_root, package_ids),
        *_command_inventory_findings(core_root, inventory),
        *_ownership_findings(core_root, inventory),
    ]


def _resolve_modules_root(raw_path: str | None) -> Path:
    """Resolve the required modules checkout from explicit or documented paths."""
    candidates = [Path(raw_path).expanduser()] if raw_path else []
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(REPO_ROOT.parent / "specfact-cli-modules")
    if "specfact-cli-worktrees" in REPO_ROOT.parts:
        marker = REPO_ROOT.parts.index("specfact-cli-worktrees")
        candidates.append(Path(*REPO_ROOT.parts[:marker]) / "specfact-cli-modules")
    for candidate in candidates:
        if (candidate / "packages").is_dir() and (candidate / "registry/index.json").is_file():
            return candidate.resolve()
    raise ValueError(
        "Cannot resolve specfact-cli-modules. Set SPECFACT_MODULES_REPO or clone it beside this repository."
    )


@beartype
@ensure(lambda result: isinstance(result, int))
def main(argv: list[str] | None = None) -> int:
    """Run the fail-closed documentation-accountability contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules-repo", help="Path to the specfact-cli-modules checkout")
    args = parser.parse_args(argv)
    try:
        findings = validate_documentation_accountability(REPO_ROOT, _resolve_modules_root(args.modules_repo))
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        sys.stdout.write(f"documentation-accountability: {exc}\n")
        return 1
    if findings:
        sys.stdout.write("documentation-accountability: FAILED\n")
        sys.stdout.write("\n".join(f"- {finding}" for finding in findings) + "\n")
        return 1
    sys.stdout.write("documentation-accountability: OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
