"""Contract stub generator from SDD HOW sections.

Generates contract stubs (icontract decorators, beartype type checks, CrossHair harnesses)
from SDD manifest HOW sections, mapping to plan bundle stories/features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature, PlanBundle, Story
from specfact_cli.models.sdd import SDDHow, SDDManifest
from specfact_cli.utils.structure import SpecFactStructure


class ContractGenerator:
    """
    Generates contract stubs from SDD HOW sections.

    Creates icontract decorators, beartype type checks, and CrossHair harnesses
    based on SDD manifest invariants and contracts, mapped to plan bundle stories/features.
    """

    @beartype
    def __init__(self) -> None:
        """Initialize contract generator."""

    @beartype
    @require(lambda sdd: isinstance(sdd, SDDManifest), "SDD must be SDDManifest instance")
    @require(lambda plan: isinstance(plan, PlanBundle), "Plan must be PlanBundle instance")
    @require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
    @require(
        lambda contracts_dir: contracts_dir is None or isinstance(contracts_dir, Path),
        "Contracts dir must be None or Path",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def generate_contracts(
        self, sdd: SDDManifest, plan: PlanBundle, base_path: Path | None = None, contracts_dir: Path | None = None
    ) -> dict[str, Any]:
        """
        Generate contract stubs from SDD HOW sections.

        Args:
            sdd: SDD manifest with HOW section containing invariants and contracts
            plan: Plan bundle to map contracts to stories/features
            base_path: Base directory for output (default: current directory)
            contracts_dir: Specific contracts directory (default: .specfact/contracts/ or bundle-specific if provided)

        Returns:
            Dictionary with generation results:
            - generated_files: List of generated file paths
            - contracts_per_story: Dict mapping story keys to contract counts
            - invariants_per_feature: Dict mapping feature keys to invariant counts
            - errors: List of error messages (if any)
        """
        if base_path is None:
            base_path = Path(".")

        # Determine contracts directory: use provided one, or default to global .specfact/contracts/
        if contracts_dir is None:
            contracts_dir = base_path / SpecFactStructure.ROOT / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        generated_files: list[Path] = []
        contracts_per_story: dict[str, int] = {}
        invariants_per_feature: dict[str, int] = {}
        errors: list[str] = []

        # Map SDD contracts to plan stories/features
        # For now, we'll generate one contract file per feature
        # with contracts mapped to stories within that feature
        for feature in plan.features:
            try:
                # Extract contracts and invariants for this feature
                feature_contracts = self._extract_feature_contracts(sdd.how, feature)
                feature_invariants = self._extract_feature_invariants(sdd.how, feature)

                if feature_contracts or feature_invariants:
                    # Generate contract stub file for this feature
                    contract_file = self._generate_feature_contract_file(
                        feature, feature_contracts, feature_invariants, sdd, contracts_dir
                    )
                    generated_files.append(contract_file)

                    # Count contracts per story
                    for story in feature.stories:
                        story_contracts = self._extract_story_contracts(feature_contracts, story)
                        contracts_per_story[story.key] = len(story_contracts)

                    # Count invariants per feature
                    invariants_per_feature[feature.key] = len(feature_invariants)

            except Exception as e:
                errors.append(f"Error generating contracts for {feature.key}: {e}")

        # Fallback: if SDD has contracts/invariants but no feature-specific files were generated,
        # create a generic bundle-level stub so users still get actionable output.
        # Also handle case where plan has no features but SDD has contracts/invariants
        # IMPORTANT: Always generate at least one file if SDD has contracts/invariants
        has_contracts = bool(sdd.how.contracts)
        has_invariants = bool(sdd.how.invariants)
        has_contracts_or_invariants = has_contracts or has_invariants

        if not generated_files and has_contracts_or_invariants:
            generic_file = contracts_dir / "bundle_contracts.py"
            # Ensure directory exists
            generic_file.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                '"""Contract stubs generated from SDD HOW section (bundle-level fallback)."""',
                "from beartype import beartype",
                "from icontract import ensure, invariant, require",
                "",
                "# TODO: Map these contracts/invariants to specific features and stories",
            ]
            if has_contracts:
                for idx, contract in enumerate(sdd.how.contracts, 1):
                    lines.append(f"# Contract {idx}: {contract}")
            if has_invariants:
                for idx, invariant in enumerate(sdd.how.invariants, 1):
                    lines.append(f"# Invariant {idx}: {invariant}")
            lines.append("")
            generic_file.write_text("\n".join(lines), encoding="utf-8")
            generated_files.append(generic_file)

        return {
            "generated_files": [str(f) for f in generated_files],
            "contracts_per_story": contracts_per_story,
            "invariants_per_feature": invariants_per_feature,
            "errors": errors,
        }

    @beartype
    @require(lambda how: isinstance(how, SDDHow), "HOW must be SDDHow instance")
    @require(lambda feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_feature_contracts(self, how: SDDHow, feature: Feature) -> list[str]:
        """
        Extract contracts relevant to a feature from SDD HOW section.

        Args:
            how: SDD HOW section with contracts
            feature: Feature to extract contracts for

        Returns:
            List of contract strings relevant to this feature
        """
        # Simple heuristic: if contract mentions feature key or title, it's relevant
        # In the future, this could be more sophisticated (e.g., semantic matching)
        feature_contracts: list[str] = []
        feature_keywords = [feature.key.lower(), feature.title.lower()]

        for contract in how.contracts:
            contract_lower = contract.lower()
            if any(keyword in contract_lower for keyword in feature_keywords):
                feature_contracts.append(contract)

        # If no specific contracts found, use all contracts (they may apply globally)
        if not feature_contracts and how.contracts:
            feature_contracts = how.contracts

        return feature_contracts

    @beartype
    @require(lambda how: isinstance(how, SDDHow), "HOW must be SDDHow instance")
    @require(lambda feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_feature_invariants(self, how: SDDHow, feature: Feature) -> list[str]:
        """
        Extract invariants relevant to a feature from SDD HOW section.

        Args:
            how: SDD HOW section with invariants
            feature: Feature to extract invariants for

        Returns:
            List of invariant strings relevant to this feature
        """
        # Simple heuristic: if invariant mentions feature key or title, it's relevant
        feature_invariants: list[str] = []
        feature_keywords = [feature.key.lower(), feature.title.lower()]

        for invariant in how.invariants:
            invariant_lower = invariant.lower()
            if any(keyword in invariant_lower for keyword in feature_keywords):
                feature_invariants.append(invariant)

        # If no specific invariants found, use all invariants (they may apply globally)
        if not feature_invariants and how.invariants:
            feature_invariants = how.invariants

        return feature_invariants

    @beartype
    @require(lambda contracts: isinstance(contracts, list), "Contracts must be list")
    @require(lambda story: isinstance(story, Story), "Story must be Story instance")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_story_contracts(self, contracts: list[str], story: Story) -> list[str]:
        """
        Extract contracts relevant to a story from feature contracts.

        Args:
            contracts: List of contract strings
            story: Story to extract contracts for

        Returns:
            List of contract strings relevant to this story
        """
        # Simple heuristic: if contract mentions story key or title, it's relevant
        story_contracts: list[str] = []
        story_keywords = [story.key.lower(), story.title.lower()]

        for contract in contracts:
            contract_lower = contract.lower()
            if any(keyword in contract_lower for keyword in story_keywords):
                story_contracts.append(contract)

        return story_contracts

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @require(lambda contracts: isinstance(contracts, list), "Contracts must be list")
    @require(lambda invariants: isinstance(invariants, list), "Invariants must be list")
    @require(lambda sdd: isinstance(sdd, SDDManifest), "SDD must be SDDManifest instance")
    @require(lambda output_dir: isinstance(output_dir, Path), "Output dir must be Path")
    @ensure(lambda result: isinstance(result, Path) and result.exists(), "Output file must exist")
    def _generate_feature_contract_file(
        self,
        feature: Feature,
        contracts: list[str],
        invariants: list[str],
        sdd: SDDManifest,
        output_dir: Path,
    ) -> Path:
        """
        Generate contract stub file for a feature.

        Args:
            feature: Feature to generate contracts for
            contracts: List of contract strings
            invariants: List of invariant strings
            sdd: SDD manifest (for metadata)
            output_dir: Directory to write contract file

        Returns:
            Path to generated contract file
        """
        # Generate filename from feature key
        feature_slug = feature.key.lower().replace("feature-", "").replace("-", "_")
        contract_file = output_dir / f"{feature_slug}_contracts.py"

        # Generate contract stub content
        content = self._generate_contract_content(feature, contracts, invariants, sdd)

        # Write to file
        contract_file.write_text(content, encoding="utf-8")

        return contract_file

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @require(lambda contracts: isinstance(contracts, list), "Contracts must be list")
    @require(lambda invariants: isinstance(invariants, list), "Invariants must be list")
    @require(lambda sdd: isinstance(sdd, SDDManifest), "SDD must be SDDManifest instance")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty string")
    def _generate_contract_content(
        self,
        feature: Feature,
        contracts: list[str],
        invariants: list[str],
        sdd: SDDManifest,
    ) -> str:
        """
        Generate Python contract stub content.

        Args:
            feature: Feature to generate contracts for
            contracts: List of contract strings
            invariants: List of invariant strings
            sdd: SDD manifest (for metadata)

        Returns:
            Python code string with contract stubs
        """
        lines: list[str] = []
        lines.append('"""Contract stubs generated from SDD HOW section.')
        lines.append("")
        lines.append(f"Feature: {feature.key} ({feature.title})")
        lines.append(f"SDD Version: {sdd.version}")
        lines.append(f"Plan Bundle ID: {sdd.plan_bundle_id}")
        lines.append('"""')
        lines.append("")
        lines.append("from __future__ import annotations")
        lines.append("")
        lines.append("from beartype import beartype")
        lines.append("from icontract import ensure, invariant, require")
        lines.append("")

        # Add invariants as class-level invariants or module-level checks
        if invariants:
            lines.append("# System Invariants")
            for i, invariant in enumerate(invariants, 1):
                lines.append(f"# Invariant {i}: {invariant}")
            lines.append("")

        # Add contracts as function decorator templates
        if contracts:
            lines.append("# Contract Templates")
            lines.append("# TODO: Map these contracts to actual functions in your codebase")
            lines.append("")
            for i, contract in enumerate(contracts, 1):
                lines.append(f"# Contract {i}: {contract}")
                lines.append("# Example usage:")
                lines.append("# @require(lambda param: condition, 'Contract description')")
                lines.append("# @ensure(lambda result: condition, 'Postcondition description')")
                lines.append("# @beartype")
                lines.append("# def function_name(param: type) -> return_type:")
                lines.append("#     ...")
                lines.append("")

        # Add CrossHair harness template
        if contracts or invariants:
            lines.append("# CrossHair Property Testing Harness")
            lines.append("# TODO: Implement property tests based on contracts and invariants")
            lines.append("")
            lines.append("# Example:")
            lines.append("# from crosshair import register_type, SymbolicValue")
            lines.append("#")
            lines.append("# def test_feature_contracts():")
            lines.append("#     # Add property tests here")
            lines.append("#     pass")
            lines.append("")

        # Add metadata
        lines.append("# Metadata")
        lines.append(f"SDD_PLAN_BUNDLE_ID = '{sdd.plan_bundle_id}'")
        lines.append(f"SDD_PLAN_BUNDLE_HASH = '{sdd.plan_bundle_hash}'")
        lines.append(f"FEATURE_KEY = '{feature.key}'")
        lines.append(f"SDD_VERSION = '{sdd.version}'")
        lines.append("")

        return "\n".join(lines)
