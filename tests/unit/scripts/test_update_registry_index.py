"""Unit tests for scripts/update-registry-index.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Protocol, cast

import pytest


class UpdateRegistryIndexModule(Protocol):
    """Protocol for the dynamically loaded update-registry-index script."""

    def main(self, argv: list[str]) -> int:
        """Run the script entry point."""
        ...


def _load_script_module() -> UpdateRegistryIndexModule:
    """Load scripts/update-registry-index.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "update-registry-index.py"
    spec = importlib.util.spec_from_file_location("update_registry_index", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(UpdateRegistryIndexModule, module)


def _write_entry_fragment(entry_path: Path, module_id: str, version: str, download_url: str, checksum: str) -> None:
    """Write a minimal registry entry fragment for updater tests."""
    entry_path.write_text(
        "\n".join(
            [
                f"id: {module_id}",
                f"latest_version: {version}",
                f"download_url: {download_url}",
                f"checksum_sha256: {checksum}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_main_upserts_new_module_entry(tmp_path: Path) -> None:
    """main() appends module entry when id is not yet present."""
    module = _load_script_module()
    index_path = tmp_path / "index.json"
    entry_path = tmp_path / "entry.yaml"
    index_path.write_text(json.dumps({"schema_version": "1.0.0", "modules": []}), encoding="utf-8")
    _write_entry_fragment(
        entry_path,
        "nold-ai/backlog",
        "0.1.0",
        "https://example.com/backlog-0.1.0.tar.gz",
        "abc",
    )

    exit_code = module.main(["--index-path", str(index_path), "--entry-fragment", str(entry_path)])

    assert exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["modules"][0]["id"] == "nold-ai/backlog"
    assert payload["modules"][0]["latest_version"] == "0.1.0"


def test_main_updates_existing_entry_in_place(tmp_path: Path) -> None:
    """main() updates an existing module entry by id and keeps only one entry per id."""
    module = _load_script_module()
    index_path = tmp_path / "index.json"
    entry_path = tmp_path / "entry.yaml"
    index_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "modules": [
                    {
                        "id": "nold-ai/backlog",
                        "latest_version": "0.1.0",
                        "download_url": "https://example.com/backlog-0.1.0.tar.gz",
                        "checksum_sha256": "old",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_entry_fragment(
        entry_path,
        "nold-ai/backlog",
        "0.2.0",
        "https://example.com/backlog-0.2.0.tar.gz",
        "new",
    )

    exit_code = module.main(["--index-path", str(index_path), "--entry-fragment", str(entry_path)])

    assert exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(payload["modules"]) == 1
    assert payload["modules"][0]["latest_version"] == "0.2.0"
    assert payload["modules"][0]["checksum_sha256"] == "new"


@pytest.mark.parametrize(
    "download_url",
    [
        "https://github.com/nold-ai/specfact-cli-modules/releases/download/upgrade-0.1.20.tar.gz",
        "https://example.com/releases/download/upgrade-0.1.20.tar.gz",
    ],
)
def test_main_rejects_core_module_entry_from_unexpected_repository(tmp_path: Path, download_url: str) -> None:
    """Core bundled module entries must positively target the core repository."""
    module = _load_script_module()
    index_path = tmp_path / "index.json"
    entry_path = tmp_path / "entry.yaml"
    index_payload = {"schema_version": "1.0.0", "modules": []}
    index_path.write_text(json.dumps(index_payload), encoding="utf-8")
    _write_entry_fragment(
        entry_path,
        "upgrade",
        "0.1.20",
        download_url,
        "abc",
    )

    exit_code = module.main(["--index-path", str(index_path), "--entry-fragment", str(entry_path)])

    assert exit_code == 1
    assert json.loads(index_path.read_text(encoding="utf-8")) == index_payload
