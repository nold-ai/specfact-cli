"""Unit tests for BacklogGraphBuilder."""

from __future__ import annotations

import json
import sys
from pathlib import Path


# ruff: noqa: E402


def _add_backlog_core_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    module_src = repo_root / "modules" / "backlog-core" / "src"
    sys.path.insert(0, str(module_src))


_add_backlog_core_to_path()

from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import DependencyType, ItemType


def _load_fixture(name: str) -> dict[str, object]:
    fixture = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_builder_maps_ado_types_and_relationships() -> None:
    sample = _load_fixture("ado_sample_graph.json")
    builder = BacklogGraphBuilder(provider="ado", template_name="ado_scrum")

    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]

    assert graph.items["100"].effective_type() == ItemType.EPIC
    assert graph.items["101"].status == "in_progress"
    assert graph.dependencies[0].type == DependencyType.PARENT_CHILD


def test_builder_detects_cycle_and_transitive_closure() -> None:
    sample = _load_fixture("cycles_fixture.json")
    builder = BacklogGraphBuilder(provider="github", template_name="github_projects")

    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]

    assert "a" in graph.transitive_closure
    assert graph.cycles_detected


def test_builder_applies_custom_status_override() -> None:
    sample = _load_fixture("github_sample_graph.json")
    builder = BacklogGraphBuilder(
        provider="github",
        template_name="github_projects",
        custom_config={"status_mapping": {"in progress": "doing"}},
    )

    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]

    assert graph.items["2"].status == "doing"


def test_builder_marks_orphans_without_parents_or_inbound_dependencies() -> None:
    sample = _load_fixture("github_sample_graph.json")
    sample["relationships"] = []

    builder = BacklogGraphBuilder(provider="github", template_name="github_projects")
    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]

    assert sorted(graph.orphans) == ["1", "2"]


def test_builder_loads_backlog_config_from_spec_yaml(tmp_path: Path, monkeypatch) -> None:
    spec_dir = tmp_path / ".specfact"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.yaml").write_text(
        "backlog_config:\n  dependencies:\n    status_mapping:\n      todo: planned\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    sample = _load_fixture("github_sample_graph.json")
    builder = BacklogGraphBuilder(provider="github", template_name="github_projects")
    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]

    assert graph.items["1"].status == "planned"


def test_builder_custom_config_overrides_spec_and_metadata() -> None:
    sample = _load_fixture("github_sample_graph.json")
    builder = BacklogGraphBuilder(
        provider="github",
        template_name="github_projects",
        custom_config={
            "project_bundle_metadata": {
                "backlog_core": {
                    "backlog_config": {
                        "dependencies": {
                            "status_mapping": {"in progress": "meta-doing"},
                        }
                    }
                }
            },
            "status_mapping": {"in progress": "custom-doing"},
        },
    )

    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]
    assert graph.items["2"].status == "custom-doing"


def test_builder_reads_backlog_config_from_metadata_extensions() -> None:
    sample = _load_fixture("github_sample_graph.json")
    builder = BacklogGraphBuilder(
        provider="github",
        template_name="github_projects",
        custom_config={
            "project_bundle_metadata": {
                "extensions": {
                    "backlog_core": {
                        "backlog_config": {
                            "dependencies": {
                                "status_mapping": {"in progress": "extension-doing"},
                            }
                        }
                    }
                }
            }
        },
    )

    graph = builder.add_items(sample["items"]).add_dependencies(sample["relationships"]).build()  # type: ignore[index]
    assert graph.items["2"].status == "extension-doing"
