"""Shared bundle conversion helpers used across module commands."""

from __future__ import annotations

import re
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle


@require(lambda project_bundle: project_bundle is not None, "project_bundle must not be None")
@ensure(lambda result: result is not None, "Must return PlanBundle")
@beartype
def convert_project_bundle_to_plan_bundle(project_bundle: ProjectBundle) -> PlanBundle:
    """Convert ProjectBundle to PlanBundle for compatibility helpers."""
    return PlanBundle(
        version="1.0",
        idea=project_bundle.idea,
        business=project_bundle.business,
        product=project_bundle.product,
        features=list(project_bundle.features.values()),
        metadata=None,
        clarifications=project_bundle.clarifications,
    )


@require(lambda plan_bundle: plan_bundle is not None, "plan_bundle must not be None")
@require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "bundle_name must be non-empty")
@ensure(lambda result: result is not None, "Must return ProjectBundle")
@beartype
def convert_plan_bundle_to_project_bundle(plan_bundle: PlanBundle, bundle_name: str) -> ProjectBundle:
    """Convert PlanBundle to modular ProjectBundle format."""
    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )
    features_dict = {feature.key: feature for feature in plan_bundle.features}
    return ProjectBundle(
        manifest=manifest,
        bundle_name=bundle_name,
        idea=plan_bundle.idea,
        business=plan_bundle.business,
        product=plan_bundle.product,
        features=features_dict,
        clarifications=plan_bundle.clarifications,
    )


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_constitution_minimal(constitution_path: Path) -> bool:
    """Return True when constitution content is missing or effectively placeholder-only."""
    if not constitution_path.exists():
        return True
    try:
        content = constitution_path.read_text(encoding="utf-8").strip()
        if not content or content == "# Constitution" or len(content) < 100:
            return True
        placeholders = re.findall(r"\[[A-Z_0-9]+\]", content)
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        return bool(lines and len(placeholders) > len(lines) * 0.5)
    except Exception:
        return True
