"""Shared helpers for creating default project bundles across modules."""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature, Product
from specfact_cli.models.project import BundleManifest, ProjectBundle


@require(
    lambda bundle_name: isinstance(bundle_name, str) and bundle_name.strip() != "", "bundle_name must be non-empty"
)
@ensure(lambda result: isinstance(result, ProjectBundle), "must return ProjectBundle")
@beartype
def create_empty_project_bundle(bundle_name: str) -> ProjectBundle:
    """Create a minimal ProjectBundle with default manifest and empty Product."""
    return ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name=bundle_name,
        product=Product(),
    )


@ensure(lambda result: isinstance(result, Feature), "must return Feature")
@beartype
def create_contract_anchor_feature() -> Feature:
    """Create a synthetic feature used when contracts exist but plan has no features."""
    return Feature(
        key="FEATURE-CONTRACTS",
        title="Generated Contracts",
        outcomes=[],
        acceptance=[],
        constraints=[],
        stories=[],
        confidence=1.0,
        draft=True,
        source_tracking=None,
        contract=None,
        protocol=None,
    )
