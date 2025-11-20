"""
Unit tests for ambiguity scanner.
"""

from __future__ import annotations

from specfact_cli.analyzers.ambiguity_scanner import (
    AmbiguityFinding,
    AmbiguityReport,
    AmbiguityScanner,
    AmbiguityStatus,
    TaxonomyCategory,
)
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Story


def test_ambiguity_scanner_initialization() -> None:
    """Test ambiguity scanner initialization."""
    scanner = AmbiguityScanner()
    assert scanner is not None


def test_scan_empty_plan() -> None:
    """Test scanning empty plan bundle."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    assert isinstance(report, AmbiguityReport)
    # Empty plan may not have findings if idea is None (scanner checks idea existence)
    # But should have coverage for all categories
    assert report.coverage is not None
    assert len(report.coverage) == len(TaxonomyCategory)


def test_scan_functional_scope_missing_narrative() -> None:
    """Test scanning for missing idea narrative."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=Idea(
            title="Test Plan",
            narrative="",  # Empty narrative
            target_users=[],
            value_hypothesis="",
            constraints=[],
            metrics=None,
        ),
        business=None,
        product=Product(themes=[], releases=[]),
        features=[],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    # Should find missing narrative
    assert report.findings is not None
    functional_findings = [f for f in report.findings if f.category == TaxonomyCategory.FUNCTIONAL_SCOPE]
    assert len(functional_findings) > 0
    assert any("narrative" in f.description.lower() for f in functional_findings)


def test_scan_feature_completeness_missing_stories() -> None:
    """Test scanning for features without stories."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Test Feature",
                outcomes=["Test outcome"],
                acceptance=[],
                constraints=[],
                stories=[],  # No stories
                confidence=0.8,
                draft=False,
            )
        ],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    # Should find missing stories
    assert report.findings is not None
    completeness_findings = [f for f in report.findings if f.category == TaxonomyCategory.FEATURE_COMPLETENESS]
    assert len(completeness_findings) > 0
    assert any("no stories" in f.description.lower() for f in completeness_findings)


def test_scan_completion_signals_missing_acceptance() -> None:
    """Test scanning for stories without acceptance criteria."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Test Feature",
                outcomes=["Test outcome"],
                acceptance=[],
                constraints=[],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Test Story",
                        acceptance=[],  # No acceptance criteria
                        tags=[],
                        story_points=None,
                        value_points=None,
                        tasks=[],
                        confidence=0.8,
                        draft=False,
                        scenarios=None,
                    )
                ],
                confidence=0.8,
                draft=False,
            )
        ],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    # Should find missing acceptance criteria
    assert report.findings is not None
    completion_findings = [f for f in report.findings if f.category == TaxonomyCategory.COMPLETION_SIGNALS]
    assert len(completion_findings) > 0
    assert any("acceptance criteria" in f.description.lower() for f in completion_findings)


def test_scan_prioritization() -> None:
    """Test that findings are prioritized by impact x uncertainty."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Test Feature",
                outcomes=[],
                acceptance=[],
                constraints=[],
                stories=[],  # Missing stories (high impact)
                confidence=0.8,
                draft=False,
            )
        ],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    # Check priority score calculation
    assert report.findings is not None
    if report.findings:
        max_priority = max(f.impact * f.uncertainty for f in report.findings)
        assert report.priority_score == max_priority


def test_ambiguity_finding_validation() -> None:
    """Test AmbiguityFinding validation."""
    # Valid finding
    finding = AmbiguityFinding(
        category=TaxonomyCategory.FUNCTIONAL_SCOPE,
        status=AmbiguityStatus.MISSING,
        description="Test finding",
        impact=0.8,
        uncertainty=0.7,
    )
    assert finding.impact == 0.8
    assert finding.uncertainty == 0.7

    # Invalid impact (should raise in __post_init__)
    try:
        finding = AmbiguityFinding(
            category=TaxonomyCategory.FUNCTIONAL_SCOPE,
            status=AmbiguityStatus.MISSING,
            description="Test finding",
            impact=1.5,  # Invalid: > 1.0
            uncertainty=0.7,
        )
        raise AssertionError("Should have raised ValueError")
    except ValueError:
        pass  # Expected


def test_ambiguity_report_initialization() -> None:
    """Test AmbiguityReport initialization."""
    report = AmbiguityReport()
    assert report.findings == []
    assert report.coverage == {}
    assert report.priority_score == 0.0


def test_scan_coverage_status() -> None:
    """Test that coverage status is correctly determined."""
    scanner = AmbiguityScanner()
    bundle = PlanBundle(
        version="1.0",
        idea=Idea(
            title="Complete Plan",
            narrative="This is a complete narrative with sufficient detail to understand the plan goals and success criteria.",
            target_users=["Developers", "Users"],
            value_hypothesis="Test hypothesis",
            constraints=["Technical constraint"],
            metrics=None,
        ),
        business=None,
        product=Product(themes=["Core"], releases=[]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Complete Feature",
                outcomes=["Outcome 1", "Outcome 2"],
                acceptance=["Acceptance 1", "Acceptance 2"],
                constraints=["Constraint 1"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Complete Story",
                        acceptance=["Story acceptance 1", "Story acceptance 2"],
                        tags=[],
                        story_points=5,
                        value_points=8,
                        tasks=["Task 1"],
                        confidence=0.9,
                        draft=False,
                        scenarios=None,
                    )
                ],
                confidence=0.9,
                draft=False,
            )
        ],
        metadata=None,
        clarifications=None,
    )

    report = scanner.scan(bundle)

    # Should have fewer findings for a complete plan
    assert isinstance(report, AmbiguityReport)
    # Coverage should show some categories as Clear
    assert report.coverage is not None
    clear_categories = [cat for cat, status in report.coverage.items() if status == AmbiguityStatus.CLEAR]
    assert len(clear_categories) > 0
