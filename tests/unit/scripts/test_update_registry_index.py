"""Unit tests for scripts/update-registry-index.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_script_module() -> object:
    """Load scripts/update-registry-index.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "update-registry-index.py"
    spec = importlib.util.spec_from_file_location("update_registry_index", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_upserts_new_module_entry(tmp_path: Path) -> None:
    """main() appends module entry when id is not yet present."""
    module = _load_script_module()
    index_path = tmp_path / "index.json"
    entry_path = tmp_path / "entry.yaml"
    index_path.write_text(json.dumps({"schema_version": "1.0.0", "modules": []}), encoding="utf-8")
    entry_path.write_text(
        "\n".join(
            [
                "id: nold-ai/backlog",
                "latest_version: 0.1.0",
                "download_url: https://example.com/backlog-0.1.0.tar.gz",
                "checksum_sha256: abc",
                "",
            ]
        ),
        encoding="utf-8",
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
    entry_path.write_text(
        "\n".join(
            [
                "id: nold-ai/backlog",
                "latest_version: 0.2.0",
                "download_url: https://example.com/backlog-0.2.0.tar.gz",
                "checksum_sha256: new",
                "",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = module.main(["--index-path", str(index_path), "--entry-fragment", str(entry_path)])

    assert exit_code == 0
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(payload["modules"]) == 1
    assert payload["modules"][0]["latest_version"] == "0.2.0"
    assert payload["modules"][0]["checksum_sha256"] == "new"
