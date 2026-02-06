"""Contract-first tests for shared bundle converter utilities."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.models.plan import Business, Feature, Idea, PlanBundle, Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.utils.bundle_converters import (
    convert_plan_bundle_to_project_bundle,
    convert_project_bundle_to_plan_bundle,
    is_constitution_minimal,
)


def _sample_feature() -> Feature:
    return Feature(key="FEATURE-001", title="Feature", outcomes=[], acceptance=[], constraints=[], stories=[])


def _sample_plan_bundle() -> PlanBundle:
    return PlanBundle(
        version="1.0",
        idea=Idea(title="Idea", narrative="Narrative"),
        business=Business(),
        product=Product(),
        features=[_sample_feature()],
        metadata=None,
        clarifications=None,
    )


def _sample_project_bundle() -> ProjectBundle:
    return ProjectBundle(
        manifest=BundleManifest(versions=BundleVersions(schema="1.0", project="0.1.0")),
        bundle_name="demo",
        idea=Idea(title="Idea", narrative="Narrative"),
        business=Business(),
        product=Product(),
        features={"FEATURE-001": _sample_feature()},
        clarifications=None,
    )


def test_convert_project_bundle_to_plan_bundle_roundtrip() -> None:
    plan = convert_project_bundle_to_plan_bundle(_sample_project_bundle())
    assert isinstance(plan, PlanBundle)
    assert len(plan.features) == 1
    assert plan.features[0].key == "FEATURE-001"


def test_convert_plan_bundle_to_project_bundle_roundtrip() -> None:
    project = convert_plan_bundle_to_project_bundle(_sample_plan_bundle(), "demo")
    assert isinstance(project, ProjectBundle)
    assert "FEATURE-001" in project.features
    assert project.bundle_name == "demo"


def test_is_constitution_minimal_for_missing_file() -> None:
    assert is_constitution_minimal(Path("/tmp/does-not-exist-constitution.md")) is True
