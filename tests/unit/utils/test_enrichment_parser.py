"""Unit tests for enrichment parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product
from specfact_cli.utils.enrichment_parser import EnrichmentParser, EnrichmentReport, apply_enrichment


class TestEnrichmentReport:
    """Test EnrichmentReport class."""

    def test_init(self):
        """Test EnrichmentReport initialization."""
        report = EnrichmentReport()
        assert report.missing_features == []
        assert report.confidence_adjustments == {}
        assert report.business_context == {
            "priorities": [],
            "constraints": [],
            "unknowns": [],
        }

    def test_add_missing_feature(self):
        """Test adding missing features."""
        report = EnrichmentReport()
        feature = {
            "key": "FEATURE-TEST",
            "title": "Test Feature",
            "confidence": 0.85,
            "outcomes": ["Test outcome"],
        }
        report.add_missing_feature(feature)
        assert len(report.missing_features) == 1
        assert report.missing_features[0]["key"] == "FEATURE-TEST"

    def test_adjust_confidence(self):
        """Test confidence adjustments."""
        report = EnrichmentReport()
        report.adjust_confidence("FEATURE-TEST", 0.95)
        assert report.confidence_adjustments["FEATURE-TEST"] == 0.95

    def test_add_business_context(self):
        """Test adding business context."""
        report = EnrichmentReport()
        report.add_business_context("priorities", ["Priority 1", "Priority 2"])
        assert len(report.business_context["priorities"]) == 2


class TestEnrichmentParser:
    """Test EnrichmentParser class."""

    def test_parse_missing_features(self, tmp_path: Path):
        """Test parsing missing features from enrichment report."""
        report_content = """# Enrichment Report

## Missing Features

1. **IDE Integration Feature** (Key: FEATURE-IDEINTEGRATION)
   - Confidence: 0.85
   - Outcomes: Enables slash command support for VS Code/Cursor
   - Reason: AST missed because it's spread across multiple modules

2. **Command Orchestration** (Key: FEATURE-COMMANDORCHESTRATION)
   - Confidence: 0.80
   - Outcomes: Core CLI functionality for mode detection and routing
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        parser = EnrichmentParser()
        report = parser.parse(report_file)

        assert len(report.missing_features) == 2
        assert report.missing_features[0]["key"] == "FEATURE-IDEINTEGRATION"
        assert report.missing_features[0]["confidence"] == 0.85

    def test_parse_confidence_adjustments(self, tmp_path: Path):
        """Test parsing confidence adjustments."""
        report_content = """# Enrichment Report

## Confidence Adjustments

- FEATURE-ANALYZEAGENT → 0.95 (strong semantic understanding capabilities)
- FEATURE-SPECKITSYNC → 0.9 (well-implemented bidirectional sync)
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        parser = EnrichmentParser()
        report = parser.parse(report_file)

        assert len(report.confidence_adjustments) == 2
        assert report.confidence_adjustments["FEATURE-ANALYZEAGENT"] == 0.95
        assert report.confidence_adjustments["FEATURE-SPECKITSYNC"] == 0.9

    def test_parse_business_context(self, tmp_path: Path):
        """Test parsing business context."""
        report_content = """# Enrichment Report

## Business Context

- Priority: "Core CLI tool for contract-driven development"
- Constraint: "Must support both CI/CD and Copilot modes"
- Unknown: "Future integration requirements"
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        parser = EnrichmentParser()
        report = parser.parse(report_file)

        assert len(report.business_context["priorities"]) > 0
        assert len(report.business_context["constraints"]) > 0

    def test_parse_complete_report(self, tmp_path: Path):
        """Test parsing complete enrichment report."""
        report_content = """# Enrichment Report

## Missing Features

1. **IDE Integration Feature** (Key: FEATURE-IDEINTEGRATION)
   - Confidence: 0.85
   - Outcomes: Enables slash command support

## Confidence Adjustments

- FEATURE-ANALYZEAGENT → 0.95

## Business Context

- Priority: "Core CLI tool"
- Constraint: "Must support both modes"
"""
        report_file = tmp_path / "enrichment.md"
        report_file.write_text(report_content)

        parser = EnrichmentParser()
        report = parser.parse(report_file)

        assert len(report.missing_features) == 1
        assert len(report.confidence_adjustments) == 1
        assert len(report.business_context["priorities"]) > 0

    def test_parse_nonexistent_file(self, tmp_path: Path):
        """Test parsing nonexistent file raises FileNotFoundError."""
        parser = EnrichmentParser()
        nonexistent_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            parser.parse(nonexistent_file)


