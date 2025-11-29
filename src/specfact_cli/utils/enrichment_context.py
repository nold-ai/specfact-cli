"""
Context builder for LLM enrichment workflow.

Builds comprehensive context from CLI analysis results (relationships, contracts, schemas)
to provide rich context for LLM enrichment.
"""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import PlanBundle


class EnrichmentContext:
    """
    Context for LLM enrichment workflow.

    Contains all extracted metadata from CLI analysis:
    - Relationships (imports, dependencies, interfaces)
    - Contracts (OpenAPI schemas)
    - Bundle metadata (features, stories, source tracking)
    """

    @beartype
    def __init__(self) -> None:
        """Initialize empty enrichment context."""
        self.relationships: dict[str, Any] = {}
        self.contracts: dict[str, dict[str, Any]] = {}  # feature_key -> openapi_spec
        self.bundle_metadata: dict[str, Any] = {}

    @beartype
    @require(lambda relationships: isinstance(relationships, dict), "Relationships must be dict")
    def add_relationships(self, relationships: dict[str, Any]) -> None:
        """Add relationship data to context."""
        self.relationships = relationships

    @beartype
    @require(lambda feature_key: isinstance(feature_key, str), "Feature key must be string")
    @require(lambda contract: isinstance(contract, dict), "Contract must be dict")
    def add_contract(self, feature_key: str, contract: dict[str, Any]) -> None:
        """Add contract for a feature."""
        self.contracts[feature_key] = contract

    @beartype
    @require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
    def add_bundle_metadata(self, bundle: PlanBundle) -> None:
        """Add bundle metadata to context."""
        self.bundle_metadata = {
            "features_count": len(bundle.features),
            "stories_count": sum(len(f.stories) for f in bundle.features),
            "features": [
                {
                    "key": f.key,
                    "title": f.title,
                    "has_contract": f.contract is not None,
                    "has_source_tracking": f.source_tracking is not None,
                    "stories_count": len(f.stories),
                }
                for f in bundle.features
            ],
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def to_dict(self) -> dict[str, Any]:
        """
        Convert context to dictionary for LLM consumption.

        Returns:
            Dictionary with all context data
        """
        return {
            "relationships": self.relationships,
            "contracts": {
                key: {"paths_count": len(contract.get("paths", {})), "info": contract.get("info", {})}
                for key, contract in self.contracts.items()
            },
            "bundle_metadata": self.bundle_metadata,
            "graph_data": {
                "dependency_graph": self.relationships.get("dependency_graph", {}),
                "call_graphs_count": len(self.relationships.get("call_graphs", {})),
            },
        }

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def to_markdown(self) -> str:
        """
        Convert context to Markdown format for LLM prompt.

        Returns:
            Markdown-formatted context string
        """
        lines = ["# Enrichment Context", ""]

        # Bundle metadata
        lines.append("## Bundle Metadata")
        lines.append(f"- Features: {self.bundle_metadata.get('features_count', 0)}")
        lines.append(f"- Stories: {self.bundle_metadata.get('stories_count', 0)}")
        lines.append("")

        # Relationships
        if self.relationships:
            lines.append("## Relationships")
            if self.relationships.get("imports"):
                lines.append(f"- Files with imports: {len(self.relationships['imports'])}")
            if self.relationships.get("interfaces"):
                lines.append(f"- Interfaces found: {len(self.relationships['interfaces'])}")
            if self.relationships.get("routes"):
                total_routes = sum(len(routes) for routes in self.relationships["routes"].values())
                lines.append(f"- API routes found: {total_routes}")
            lines.append("")

        # Contracts
        if self.contracts:
            lines.append("## Contracts")
            for feature_key, contract in self.contracts.items():
                paths_count = len(contract.get("paths", {}))
                lines.append(f"- {feature_key}: {paths_count} API endpoint(s)")
            lines.append("")

        return "\n".join(lines)


def build_enrichment_context(
    plan_bundle: PlanBundle,
    relationships: dict[str, Any] | None = None,
    contracts: dict[str, dict[str, Any]] | None = None,
) -> EnrichmentContext:
    """
    Build enrichment context from analysis results.

    Args:
        plan_bundle: Plan bundle with features and stories
        relationships: Relationship data from RelationshipMapper
        contracts: Contract data (feature_key -> openapi_spec)

    Returns:
        EnrichmentContext instance
    """
    context = EnrichmentContext()
    context.add_bundle_metadata(plan_bundle)

    if relationships:
        context.add_relationships(relationships)

    if contracts:
        for feature_key, contract in contracts.items():
            context.add_contract(feature_key, contract)

    return context
