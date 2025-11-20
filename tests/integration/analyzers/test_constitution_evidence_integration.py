"""Integration tests for ConstitutionEvidenceExtractor with SpecKitConverter."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from specfact_cli.analyzers.constitution_evidence_extractor import ConstitutionEvidenceExtractor
from specfact_cli.importers.speckit_converter import SpecKitConverter
from specfact_cli.models.plan import Feature, PlanBundle, Product, Story


@pytest.fixture
def test_repo() -> Iterator[Path]:
    """Create a test repository with code for constitution analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / "src" / "module").mkdir(parents=True)
        (repo_path / "tests").mkdir()

        # Create Python files with contracts
        (repo_path / "src" / "module" / "__init__.py").write_text("")
        (repo_path / "src" / "module" / "api.py").write_text(
            """
from icontract import require, ensure
from beartype import beartype

@require(lambda x: x > 0)
@ensure(lambda result: result > 0)
@beartype
def process_data(x: int) -> int:
    return x * 2
"""
        )

        # Create a simple plan bundle for testing
        (repo_path / ".specfact" / "plans").mkdir(parents=True)

        yield repo_path


class TestConstitutionEvidenceIntegration:
    """Integration tests for ConstitutionEvidenceExtractor with SpecKitConverter."""

    def test_constitution_extractor_in_speckit_converter(self, test_repo: Path) -> None:
        """Test that ConstitutionEvidenceExtractor is integrated into SpecKitConverter."""
        converter = SpecKitConverter(test_repo)
        assert hasattr(converter, "constitution_extractor")
        assert isinstance(converter.constitution_extractor, ConstitutionEvidenceExtractor)

    def test_constitution_check_section_generation(self, test_repo: Path) -> None:
        """Test that constitution check section is generated in plan.md."""
        # Create a simple plan bundle
        plan_bundle = PlanBundle(
            product=Product(),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    stories=[
                        Story(
                            key="STORY-001",
                            title="Test Story",
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts={
                                "parameters": [{"name": "x", "type": "int", "required": True}],
                                "return_type": {"type": "int"},
                            },
                        )
                    ],
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        converter = SpecKitConverter(test_repo)
        converter.convert_to_speckit(plan_bundle)

        # Check that plan.md was generated
        plan_file = test_repo / "specs" / "001-test-feature" / "plan.md"
        assert plan_file.exists()

        # Check that constitution check section is present
        plan_content = plan_file.read_text(encoding="utf-8")
        assert "## Constitution Check" in plan_content
        assert "Article VII" in plan_content
        assert "Article VIII" in plan_content
        assert "Article IX" in plan_content

    def test_constitution_check_has_status(self, test_repo: Path) -> None:
        """Test that constitution check section has PASS/FAIL status (not PENDING)."""
        plan_bundle = PlanBundle(
            product=Product(),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    stories=[],
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        converter = SpecKitConverter(test_repo)
        converter.convert_to_speckit(plan_bundle)

        plan_file = test_repo / "specs" / "001-test-feature" / "plan.md"
        plan_content = plan_file.read_text(encoding="utf-8")

        # Should have PASS or FAIL status, but not PENDING
        assert "**Status**: PASS" in plan_content or "**Status**: FAIL" in plan_content
        assert "**Status**: PENDING" not in plan_content

    def test_constitution_check_has_evidence(self, test_repo: Path) -> None:
        """Test that constitution check section includes evidence."""
        plan_bundle = PlanBundle(
            product=Product(),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    stories=[],
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        converter = SpecKitConverter(test_repo)
        converter.convert_to_speckit(plan_bundle)

        plan_file = test_repo / "specs" / "001-test-feature" / "plan.md"
        plan_content = plan_file.read_text(encoding="utf-8")

        # Should have rationale for each article
        assert "rationale" in plan_content.lower() or "Project" in plan_content

    def test_constitution_check_fallback_on_error(self, test_repo: Path) -> None:
        """Test that constitution check falls back gracefully on extraction errors."""
        # Create a plan bundle
        plan_bundle = PlanBundle(
            product=Product(),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    stories=[],
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        converter = SpecKitConverter(test_repo)
        # Mock an error in the extractor
        original_extract = converter.constitution_extractor.extract_all_evidence

        def failing_extract(*args: object, **kwargs: object) -> dict[str, object]:
            raise Exception("Test error")

        converter.constitution_extractor.extract_all_evidence = failing_extract

        # Should not raise, but fall back to basic check
        converter.convert_to_speckit(plan_bundle)

        plan_file = test_repo / "specs" / "001-test-feature" / "plan.md"
        assert plan_file.exists()

        plan_content = plan_file.read_text(encoding="utf-8")
        # Should have fallback constitution check
        assert "## Constitution Check" in plan_content

        # Restore original method
        converter.constitution_extractor.extract_all_evidence = original_extract