class TestApplyEnrichment:
    """Test apply_enrichment function."""

    def test_apply_confidence_adjustments(self):
        """Test applying confidence adjustments."""
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", metrics=None),
            product=Product(themes=["Test"]),
            features=[
                Feature(
                    key="FEATURE-TEST",
                    title="Test Feature",
                    confidence=0.7,
                    outcomes=[],
                    acceptance=[],
                    constraints=[],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            business=None,
            metadata=None,
            clarifications=None,
        )

        enrichment = EnrichmentReport()
        enrichment.adjust_confidence("FEATURE-TEST", 0.95)

        enriched = apply_enrichment(plan_bundle, enrichment)

        assert enriched.features[0].confidence == 0.95

    def test_apply_missing_features(self):
        """Test applying missing features."""
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", metrics=None),
            product=Product(themes=["Test"]),
            features=[],
            business=None,
            metadata=None,
            clarifications=None,
        )

        enrichment = EnrichmentReport()
        enrichment.add_missing_feature(
            {
                "key": "FEATURE-NEW",
                "title": "New Feature",
                "confidence": 0.85,
                "outcomes": ["New outcome"],
            }
        )

        enriched = apply_enrichment(plan_bundle, enrichment)

        assert len(enriched.features) == 1
        assert enriched.features[0].key == "FEATURE-NEW"
        assert enriched.features[0].confidence == 0.85

    def test_apply_business_context(self):
        """Test applying business context."""
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", constraints=[], metrics=None),
            product=Product(themes=["Test"]),
            features=[],
            business=None,
            metadata=None,
            clarifications=None,
        )

        enrichment = EnrichmentReport()
        enrichment.add_business_context("constraints", ["Constraint 1", "Constraint 2"])

        enriched = apply_enrichment(plan_bundle, enrichment)

        assert enriched.idea is not None
        assert len(enriched.idea.constraints) == 2
        assert "Constraint 1" in enriched.idea.constraints

    def test_apply_all_enrichments(self):
        """Test applying all enrichment types together."""
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", constraints=[], metrics=None),
            product=Product(themes=["Test"]),
            features=[
                Feature(
                    key="FEATURE-EXISTING",
                    title="Existing Feature",
                    confidence=0.7,
                    outcomes=[],
                    acceptance=[],
                    constraints=[],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            business=None,
            metadata=None,
            clarifications=None,
        )

        enrichment = EnrichmentReport()
        enrichment.adjust_confidence("FEATURE-EXISTING", 0.95)
        enrichment.add_missing_feature(
            {
                "key": "FEATURE-NEW",
                "title": "New Feature",
                "confidence": 0.85,
                "outcomes": ["New outcome"],
            }
        )
        enrichment.add_business_context("constraints", ["New constraint"])

        enriched = apply_enrichment(plan_bundle, enrichment)

        assert enriched.features[0].confidence == 0.95  # Adjusted
        assert len(enriched.features) == 2  # Original + new
        assert enriched.idea is not None
        assert len(enriched.idea.constraints) == 1  # Business context added

    def test_apply_enrichment_preserves_original(self):
        """Test that apply_enrichment doesn't mutate original plan bundle."""
        plan_bundle = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test narrative", metrics=None),
            product=Product(themes=["Test"]),
            features=[
                Feature(
                    key="FEATURE-TEST",
                    title="Test Feature",
                    confidence=0.7,
                    outcomes=[],
                    acceptance=[],
                    constraints=[],
                    stories=[],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                ),
            ],
            business=None,
            metadata=None,
            clarifications=None,
        )

        original_confidence = plan_bundle.features[0].confidence

        enrichment = EnrichmentReport()
        enrichment.adjust_confidence("FEATURE-TEST", 0.95)

        enriched = apply_enrichment(plan_bundle, enrichment)

        # Original should be unchanged
        assert plan_bundle.features[0].confidence == original_confidence
        # Enriched should have new value
        assert enriched.features[0].confidence == 0.95
