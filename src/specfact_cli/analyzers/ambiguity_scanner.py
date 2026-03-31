"""
Ambiguity scanner for plan bundle review.

This module analyzes plan bundles to identify ambiguities, missing information,
and unknowns using a structured taxonomy.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import PlanBundle


class AmbiguityStatus(StrEnum):
    """Ambiguity status levels."""

    CLEAR = "Clear"
    PARTIAL = "Partial"
    MISSING = "Missing"


class TaxonomyCategory(StrEnum):
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


def _pyproject_classifier_strings_from_text(text: str) -> list[str]:
    """Return project.classifiers from pyproject.toml text as strings."""
    try:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                return []
        _tl = cast(Any, tomllib)
        raw = _tl.loads(text)
        data = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}
        project_raw = data.get("project")
        project = cast(dict[str, Any], project_raw) if isinstance(project_raw, dict) else {}
        classifiers_raw = project.get("classifiers", [])
        if not isinstance(classifiers_raw, list):
            return []
        return [c for c in classifiers_raw if isinstance(c, str)]
    except Exception:
        return []


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

    _BEHAVIORAL_PATTERNS: tuple[str, ...] = (
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
    )

    @staticmethod
    def _acceptance_list_has_behavioral_pattern(acceptance_lines: list[str], patterns: tuple[str, ...]) -> bool:
        return bool(acceptance_lines and any(any(p in acc.lower() for p in patterns) for acc in acceptance_lines))

    def _feature_has_behavioral_descriptions(self, feature: Any, patterns: tuple[str, ...]) -> bool:
        if self._acceptance_list_has_behavioral_pattern(list(feature.acceptance or []), patterns):
            return True
        return any(
            self._acceptance_list_has_behavioral_pattern(list(story.acceptance or []), patterns)
            for story in feature.stories
        )

    def _functional_scope_findings_for_feature(self, feature: Any) -> list[AmbiguityFinding]:
        findings: list[AmbiguityFinding] = []
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
        patterns = self._BEHAVIORAL_PATTERNS
        if self._feature_has_behavioral_descriptions(feature, patterns):
            return findings
        has_any_acceptance = bool(feature.acceptance or any(story.acceptance for story in feature.stories))
        if not has_any_acceptance:
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
            return findings
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

        for feature in plan_bundle.features:
            findings.extend(self._functional_scope_findings_for_feature(feature))

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

    _VAGUE_ACCEPTANCE_PATTERNS: tuple[str, ...] = (
        "is implemented",
        "is functional",
        "works",
        "is done",
        "is complete",
        "is ready",
    )
    _TESTABILITY_KEYWORDS: tuple[str, ...] = ("must", "should", "will", "verify", "validate", "check")

    def _completion_findings_for_story_with_acceptance(self, feature: Any, story: Any) -> list[AmbiguityFinding]:
        from specfact_cli.utils.acceptance_criteria import (
            is_code_specific_criteria,
            is_simplified_format_criteria,
        )

        vague_patterns = self._VAGUE_ACCEPTANCE_PATTERNS
        non_code_specific_criteria = [
            acc
            for acc in story.acceptance
            if not is_code_specific_criteria(acc) and not is_simplified_format_criteria(acc)
        ]
        vague_criteria = [
            acc for acc in non_code_specific_criteria if any(pattern in acc.lower() for pattern in vague_patterns)
        ]
        if vague_criteria:
            return [
                AmbiguityFinding(
                    category=TaxonomyCategory.COMPLETION_SIGNALS,
                    status=AmbiguityStatus.PARTIAL,
                    description=f"Story {story.key} has vague acceptance criteria: {', '.join(vague_criteria[:2])}",
                    impact=0.7,
                    uncertainty=0.6,
                    question=f"Story {story.key} ({story.title}) has vague acceptance criteria (e.g., '{vague_criteria[0]}'). Should these be more specific? Note: Detailed test examples should be in OpenAPI contract files, not acceptance criteria.",
                    related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
                )
            ]
        if any(keyword in acc.lower() for acc in story.acceptance for keyword in self._TESTABILITY_KEYWORDS):
            return []
        return [
            AmbiguityFinding(
                category=TaxonomyCategory.COMPLETION_SIGNALS,
                status=AmbiguityStatus.PARTIAL,
                description=f"Story {story.key} acceptance criteria may not be testable",
                impact=0.5,
                uncertainty=0.4,
                question=f"Are the acceptance criteria for story {story.key} ({story.title}) measurable and testable?",
                related_sections=[f"features.{feature.key}.stories.{story.key}.acceptance"],
            )
        ]

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
                    findings.extend(self._completion_findings_for_story_with_acceptance(feature, story))

        return findings

    _INCOMPLETE_OUTCOME_PREFIXES: tuple[str, ...] = ("system must", "system should", "must", "should")
    _INCOMPLETE_OUTCOME_KEYWORDS: tuple[str, ...] = ("class", "helper", "module", "component", "service", "function")
    _GENERIC_TASK_PATTERNS: tuple[str, ...] = ("implement", "create", "add", "set up")
    _TASK_DETAIL_MARKERS: tuple[str, ...] = ("file", "path", "method", "class", "component", "module", "function")

    def _incomplete_outcome_findings(self, feature: Any) -> list[AmbiguityFinding]:
        findings: list[AmbiguityFinding] = []
        for outcome in feature.outcomes:
            outcome_lower = outcome.lower()
            for pattern in self._INCOMPLETE_OUTCOME_PREFIXES:
                if not outcome_lower.startswith(pattern):
                    continue
                remaining = outcome_lower[len(pattern) :].strip()
                if (
                    remaining
                    and len(remaining.split()) < 3
                    and any(kw in remaining for kw in self._INCOMPLETE_OUTCOME_KEYWORDS)
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
        return findings

    def _generic_task_finding_for_story(self, feature: Any, story: Any) -> AmbiguityFinding | None:
        if not story.tasks:
            return None
        generic_tasks = [
            task
            for task in story.tasks
            if any(
                pattern in task.lower() and not any(detail in task.lower() for detail in self._TASK_DETAIL_MARKERS)
                for pattern in self._GENERIC_TASK_PATTERNS
            )
        ]
        if not generic_tasks:
            return None
        return AmbiguityFinding(
            category=TaxonomyCategory.FEATURE_COMPLETENESS,
            status=AmbiguityStatus.PARTIAL,
            description=f"Story {story.key} has generic tasks without implementation details: {', '.join(generic_tasks[:2])}",
            impact=0.4,
            uncertainty=0.3,
            question=f"Story {story.key} ({story.title}) has generic tasks. Should these include file paths, method names, or component references?",
            related_sections=[f"features.{feature.key}.stories.{story.key}.tasks"],
        )

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

            findings.extend(self._incomplete_outcome_findings(feature))

            for story in feature.stories:
                gt = self._generic_task_finding_for_story(feature, story)
                if gt:
                    findings.append(gt)

        return findings

    _EXCLUDED_PERSONA_TERMS: frozenset[str] = frozenset(
        {
            "a",
            "an",
            "the",
            "i",
            "can",
            "user",
            "users",
            "developer",
            "feature",
            "system",
            "application",
            "software",
            "code",
            "test",
            "detecting",
            "data",
            "pipeline",
            "pipelines",
            "devops",
            "script",
            "scripts",
        }
    )

    def _personas_from_pyproject(self) -> set[str]:
        """
        Extract persona suggestions from pyproject.toml classifiers.

        Returns:
            Set of candidate persona strings
        """
        excluded = self._EXCLUDED_PERSONA_TERMS
        result: set[str] = set()
        if not self.repo_path:
            return result
        pyproject_path = self.repo_path / "pyproject.toml"
        if not pyproject_path.exists():
            return result
        try:
            text = pyproject_path.read_text(encoding="utf-8")
        except Exception:
            return result
        for classifier in _pyproject_classifier_strings_from_text(text):
            if "Intended Audience ::" in classifier:
                audience = classifier.split("::")[-1].strip()
                if audience and audience.lower() not in excluded and len(audience) > 3 and not audience.isupper():
                    result.add(audience)
        return result

    def _personas_from_readme(self) -> set[str]:
        """
        Extract persona suggestions from README.md target-user patterns.

        Returns:
            Set of candidate persona strings
        """
        excluded = self._EXCLUDED_PERSONA_TERMS
        result: set[str] = set()
        if not self.repo_path:
            return result
        readme_path = self.repo_path / "README.md"
        if not readme_path.exists():
            return result
        try:
            content = readme_path.read_text(encoding="utf-8")
            m = re.search(r"(?:Perfect for|Target users?|For|Audience):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            if not m:
                return result
            use_case_terms = ["pipeline", "script", "system", "application", "code", "api", "service"]
            for user in re.split(r"[,;]|\sand\s", m.group(1)):
                user_clean = re.sub(r"^\*\*?|\*\*?$", "", user.strip()).strip()
                user_lower = user_clean.lower()
                if any(uc in user_lower for uc in use_case_terms):
                    continue
                if user_clean and len(user_clean) > 2 and user_lower not in excluded and len(user_clean.split()) <= 3:
                    result.add(user_clean.title())
        except (OSError, UnicodeDecodeError, re.error):
            pass
        return result

    def _personas_from_story_titles(self, plan_bundle: Any) -> set[str]:
        """
        Extract persona suggestions from "As a X" story title patterns.

        Args:
            plan_bundle: Plan bundle containing features and stories

        Returns:
            Set of candidate persona strings
        """
        excluded = self._EXCLUDED_PERSONA_TERMS
        result: set[str] = set()
        for feature in plan_bundle.features:
            for story in feature.stories:
                m = re.search(r"as (?:a|an) ([^,\.]+?)(?:\s+(?:i|can|want|need|should|will)|$)", story.title.lower())
                if m:
                    user_type = m.group(1).strip()
                    if (
                        user_type
                        and len(user_type) > 2
                        and user_type.lower() not in excluded
                        and not user_type.isupper()
                        and len(user_type.split()) <= 3
                    ):
                        result.add(user_type.title())
        return result

    @staticmethod
    def _role_fragment_from_class_name(cn: str) -> str:
        if cn.endswith("user"):
            return cn[:-4].strip()
        if cn.startswith("user"):
            return cn[4:].strip()
        if cn.endswith("role"):
            return cn[:-4].strip()
        if cn.startswith("role"):
            return cn[4:].strip()
        return cn.replace("persona", "").strip()

    def _add_persona_role_if_valid(self, role: str, result: set[str], excluded: frozenset[str]) -> None:
        role = re.sub(r"[_-]", " ", role).strip()
        if not role or role.lower() in excluded:
            return
        if len(role) <= 2 or len(role.split()) > 2 or role.isupper():
            return
        if re.match(r"^[A-Z][a-z]+[A-Z]", role):
            return
        result.add(role.title())

    def _personas_from_class_name_pattern(self, node: ast.ClassDef, result: set[str], excluded: frozenset[str]) -> None:
        cn = node.name.lower()
        if not (cn.endswith(("user", "role", "persona")) or cn.startswith(("user", "role", "persona"))):
            return
        self._add_persona_role_if_valid(self._role_fragment_from_class_name(cn), result, excluded)

    @staticmethod
    def _maybe_add_persona_from_class_assignment(
        target: ast.expr,
        value: ast.expr,
        result: set[str],
        excluded: frozenset[str],
    ) -> None:
        if not isinstance(target, ast.Name):
            return
        attr_name = target.id.lower()
        if "role" not in attr_name and "permission" not in attr_name:
            return
        if not isinstance(value, ast.Constant):
            return
        role_value = value.value
        if not isinstance(role_value, str) or len(role_value) <= 2:
            return
        role_clean = role_value.strip().lower()
        if role_clean in excluded or len(role_clean.split()) > 2:
            return
        result.add(role_value.title())

    @staticmethod
    def _personas_from_class_assignments(node: ast.ClassDef, result: set[str], excluded: frozenset[str]) -> None:
        for item in node.body:
            if not (isinstance(item, ast.Assign) and item.targets):
                continue
            for target in item.targets:
                AmbiguityScanner._maybe_add_persona_from_class_assignment(target, item.value, result, excluded)

    def _personas_from_py_file(self, py_file: Path, result: set[str], excluded: frozenset[str]) -> None:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            self._personas_from_class_name_pattern(node, result, excluded)
            self._personas_from_class_assignments(node, result, excluded)

    def _personas_from_codebase(self) -> set[str]:
        """
        Extract persona suggestions by scanning user/role model class names in the codebase.

        Only searches in directories likely to contain user models. Returns empty set if
        no specific model directories are found.

        Returns:
            Set of candidate persona strings
        """
        excluded = self._EXCLUDED_PERSONA_TERMS
        result: set[str] = set()
        if not self.repo_path:
            return result
        try:
            user_model_dirs = ["models", "auth", "users", "accounts", "roles", "permissions", "user"]
            search_paths = [
                self.repo_path / d
                for d in user_model_dirs
                if (self.repo_path / d).exists() and (self.repo_path / d).is_dir()
            ]
            if not search_paths:
                return result
            for search_path in search_paths:
                for py_file in search_path.rglob("*.py"):
                    if not py_file.is_file():
                        continue
                    try:
                        self._personas_from_py_file(py_file, result, excluded)
                    except (OSError, UnicodeDecodeError, re.error):
                        continue
        except (OSError, UnicodeDecodeError, re.error):
            pass
        return result

    def _personas_from_outcomes(self, plan_bundle: Any) -> set[str]:
        """
        Extract single-word persona suggestions from feature outcome sentences.

        Very conservative: only matches patterns like "allows X to" or "enables X to".

        Args:
            plan_bundle: Plan bundle containing features

        Returns:
            Set of candidate persona strings
        """
        excluded = self._EXCLUDED_PERSONA_TERMS
        result: set[str] = set()
        for feature in plan_bundle.features:
            for outcome in feature.outcomes:
                for match in re.findall(r"(?:allows|enables|for) ([a-z]+) (?:to|can)", outcome.lower()):
                    m = match.strip()
                    if m and len(m) > 2 and m not in excluded and len(m.split()) == 1:
                        result.add(m.title())
        return result

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
        suggested_users |= self._personas_from_pyproject()
        suggested_users |= self._personas_from_readme()
        suggested_users |= self._personas_from_story_titles(plan_bundle)

        if len(suggested_users) < 2:
            suggested_users |= self._personas_from_codebase()

        suggested_users |= self._personas_from_outcomes(plan_bundle)

        excluded = self._EXCLUDED_PERSONA_TERMS
        cleaned_users = [
            u
            for u in suggested_users
            if u.lower() not in excluded
            and len(u.split()) <= 2
            and not u.isupper()
            and not re.match(r"^[A-Z][a-z]+[A-Z]", u)
        ]
        return sorted(set(cleaned_users))[:3]
