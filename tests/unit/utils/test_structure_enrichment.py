"""Unit tests for enrichment report path utilities in SpecFactStructure."""

from __future__ import annotations

import os
from pathlib import Path

from specfact_cli.utils.structure import SpecFactStructure


class TestEnrichmentReportPath:
    """Test enrichment report path generation."""

    def test_get_enrichment_report_path_basic(self, tmp_path: Path):
        """Test basic enrichment report path generation."""
        plan_bundle = tmp_path / ".specfact" / "plans" / "test-plan.2025-11-17T10-00-00.bundle.yaml"
        plan_bundle.parent.mkdir(parents=True, exist_ok=True)
        plan_bundle.touch()

        enrichment_path = SpecFactStructure.get_enrichment_report_path(plan_bundle, base_path=tmp_path)

        assert enrichment_path.parent == tmp_path / ".specfact" / "reports" / "enrichment"
        assert enrichment_path.name == "test-plan.2025-11-17T10-00-00.enrichment.md"
        assert enrichment_path.exists() is False  # Directory created, file not created

    def test_get_enrichment_report_path_creates_directory(self, tmp_path: Path):
        """Test that enrichment report path creation creates the directory."""
        plan_bundle = tmp_path / ".specfact" / "plans" / "my-feature.2025-11-17T12-30-45.bundle.yaml"
        plan_bundle.parent.mkdir(parents=True, exist_ok=True)
        plan_bundle.touch()

        enrichment_path = SpecFactStructure.get_enrichment_report_path(plan_bundle, base_path=tmp_path)

        assert enrichment_path.parent.exists(), "Enrichment directory should be created"
        assert enrichment_path.parent.is_dir()

    def test_get_enrichment_report_path_name_matching(self, tmp_path: Path):
        """Test that enrichment report name matches plan bundle name."""
        plan_bundle = tmp_path / ".specfact" / "plans" / "api-client-v2.2025-11-04T22-17-22.bundle.yaml"
        plan_bundle.parent.mkdir(parents=True, exist_ok=True)
        plan_bundle.touch()

        enrichment_path = SpecFactStructure.get_enrichment_report_path(plan_bundle, base_path=tmp_path)

        expected_name = "api-client-v2.2025-11-04T22-17-22.enrichment.md"
        assert enrichment_path.name == expected_name

    def test_get_enrichment_report_path_fallback(self, tmp_path: Path):
        """Test fallback for non-standard plan bundle names."""
        plan_bundle = tmp_path / ".specfact" / "plans" / "custom-plan.yaml"
        plan_bundle.parent.mkdir(parents=True, exist_ok=True)
        plan_bundle.touch()

        enrichment_path = SpecFactStructure.get_enrichment_report_path(plan_bundle, base_path=tmp_path)

        assert enrichment_path.name == "custom-plan.enrichment.md"

    def test_get_enrichment_report_path_relative_base(self, tmp_path: Path):
        """Test enrichment report path with relative base path."""
        # Use tmp_path to avoid conflicts with existing .specfact directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            plan_bundle = tmp_path / ".specfact" / "plans" / "test.2025-11-17T10-00-00.bundle.yaml"
            plan_bundle.parent.mkdir(parents=True, exist_ok=True)
            plan_bundle.touch()

            enrichment_path = SpecFactStructure.get_enrichment_report_path(plan_bundle, base_path=tmp_path)

            assert ".specfact/reports/enrichment" in str(enrichment_path)
            assert enrichment_path.name == "test.2025-11-17T10-00-00.enrichment.md"
        finally:
            os.chdir(old_cwd)


