"""
Ambiguity scanner for plan bundle review.

This module analyzes plan bundles to identify ambiguities, missing information,
and unknowns using a structured taxonomy.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import PlanBundle


class AmbiguityStatus(str, Enum):
    """Ambiguity status levels."""

    CLEAR = "Clear"
    PARTIAL = "Partial"
    MISSING = "Missing"


class TaxonomyCategory(str, Enum):
    """Taxonomy categories for ambiguity detection."""

    FUNCTIONAL_SCOPE = "Functional Scope & Behavior"
    DATA_MODEL = "Domain & Data Model"
    INTERACTION_UX = "Interaction & UX Flow"
    NON_FUNCTIONAL = "Non-Functional Quality Attributes"
    INTEGRATION = "Integration & External Dependencies"
    EDGE_CASES = "Edge Cases & Failure Handling"
    CONSTRAINTS = "Constraints & Tradeoffs"
    TERMINOLOGY = "Terminology & Consistency"
    COMPLETION_SIGNALS = "Completion Signals"
    FEATURE_COMPLETENESS = "Feature/Story Completeness"


@dataclass
class AmbiguityFinding:
    """Single ambiguity finding."""

    category: TaxonomyCategory
    status: AmbiguityStatus
    description: str
    impact: float = 0.5
    uncertainty: float = 0.5
    question: str | None = None
    related_sections: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate and initialize defaults."""
        if self.related_sections is None:
            self.related_sections = []
        if not 0.0 <= self.impact <= 1.0:
            raise ValueError(f"Impact must be 0.0-1.0, got {self.impact}")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError(f"Uncertainty must be 0.0-1.0, got {self.uncertainty}")


@dataclass
class AmbiguityReport:
    """Complete ambiguity analysis report."""

    findings: list[AmbiguityFinding] | None = None
    coverage: dict[TaxonomyCategory, AmbiguityStatus] | None = None
    priority_score: float = 0.0

    def __post_init__(self) -> None:
        """Validate and initialize defaults."""
        if self.findings is None:
            self.findings = []
        if self.coverage is None:
            self.coverage = {}
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError(f"Priority score must be 0.0-1.0, got {self.priority_score}")


