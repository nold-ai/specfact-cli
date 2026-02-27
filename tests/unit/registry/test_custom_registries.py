"""Unit tests for custom registries (add, list, remove, fetch_all_indexes, trust)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

from specfact_cli.registry.custom_registries import (
    add_registry,
    fetch_all_indexes,
    get_registries_config_path,
    list_registries,
    remove_registry,
)


def test_get_registries_config_path_returns_specfact_config_path() -> None:
    """get_registries_config_path() returns path under ~/.specfact/config/registries.yaml."""
    path = get_registries_config_path()
    assert path.name == "registries.yaml"
    assert ".specfact" in path.parts
    assert "config" in path.parts


def test_add_registry_stores_config(tmp_path: Path) -> None:
    """add_registry() appends registry to registries.yaml with id, url, priority, trust."""
    with patch(
        "specfact_cli.registry.custom_registries.get_registries_config_path", return_value=tmp_path / "registries.yaml"
    ):
        add_registry("enterprise", "https://registry.company.com/index.json", priority=2, trust="prompt")
    assert (tmp_path / "registries.yaml").exists()
    data = yaml.safe_load((tmp_path / "registries.yaml").read_text())
    assert "registries" in data
    regs = data["registries"]
    assert len(regs) == 1
    assert regs[0]["id"] == "enterprise"
    assert regs[0]["url"] == "https://registry.company.com/index.json"
    assert regs[0]["priority"] == 2
    assert regs[0]["trust"] == "prompt"


def test_add_registry_assigns_next_priority_when_none(tmp_path: Path) -> None:
    """When priority is None, add_registry assigns next available priority."""
    config_path = tmp_path / "registries.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.dump(
            {"registries": [{"id": "first", "url": "https://a.com/index.json", "priority": 1, "trust": "always"}]}
        )
    )
    with patch("specfact_cli.registry.custom_registries.get_registries_config_path", return_value=config_path):
        add_registry("second", "https://b.com/index.json", priority=None, trust="prompt")
    data = yaml.safe_load(config_path.read_text())
    regs = {r["id"]: r for r in data["registries"]}
    assert regs["second"]["priority"] == 2


def test_list_registries_returns_all_configured(tmp_path: Path) -> None:
    """list_registries() returns list of registry dicts (official + custom from file)."""
    config_path = tmp_path / "registries.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.dump(
            {
                "registries": [
                    {"id": "official", "url": "https://official/index.json", "priority": 1, "trust": "always"},
                    {"id": "enterprise", "url": "https://enterprise/index.json", "priority": 2, "trust": "prompt"},
                ]
            }
        )
    )
    with patch("specfact_cli.registry.custom_registries.get_registries_config_path", return_value=config_path):
        result = list_registries()
    ids = [r["id"] for r in result]
    assert "official" in ids
    assert "enterprise" in ids
    by_id = {r["id"]: r for r in result}
    assert by_id["enterprise"]["url"] == "https://enterprise/index.json"
    assert by_id["enterprise"]["trust"] == "prompt"


def test_list_registries_includes_official_when_file_empty_or_missing() -> None:
    """list_registries() includes default official registry when config missing."""
    with patch("specfact_cli.registry.custom_registries.get_registries_config_path") as mock_path:
        mock_path.return_value = Path("/nonexistent/specfact/config/registries.yaml")
        result = list_registries()
    assert any(r.get("id") == "official" for r in result)


def test_remove_registry_deletes_from_config(tmp_path: Path) -> None:
    """remove_registry() removes registry by id from config."""
    config_path = tmp_path / "registries.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.dump(
            {
                "registries": [
                    {"id": "official", "url": "https://o/index.json", "priority": 1, "trust": "always"},
                    {"id": "enterprise", "url": "https://e/index.json", "priority": 2, "trust": "prompt"},
                ]
            }
        )
    )
    with patch("specfact_cli.registry.custom_registries.get_registries_config_path", return_value=config_path):
        remove_registry("enterprise")
    data = yaml.safe_load(config_path.read_text())
    ids = [r["id"] for r in data["registries"]]
    assert "enterprise" not in ids
    assert "official" in ids


def test_fetch_all_indexes_returns_list_of_indexes_by_priority() -> None:
    """fetch_all_indexes() fetches each registry URL and returns (registry_id, index) in priority order."""
    with patch("specfact_cli.registry.custom_registries.list_registries") as mock_list:
        mock_list.return_value = [
            {"id": "official", "url": "https://official/index.json", "priority": 1, "trust": "always"},
            {"id": "custom", "url": "https://custom/index.json", "priority": 2, "trust": "prompt"},
        ]
        with patch("specfact_cli.registry.custom_registries.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.side_effect = [
                {"modules": [{"id": "specfact/backlog"}]},
                {"modules": [{"id": "acme/backlog-pro"}]},
            ]
            mock_get.return_value.raise_for_status = lambda: None
            result = fetch_all_indexes()
    assert len(result) == 2
    assert result[0][0] == "official"
    assert result[0][1].get("modules") == [{"id": "specfact/backlog"}]
    assert result[1][0] == "custom"
    assert result[1][1].get("modules") == [{"id": "acme/backlog-pro"}]


def test_trust_level_enforcement_always_prompt_never() -> None:
    """Registry entries have trust one of always, prompt, never."""
    with (
        patch(
            "specfact_cli.registry.custom_registries.get_registries_config_path",
            return_value=Path("/tmp/registries.yaml"),
        ),
        patch("specfact_cli.registry.custom_registries.Path.exists", return_value=True),
        patch(
            "specfact_cli.registry.custom_registries.Path.read_text",
            return_value=yaml.dump(
                {
                    "registries": [
                        {"id": "a", "url": "https://a/index.json", "priority": 1, "trust": "always"},
                        {"id": "b", "url": "https://b/index.json", "priority": 2, "trust": "prompt"},
                        {"id": "c", "url": "https://c/index.json", "priority": 3, "trust": "never"},
                    ]
                }
            ),
        ),
    ):
        result = list_registries()
        trusts = {r["id"]: r["trust"] for r in result if r["id"] in ("a", "b", "c")}
        assert trusts.get("a") == "always"
        assert trusts.get("b") == "prompt"
        assert trusts.get("c") == "never"