class TestPlanBundleFromEnrichment:
    """Test get_plan_bundle_from_enrichment method."""

    def test_get_plan_bundle_from_enrichment_basic(self, tmp_path: Path):
        """Test basic plan bundle derivation from enrichment report."""
        # Create enrichment report
        enrichment_report = (
            tmp_path / ".specfact" / "reports" / "enrichment" / "test-plan.2025-11-17T10-00-00.enrichment.md"
        )
        enrichment_report.parent.mkdir(parents=True, exist_ok=True)
        enrichment_report.write_text("# Enrichment Report")

        # Create corresponding plan bundle
        plan_bundle = tmp_path / ".specfact" / "plans" / "test-plan.2025-11-17T10-00-00.bundle.yaml"
        plan_bundle.parent.mkdir(parents=True, exist_ok=True)
        plan_bundle.write_text("version: '1.0'")

        # Test derivation
        derived_plan = SpecFactStructure.get_plan_bundle_from_enrichment(enrichment_report, base_path=tmp_path)
        assert derived_plan is not None, "Should derive plan bundle path"
        assert derived_plan == plan_bundle, "Should match the actual plan bundle"

    def test_get_plan_bundle_from_enrichment_not_found(self, tmp_path: Path):
        """Test that None is returned when plan bundle doesn't exist."""
        # Create enrichment report without corresponding plan
        enrichment_report = (
            tmp_path / ".specfact" / "reports" / "enrichment" / "missing-plan.2025-11-17T10-00-00.enrichment.md"
        )
        enrichment_report.parent.mkdir(parents=True, exist_ok=True)
        enrichment_report.write_text("# Enrichment Report")

        # Test derivation
        derived_plan = SpecFactStructure.get_plan_bundle_from_enrichment(enrichment_report, base_path=tmp_path)
        assert derived_plan is None, "Should return None when plan bundle doesn't exist"


class TestEnrichedPlanPath:
    """Test get_enriched_plan_path method."""

    def test_get_enriched_plan_path_basic(self, tmp_path: Path):
        """Test basic enriched plan path generation."""
        original_plan = tmp_path / ".specfact" / "plans" / "test-plan.2025-11-17T10-00-00.bundle.yaml"
        original_plan.parent.mkdir(parents=True, exist_ok=True)
        original_plan.write_text("version: '1.0'")

        enriched_path = SpecFactStructure.get_enriched_plan_path(original_plan, base_path=tmp_path)

        assert enriched_path.name.startswith("test-plan"), "Should start with plan name"
        assert ".enriched." in enriched_path.name, "Should contain .enriched. label"
        assert enriched_path.name.endswith(".bundle.yaml"), "Should end with .bundle.yaml"
        assert enriched_path != original_plan, "Should be different from original"

    def test_get_enriched_plan_path_naming_convention(self, tmp_path: Path):
        """Test enriched plan naming convention matches expected format."""
        original_plan = tmp_path / ".specfact" / "plans" / "my-feature.2025-11-17T10-00-00.bundle.yaml"
        original_plan.parent.mkdir(parents=True, exist_ok=True)
        original_plan.write_text("version: '1.0'")

        enriched_path = SpecFactStructure.get_enriched_plan_path(original_plan, base_path=tmp_path)

        # Format: <name>.<original-timestamp>.enriched.<enrichment-timestamp>.bundle.yaml
        parts = enriched_path.stem.split(".")
        assert len(parts) >= 4, f"Enriched plan name should have at least 4 parts: {enriched_path.name}"
        assert parts[0] == "my-feature", "First part should be plan name"
        assert parts[1] == "2025-11-17T10-00-00", "Second part should be original timestamp"
        assert parts[2] == "enriched", "Third part should be 'enriched' label"
        # Fourth part should be enrichment timestamp (format: YYYY-MM-DDTHH-MM-SS)

    def test_get_enriched_plan_path_creates_directory(self, tmp_path: Path):
        """Test that enriched plan path creation creates the directory."""
        original_plan = tmp_path / ".specfact" / "plans" / "test.2025-11-17T10-00-00.bundle.yaml"
        original_plan.parent.mkdir(parents=True, exist_ok=True)
        original_plan.write_text("version: '1.0'")

        enriched_path = SpecFactStructure.get_enriched_plan_path(original_plan, base_path=tmp_path)

        assert enriched_path.parent.exists(), "Enriched plan directory should exist"
        assert enriched_path.parent == original_plan.parent, "Should be in same directory as original"