class AmbiguityScanner:
    """
    Scanner for identifying ambiguities in plan bundles.

    Uses structured taxonomy to detect missing information, unclear requirements,
    and unknowns that should be resolved before promotion.
    """

    def __init__(self, repo_path: Path | None = None) -> None:
        """
        Initialize ambiguity scanner.

        Args:
            repo_path: Optional repository path for code-based auto-extraction
        """
        self.repo_path = repo_path

    @beartype
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
    @ensure(lambda result: isinstance(result, AmbiguityReport), "Must return AmbiguityReport")
    def scan(self, plan_bundle: PlanBundle) -> AmbiguityReport:
        """
        Scan plan bundle for ambiguities.

        Args:
            plan_bundle: Plan bundle to analyze

        Returns:
            Ambiguity report with findings and coverage
        """
        findings: list[AmbiguityFinding] = []
        coverage: dict[TaxonomyCategory, AmbiguityStatus] = {}

        # Scan each taxonomy category
        for category in TaxonomyCategory:
            category_findings = self._scan_category(plan_bundle, category)
            findings.extend(category_findings)

            # Determine category status
            if not category_findings:
                coverage[category] = AmbiguityStatus.CLEAR
            elif any(f.status == AmbiguityStatus.MISSING for f in category_findings):
                coverage[category] = AmbiguityStatus.MISSING
            else:
                coverage[category] = AmbiguityStatus.PARTIAL

        # Calculate priority score (highest impact x uncertainty)
        priority_score = 0.0
        if findings:
            priority_score = max(f.impact * f.uncertainty for f in findings)

        return AmbiguityReport(findings=findings, coverage=coverage, priority_score=priority_score)

    @beartype
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
    @require(lambda category: isinstance(category, TaxonomyCategory), "Category must be TaxonomyCategory")
    @ensure(lambda result: isinstance(result, list), "Must return list of findings")
    def _scan_category(self, plan_bundle: PlanBundle, category: TaxonomyCategory) -> list[AmbiguityFinding]:
        """Scan specific taxonomy category."""
        findings: list[AmbiguityFinding] = []

        if category == TaxonomyCategory.FUNCTIONAL_SCOPE:
            findings.extend(self._scan_functional_scope(plan_bundle))
        elif category == TaxonomyCategory.DATA_MODEL:
            findings.extend(self._scan_data_model(plan_bundle))
        elif category == TaxonomyCategory.INTERACTION_UX:
            findings.extend(self._scan_interaction_ux(plan_bundle))
        elif category == TaxonomyCategory.NON_FUNCTIONAL:
            findings.extend(self._scan_non_functional(plan_bundle))
        elif category == TaxonomyCategory.INTEGRATION:
            findings.extend(self._scan_integration(plan_bundle))
        elif category == TaxonomyCategory.EDGE_CASES:
            findings.extend(self._scan_edge_cases(plan_bundle))
        elif category == TaxonomyCategory.CONSTRAINTS:
            findings.extend(self._scan_constraints(plan_bundle))
        elif category == TaxonomyCategory.TERMINOLOGY:
            findings.extend(self._scan_terminology(plan_bundle))
        elif category == TaxonomyCategory.COMPLETION_SIGNALS:
            findings.extend(self._scan_completion_signals(plan_bundle))
        elif category == TaxonomyCategory.FEATURE_COMPLETENESS:
            findings.extend(self._scan_feature_completeness(plan_bundle))

        return findings

    @beartype
    def _scan_functional_scope(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan functional scope and behavior."""
        findings: list[AmbiguityFinding] = []

        # Check idea narrative
        if plan_bundle.idea and (not plan_bundle.idea.narrative or len(plan_bundle.idea.narrative.strip()) < 20):
            findings.append(
                AmbiguityFinding(
                    category=TaxonomyCategory.FUNCTIONAL_SCOPE,
                    status=AmbiguityStatus.PARTIAL,
                    description="Idea narrative is too brief or missing",
                    impact=0.8,
                    uncertainty=0.7,
                    question="What is the core user goal and success criteria for this plan?",
                    related_sections=["idea.narrative"],
                )
            )

        # Check target users
        if plan_bundle.idea and not plan_bundle.idea.target_users:
            # Try to auto-extract from codebase if available
            suggested_users = self._extract_target_users(plan_bundle) if self.repo_path else None

            question = "Who are the target users or personas for this plan?"
            if suggested_users:
                question += f" (Suggested: {', '.join(suggested_users)})"

            findings.append(
                AmbiguityFinding(
                    category=TaxonomyCategory.FUNCTIONAL_SCOPE,
                    status=AmbiguityStatus.MISSING,
                    description="Target users/personas not specified",
                    impact=0.7,
                    uncertainty=0.6,
                    question=question,
                    related_sections=["idea.target_users"],
                )
            )

        # Check features have clear outcomes
        for feature in plan_bundle.features:
            if not feature.outcomes:
                findings.append(
                    AmbiguityFinding(
                        category=TaxonomyCategory.FUNCTIONAL_SCOPE,
                        status=AmbiguityStatus.MISSING,
                        description=f"Feature {feature.key} has no outcomes specified",
                        impact=0.6,
                        uncertainty=0.5,
                        question=f"What are the expected outcomes for feature {feature.key} ({feature.title})?",
                        related_sections=[f"features.{feature.key}.outcomes"],
                    )
                )

            # Check for behavioral descriptions in acceptance criteria
            # Behavioral patterns: action verbs, user/system actions, conditional logic
            behavioral_patterns = [
                "can ",
                "should ",
                "must ",
                "will ",
                "when ",
                "then ",
                "if ",
                "after ",
                "before ",
                "user ",
                "system ",
                "application ",
                "allows ",
                "enables ",
                "performs ",
                "executes ",
                "triggers ",
                "responds ",
                "validates ",
                "processes ",
                "handles ",
                "supports ",
            ]

            has_behavioral_content = False
            if feature.acceptance:
                has_behavioral_content = any(
                    any(pattern in acc.lower() for pattern in behavioral_patterns) for acc in feature.acceptance
                )

            # Also check stories for behavioral content
            story_has_behavior = False
            for story in feature.stories:
                if story.acceptance and any(
                    any(pattern in acc.lower() for pattern in behavioral_patterns) for acc in story.acceptance
                ):
                    story_has_behavior = True
                    break

            # If no behavioral content found in feature or stories, flag it
            if not has_behavioral_content and not story_has_behavior:
                # Check if feature has any acceptance criteria at all
                if not feature.acceptance and not any(story.acceptance for story in feature.stories):
                    findings.append(
                        AmbiguityFinding(
                            category=TaxonomyCategory.FUNCTIONAL_SCOPE,
                            status=AmbiguityStatus.MISSING,
                            description=f"Feature {feature.key} has no acceptance criteria with behavioral descriptions",
                            impact=0.7,
                            uncertainty=0.6,
                            question=f"What are the behavioral requirements for feature {feature.key} ({feature.title})? How should it behave in different scenarios?",
                            related_sections=[f"features.{feature.key}.acceptance", f"features.{feature.key}.stories"],
                        )
                    )
                elif feature.acceptance or any(story.acceptance for story in feature.stories):
                    # Has acceptance criteria but lacks behavioral patterns
                    findings.append(
                        AmbiguityFinding(
                            category=TaxonomyCategory.FUNCTIONAL_SCOPE,
                            status=AmbiguityStatus.PARTIAL,
                            description=f"Feature {feature.key} has acceptance criteria but may lack clear behavioral descriptions",
                            impact=0.5,
                            uncertainty=0.5,
                            question=f"Are the acceptance criteria for feature {feature.key} ({feature.title}) clear about expected behavior? Consider adding behavioral patterns (e.g., 'user can...', 'system should...', 'when X then Y').",
                            related_sections=[f"features.{feature.key}.acceptance", f"features.{feature.key}.stories"],
                        )
                    )

        return findings

    @beartype
    def _scan_data_model(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan domain and data model."""
        findings: list[AmbiguityFinding] = []

        # Check if features reference data entities without constraints
        for feature in plan_bundle.features:
            # Look for data-related keywords in outcomes/acceptance
            data_keywords = ["data", "entity", "model", "record", "database", "storage"]
            has_data_mentions = any(
                keyword in outcome.lower() or keyword in acc.lower()
                for outcome in feature.outcomes
                for acc in feature.acceptance
                for keyword in data_keywords
            )

            if has_data_mentions and not feature.constraints:
                findings.append(
                    AmbiguityFinding(
                        category=TaxonomyCategory.DATA_MODEL,
                        status=AmbiguityStatus.PARTIAL,
                        description=f"Feature {feature.key} mentions data but has no constraints",
                        impact=0.5,
                        uncertainty=0.6,
                        question=f"What are the data model constraints for feature {feature.key} ({feature.title})?",
                        related_sections=[f"features.{feature.key}.constraints"],
                    )
                )

        return findings

    @beartype
    def _scan_interaction_ux(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan interaction and UX flow."""
        findings: list[AmbiguityFinding] = []

        # Check stories for UX-related acceptance criteria
        for feature in plan_bundle.features:
            for story in feature.stories:
                # Check if story mentions user interaction but lacks error handling
                ux_keywords = ["user", "click", "input", "form", "button", "interface", "ui"]
                has_ux_mentions = any(keyword in story.title.lower() for keyword in ux_keywords)

                if has_ux_mentions:
                    # Check for error/empty state handling
                    error_keywords = ["error", "empty", "invalid", "validation", "failure"]
                    has_error_handling = any(
                        keyword in acc.lower() for acc in story.acceptance for keyword in error_keywords
                    )

                    if not has_error_handling:
                        findings.append(
                            AmbiguityFinding(
                                category=TaxonomyCategory.INTERACTION_UX,
                                status=AmbiguityStatus.PARTIAL,
                                description=f"Story {story.key} mentions UX but lacks error handling",
                                impact=0.5,
                                uncertainty=0.4,
                                question=f"What error/empty states should be handled for story {story.key} ({story.title})?",
                                related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                            )
                        )

        return findings

    @beartype
    def _scan_non_functional(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan non-functional quality attributes."""
        findings: list[AmbiguityFinding] = []

        # Check idea constraints for non-functional requirements
        if (
            plan_bundle.idea
            and plan_bundle.idea.constraints
            and any(
                term in constraint.lower()
                for constraint in plan_bundle.idea.constraints
                for term in ["robust", "scalable", "fast", "secure", "reliable", "intuitive"]
            )
        ):
            findings.append(
                AmbiguityFinding(
                    category=TaxonomyCategory.NON_FUNCTIONAL,
                    status=AmbiguityStatus.PARTIAL,
                    description="Non-functional requirements use vague terms without quantification",
                    impact=0.7,
                    uncertainty=0.8,
                    question="What are the measurable targets for non-functional requirements (performance, scalability, security)?",
                    related_sections=["idea.constraints"],
                )
            )

        return findings

    @beartype
    def _scan_integration(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan integration and external dependencies."""
        findings: list[AmbiguityFinding] = []

        # Check features for external service mentions
        integration_keywords = ["api", "service", "external", "third-party", "integration", "sync"]
        for feature in plan_bundle.features:
            has_integration_mentions = any(
                keyword in outcome.lower() or keyword in acc.lower()
                for outcome in feature.outcomes
                for acc in feature.acceptance
                for keyword in integration_keywords
            )

            if has_integration_mentions and not feature.constraints:
                findings.append(
                    AmbiguityFinding(
                        category=TaxonomyCategory.INTEGRATION,
                        status=AmbiguityStatus.PARTIAL,
                        description=f"Feature {feature.key} mentions integration but has no constraints",
                        impact=0.6,
                        uncertainty=0.5,
                        question=f"What are the external dependency constraints and failure modes for feature {feature.key} ({feature.title})?",
                        related_sections=[f"features.{feature.key}.constraints"],
                    )
                )

        return findings

    @beartype
    def _scan_edge_cases(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan edge cases and failure handling."""
        findings: list[AmbiguityFinding] = []

        # Check stories for edge case coverage
        for feature in plan_bundle.features:
            for story in feature.stories:
                # Check if story has acceptance criteria but no edge cases
                if (
                    story.acceptance
                    and not any(
                        keyword in acc.lower()
                        for acc in story.acceptance
                        for keyword in ["edge", "corner", "boundary", "limit", "invalid", "null", "empty"]
                    )
                    and len(story.acceptance) < 3
                ):
                    # Low acceptance criteria count might indicate missing edge cases
                    findings.append(
                        AmbiguityFinding(
                            category=TaxonomyCategory.EDGE_CASES,
                            status=AmbiguityStatus.PARTIAL,
                            description=f"Story {story.key} has limited acceptance criteria, may be missing edge cases",
                            impact=0.4,
                            uncertainty=0.5,
                            question=f"What edge cases or negative scenarios should be handled for story {story.key} ({story.title})?",
                            related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                        )
                    )

        return findings

    @beartype
    def _scan_constraints(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan constraints and tradeoffs."""
        findings: list[AmbiguityFinding] = []

        # Check if idea has constraints
        if plan_bundle.idea and not plan_bundle.idea.constraints:
            findings.append(
                AmbiguityFinding(
                    category=TaxonomyCategory.CONSTRAINTS,
                    status=AmbiguityStatus.MISSING,
                    description="No technical or business constraints specified",
                    impact=0.5,
                    uncertainty=0.6,
                    question="What are the technical constraints (language, storage, hosting) and explicit tradeoffs?",
                    related_sections=["idea.constraints"],
                )
            )

        return findings

    @beartype
    def _scan_terminology(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan terminology and consistency."""
        findings: list[AmbiguityFinding] = []

        # Check for inconsistent terminology across features
        terms: dict[str, list[str]] = {}
        for feature in plan_bundle.features:
            # Extract key terms from title and outcomes
            feature_terms = set(feature.title.lower().split())
            for outcome in feature.outcomes:
                feature_terms.update(outcome.lower().split())

            for term in feature_terms:
                if len(term) > 4:  # Only check meaningful terms
                    if term not in terms:
                        terms[term] = []
                    terms[term].append(feature.key)

        # Find terms used in multiple features (potential inconsistency)
        # For now, skip terminology checks (low priority)
        # This is a simple heuristic - could be enhanced
        _ = terms  # Unused for now

        return findings

    @beartype
    def _scan_completion_signals(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan completion signals and testability."""
        findings: list[AmbiguityFinding] = []

        # Check stories for testable acceptance criteria
        for feature in plan_bundle.features:
            for story in feature.stories:
                if not story.acceptance:
                    findings.append(
                        AmbiguityFinding(
                            category=TaxonomyCategory.COMPLETION_SIGNALS,
                            status=AmbiguityStatus.MISSING,
                            description=f"Story {story.key} has no acceptance criteria",
                            impact=0.8,
                            uncertainty=0.7,
                            question=f"What are the testable acceptance criteria for story {story.key} ({story.title})?",
                            related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                        )
                    )
                else:
                    # Check for vague acceptance criteria patterns
                    # BUT: Skip if criteria are already code-specific (preserve code-specific criteria from code2spec)
                    # AND: Skip if criteria use the new simplified format (post-GWT refactoring)
                    from specfact_cli.utils.acceptance_criteria import (
                        is_code_specific_criteria,
                        is_simplified_format_criteria,
                    )

                    vague_patterns = [
                        "is implemented",
                        "is functional",
                        "works",
                        "is done",
                        "is complete",
                        "is ready",
                    ]

                    # Only check criteria that are NOT code-specific AND NOT using simplified format
                    # Note: Acceptance criteria are simple text descriptions (not OpenAPI format)
                    # Detailed testable examples are stored in OpenAPI contract files (.openapi.yaml)
                    # The new simplified format (e.g., "Must verify X works correctly (see contract examples)")
                    # is VALID and should not be flagged as vague
                    non_code_specific_criteria = [
                        acc
                        for acc in story.acceptance
                        if not is_code_specific_criteria(acc) and not is_simplified_format_criteria(acc)
                    ]

                    vague_criteria = [
                        acc
                        for acc in non_code_specific_criteria
                        if any(pattern in acc.lower() for pattern in vague_patterns)
                    ]

                    if vague_criteria:
                        findings.append(
                            AmbiguityFinding(
                                category=TaxonomyCategory.COMPLETION_SIGNALS,
                                status=AmbiguityStatus.PARTIAL,
                                description=f"Story {story.key} has vague acceptance criteria: {', '.join(vague_criteria[:2])}",
                                impact=0.7,
                                uncertainty=0.6,
                                question=f"Story {story.key} ({story.title}) has vague acceptance criteria (e.g., '{vague_criteria[0]}'). Should these be more specific? Note: Detailed test examples should be in OpenAPI contract files, not acceptance criteria.",
                                related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                            )
                        )
                    elif not any(
                        keyword in acc.lower()
                        for acc in story.acceptance
                        for keyword in [
                            "must",
                            "should",
                            "will",
                            "verify",
                            "validate",
                            "check",
                        ]
                    ):
                        # Check if acceptance criteria are measurable
                        findings.append(
                            AmbiguityFinding(
                                category=TaxonomyCategory.COMPLETION_SIGNALS,
                                status=AmbiguityStatus.PARTIAL,
                                description=f"Story {story.key} acceptance criteria may not be testable",
                                impact=0.5,
                                uncertainty=0.4,
                                question=f"Are the acceptance criteria for story {story.key} ({story.title}) measurable and testable?",
                                related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                            )
                        )

        return findings

    @beartype
    def _scan_feature_completeness(self, plan_bundle: PlanBundle) -> list[AmbiguityFinding]:
        """Scan feature and story completeness."""
        findings: list[AmbiguityFinding] = []

        # Check features without stories
        for feature in plan_bundle.features:
            if not feature.stories:
                findings.append(
                    AmbiguityFinding(
                        category=TaxonomyCategory.FEATURE_COMPLETENESS,
                        status=AmbiguityStatus.MISSING,
                        description=f"Feature {feature.key} has no stories",
                        impact=0.9,
                        uncertainty=0.8,
                        question=f"What user stories are needed for feature {feature.key} ({feature.title})?",
                        related_sections=[f"features.{feature.key}.stories"],
                    )
                )

            # Check features without acceptance criteria
            if not feature.acceptance:
                findings.append(
                    AmbiguityFinding(
                        category=TaxonomyCategory.FEATURE_COMPLETENESS,
                        status=AmbiguityStatus.MISSING,
                        description=f"Feature {feature.key} has no acceptance criteria",
                        impact=0.7,
                        uncertainty=0.6,
                        question=f"What are the acceptance criteria for feature {feature.key} ({feature.title})?",
                        related_sections=[f"features.{feature.key}.acceptance"],
                    )
                )

            # Check for incomplete requirements in outcomes
            for outcome in feature.outcomes:
                # Check for incomplete patterns like "System MUST Helper class" (missing verb/object)
                incomplete_patterns = [
                    "system must",
                    "system should",
                    "must",
                    "should",
                ]
                outcome_lower = outcome.lower()
                # Check if outcome starts with pattern but is incomplete (missing verb after "must" or ends abruptly)
                for pattern in incomplete_patterns:
                    if outcome_lower.startswith(pattern):
                        # Check if it's incomplete (e.g., "System MUST Helper class" - missing verb)
                        remaining = outcome_lower[len(pattern) :].strip()
                        # If remaining is just a noun phrase without a verb, it's likely incomplete
                        if (
                            remaining
                            and len(remaining.split()) < 3
                            and any(
                                keyword in remaining
                                for keyword in ["class", "helper", "module", "component", "service", "function"]
                            )
                        ):
                            findings.append(
                                AmbiguityFinding(
                                    category=TaxonomyCategory.FEATURE_COMPLETENESS,
                                    status=AmbiguityStatus.PARTIAL,
                                    description=f"Feature {feature.key} has incomplete requirement: '{outcome}' (missing verb/action)",
                                    impact=0.6,
                                    uncertainty=0.5,
                                    question=f"Feature {feature.key} ({feature.title}) requirement '{outcome}' appears incomplete. What should the system do?",
                                    related_sections=[f"features.{feature.key}.outcomes"],
                                )
                            )
                            break

            # Check for generic tasks in stories
            for story in feature.stories:
                if story.tasks:
                    generic_patterns = [
                        "implement",
                        "create",
                        "add",
                        "set up",
                    ]
                    generic_tasks = [
                        task
                        for task in story.tasks
                        if any(
                            pattern in task.lower()
                            and not any(
                                detail in task.lower()
                                for detail in ["file", "path", "method", "class", "component", "module", "function"]
                            )
                            for pattern in generic_patterns
                        )
                    ]
                    if generic_tasks:
                        findings.append(
                            AmbiguityFinding(
                                category=TaxonomyCategory.FEATURE_COMPLETENESS,
                                status=AmbiguityStatus.PARTIAL,
                                description=f"Story {story.key} has generic tasks without implementation details: {', '.join(generic_tasks[:2])}",
                                impact=0.4,
                                uncertainty=0.3,
                                question=f"Story {story.key} ({story.title}) has generic tasks. Should these include file paths, method names, or component references?",
                                related_sections=[f"features.{feature.key}.stories.{story.key}.tasks"],
                            )
                        )

        return findings

    @beartype
    def _extract_target_users(self, plan_bundle: PlanBundle) -> list[str]:
        """
        Extract target users/personas from project metadata and plan bundle.

        Priority order (most reliable first):
        1. pyproject.toml classifiers and keywords
        2. README.md "Perfect for:" or "Target users:" patterns
        3. Story titles with "As a..." patterns
        4. Codebase user models (optional, conservative)

        Args:
            plan_bundle: Plan bundle to analyze

        Returns:
            List of suggested user personas (may be empty)
        """
        if not self.repo_path or not self.repo_path.exists():
            return []

        suggested_users: set[str] = set()

        # Common false positives to exclude (terms that aren't user personas)
        excluded_terms = {
            "a",
            "an",
            "the",
            "i",
            "can",
            "user",  # Too generic
            "users",  # Too generic
            "developer",  # Too generic - often refers to code developer, not persona
            "feature",
            "system",
            "application",
            "software",
            "code",
            "test",
            "detecting",  # Technical term, not a persona
            "data",  # Too generic
            "pipeline",  # Use case, not a persona
            "pipelines",  # Use case, not a persona
            "devops",  # Use case, not a persona
            "script",  # Technical term, not a persona
            "scripts",  # Technical term, not a persona
        }

        # 1. Extract from pyproject.toml (classifiers and keywords) - MOST RELIABLE
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                # Try standard library first (Python 3.11+)
                try:
                    import tomllib
                except ImportError:
                    # Fall back to tomli for older Python versions
                    try:
                        import tomli as tomllib
                    except ImportError:
                        # If neither is available, skip TOML parsing
                        tomllib = None

                if tomllib:
                    content = pyproject_path.read_text(encoding="utf-8")
                    data = tomllib.loads(content)

                    # Extract from classifiers (e.g., "Intended Audience :: Developers")
                    if "project" in data and "classifiers" in data["project"]:
                        for classifier in data["project"]["classifiers"]:
                            if "Intended Audience ::" in classifier:
                                audience = classifier.split("::")[-1].strip()
                                # Only add if it's a meaningful persona (not generic)
                                if (
                                    audience
                                    and audience.lower() not in excluded_terms
                                    and len(audience) > 3
                                    and not audience.isupper()
                                ):
                                    suggested_users.add(audience)

                    # Skip keywords extraction - too unreliable (contains technical terms)
                    # Keywords are typically technical terms, not user personas
                    # We rely on classifiers and README.md instead
            except Exception:
                # If pyproject.toml parsing fails, continue with other sources
                pass

        # 2. Extract from README.md ("Perfect for:", "Target users:", etc.) - VERY RELIABLE
        readme_path = self.repo_path / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")

                # Look for "Perfect for:" or "Target users:" patterns
                perfect_for_match = re.search(
                    r"(?:Perfect for|Target users?|For|Audience):\s*(.+?)(?:\n|$)", content, re.IGNORECASE
                )
                if perfect_for_match:
                    users_text = perfect_for_match.group(1)
                    # Split by commas, semicolons, or "and"
                    users = re.split(r"[,;]|\sand\s", users_text)
                    for user in users:
                        user_clean = user.strip()
                        # Remove markdown formatting and common prefixes
                        user_clean = re.sub(r"^\*\*?|\*\*?$", "", user_clean).strip()
                        # Check if it's a persona (not a use case or technical term)
                        user_lower = user_clean.lower()
                        # Skip if it's a use case (e.g., "data pipelines", "devops scripts")
                        if any(
                            use_case in user_lower
                            for use_case in ["pipeline", "script", "system", "application", "code", "api", "service"]
                        ):
                            continue
                        if (
                            user_clean
                            and len(user_clean) > 2
                            and user_lower not in excluded_terms
                            and len(user_clean.split()) <= 3
                        ):
                            suggested_users.add(user_clean.title())
            except Exception:
                # If README.md parsing fails, continue with other sources
                pass

        # 3. Extract from story titles (e.g., "As a user, I can...") - RELIABLE
        for feature in plan_bundle.features:
            for story in feature.stories:
                # Look for "As a X" or "As an X" patterns - be more precise
                match = re.search(
                    r"as (?:a|an) ([^,\.]+?)(?:\s+(?:i|can|want|need|should|will)|$)", story.title.lower()
                )
                if match:
                    user_type = match.group(1).strip()
                    # Only add if it's a reasonable persona (not a technical term)
                    if (
                        user_type
                        and len(user_type) > 2
                        and user_type.lower() not in excluded_terms
                        and not user_type.isupper()
                        and len(user_type.split()) <= 3
                    ):
                        suggested_users.add(user_type.title())

        # 4. Extract from codebase (user models, roles, permissions) - OPTIONAL FALLBACK
        # Only look in specific directories that typically contain user models
        # Skip if we already have good suggestions from metadata
        if self.repo_path and len(suggested_users) < 2:
            try:
                user_model_dirs = ["models", "auth", "users", "accounts", "roles", "permissions", "user"]
                search_paths = []
                for subdir in user_model_dirs:
                    potential_path = self.repo_path / subdir
                    if potential_path.exists() and potential_path.is_dir():
                        search_paths.append(potential_path)

                # If no specific directories found, skip codebase extraction (too risky)
                if not search_paths:
                    # Only extract from story titles - codebase extraction is too unreliable
                    pass
                else:
                    for search_path in search_paths:
                        for py_file in search_path.rglob("*.py"):
                            if py_file.is_file():
                                try:
                                    content = py_file.read_text(encoding="utf-8")
                                    tree = ast.parse(content, filename=str(py_file))

                                    for node in ast.walk(tree):
                                        # Look for class definitions with "user" in name (most specific)
                                        if isinstance(node, ast.ClassDef):
                                            class_name = node.name
                                            class_name_lower = class_name.lower()

                                            # Only consider classes that are clearly user models
                                            # Pattern: *User, User*, *Role, Role*, *Persona, Persona*
                                            if class_name_lower.endswith(
                                                ("user", "role", "persona")
                                            ) or class_name_lower.startswith(("user", "role", "persona")):
                                                # Extract role from class name (e.g., "AdminUser" -> "Admin")
                                                if class_name_lower.endswith("user"):
                                                    role = class_name_lower[:-4].strip()
                                                elif class_name_lower.startswith("user"):
                                                    role = class_name_lower[4:].strip()
                                                elif class_name_lower.endswith("role"):
                                                    role = class_name_lower[:-4].strip()
                                                elif class_name_lower.startswith("role"):
                                                    role = class_name_lower[4:].strip()
                                                else:
                                                    role = class_name_lower.replace("persona", "").strip()

                                                # Clean up role name
                                                role = re.sub(r"[_-]", " ", role).strip()
                                                if (
                                                    role
                                                    and role.lower() not in excluded_terms
                                                    and len(role) > 2
                                                    and len(role.split()) <= 2
                                                    and not role.isupper()
                                                    and not re.match(r"^[A-Z][a-z]+[A-Z]", role)
                                                ):
                                                    suggested_users.add(role.title())

                                            # Look for role/permission enum values or constants
                                            for item in node.body:
                                                if isinstance(item, ast.Assign) and item.targets:
                                                    for target in item.targets:
                                                        if isinstance(target, ast.Name):
                                                            attr_name = target.id.lower()
                                                            # Look for role/permission constants (e.g., ADMIN = "admin")
                                                            if (
                                                                "role" in attr_name or "permission" in attr_name
                                                            ) and isinstance(item.value, (ast.Str, ast.Constant)):
                                                                role_value = (
                                                                    item.value.s
                                                                    if isinstance(item.value, ast.Str)
                                                                    else item.value
                                                                )
                                                                if isinstance(role_value, str) and len(role_value) > 2:
                                                                    role_clean = role_value.strip().lower()
                                                                    if (
                                                                        role_clean not in excluded_terms
                                                                        and len(role_clean.split()) <= 2
                                                                    ):
                                                                        suggested_users.add(role_value.title())

                                except (SyntaxError, UnicodeDecodeError, Exception):
                                    # Skip files that can't be parsed
                                    continue
            except Exception:
                # If codebase analysis fails, continue with story-based extraction
                pass

        # 3. Extract from feature outcomes/acceptance - VERY CONSERVATIVE
        # Only look for clear persona patterns (single words only)
        for feature in plan_bundle.features:
            for outcome in feature.outcomes:
                # Look for patterns like "allows [persona] to..." or "enables [persona] to..."
                # But be very selective - only single-word personas
                matches = re.findall(r"(?:allows|enables|for) ([a-z]+) (?:to|can)", outcome.lower())
                for match in matches:
                    match_clean = match.strip()
                    if (
                        match_clean
                        and len(match_clean) > 2
                        and match_clean not in excluded_terms
                        and len(match_clean.split()) == 1  # Only single words
                    ):
                        suggested_users.add(match_clean.title())

        # Final filtering: remove any remaining technical terms
        cleaned_users: list[str] = []
        for user in suggested_users:
            user_lower = user.lower()
            # Skip if it's in excluded terms or looks technical
            if (
                user_lower not in excluded_terms
                and len(user.split()) <= 2
                and not user.isupper()
                and not re.match(r"^[A-Z][a-z]+[A-Z]", user)
            ):
                cleaned_users.append(user)

        # Return top 3 most common suggestions (reduced from 5 for quality)
        return sorted(set(cleaned_users))[:3]
