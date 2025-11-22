"""E2E tests for Phase 2: Constitution Evidence Extraction."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.analyzers.constitution_evidence_extractor import ConstitutionEvidenceExtractor
from specfact_cli.importers.speckit_converter import SpecKitConverter


@pytest.fixture
def real_codebase_repo() -> Iterator[Path]:
    """Create a realistic codebase structure for E2E testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / "src" / "app" / "api").mkdir(parents=True)
        (repo_path / "src" / "app" / "models").mkdir(parents=True)
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()

        # Create realistic Python files with contracts
        (repo_path / "src" / "app" / "__init__.py").write_text("")
        (repo_path / "src" / "app" / "api" / "__init__.py").write_text("")
        (repo_path / "src" / "app" / "api" / "endpoints.py").write_text(
            """
from icontract import require, ensure
from beartype import beartype
from pydantic import BaseModel

class RequestModel(BaseModel):
    value: int

@require(lambda request: request.value > 0)
@ensure(lambda result: result.status_code == 200)
@beartype
def process_request(request: RequestModel) -> dict[str, int]:
    return {"status_code": 200, "result": request.value * 2}
"""
        )

        (repo_path / "src" / "app" / "models" / "__init__.py").write_text("")
        (repo_path / "src" / "app" / "models" / "user.py").write_text(
            """
from icontract import require
from beartype import beartype

@require(lambda user_id: user_id > 0)
@beartype
def get_user(user_id: int) -> dict[str, str]:
    return {"id": str(user_id), "name": "Test User"}
"""
        )

        # Create test files
        (repo_path / "tests" / "__init__.py").write_text("")
        (repo_path / "tests" / "test_api.py").write_text(
            """
def test_process_request():
    pass
"""
        )

        yield repo_path


class TestPhase2ConstitutionEvidenceE2E:
    """E2E tests for Phase 2 constitution evidence extraction."""

    def test_constitution_evidence_extraction_from_real_codebase(self, real_codebase_repo: Path) -> None:
        """Test constitution evidence extraction from a realistic codebase."""
        extractor = ConstitutionEvidenceExtractor(real_codebase_repo)
        evidence = extractor.extract_all_evidence()

        # Verify all articles have evidence
        assert "article_vii" in evidence
        assert "article_viii" in evidence
        assert "article_ix" in evidence

        # Verify Article VII evidence
        article_vii = evidence["article_vii"]
        assert "status" in article_vii
        assert "rationale" in article_vii
        assert article_vii["status"] in ("PASS", "FAIL")

        # Verify Article VIII evidence
        article_viii = evidence["article_viii"]
        assert "status" in article_viii
        assert "rationale" in article_viii
        assert article_viii["status"] in ("PASS", "FAIL")
        # Should detect Pydantic (BaseModel)
        assert "pydantic" in article_viii.get("frameworks_detected", [])

        # Verify Article IX evidence
        article_ix = evidence["article_ix"]
        assert "status" in article_ix
        assert "rationale" in article_ix
        assert article_ix["status"] in ("PASS", "FAIL")
        # Should detect contract decorators
        assert article_ix["contract_decorators"] > 0

    def test_constitution_check_in_generated_plan_md(self, real_codebase_repo: Path) -> None:
        """Test that constitution check is included in generated plan.md files."""
        # Analyze code to create plan bundle
        analyzer = CodeAnalyzer(
            repo_path=real_codebase_repo,
            confidence_threshold=0.5,
            entry_point=real_codebase_repo / "src",
        )
        plan_bundle = analyzer.analyze()

        # Convert to Spec-Kit
        converter = SpecKitConverter(real_codebase_repo)
        converter.convert_to_speckit(plan_bundle)

        # Check that plan.md files were generated with constitution check
        specs_dir = real_codebase_repo / "specs"
        if specs_dir.exists():
            for feature_dir in specs_dir.iterdir():
                if feature_dir.is_dir():
                    plan_file = feature_dir / "plan.md"
                    if plan_file.exists():
                        plan_content = plan_file.read_text(encoding="utf-8")
                        assert "## Constitution Check" in plan_content
                        assert "Article VII" in plan_content
                        assert "Article VIII" in plan_content
                        assert "Article IX" in plan_content
                        # Should have PASS/FAIL status, not PENDING
                        assert "**Status**: PASS" in plan_content or "**Status**: FAIL" in plan_content
                        assert "**Status**: PENDING" not in plan_content

    def test_constitution_evidence_no_pending_status(self, real_codebase_repo: Path) -> None:
        """Test that constitution evidence never returns PENDING status."""
        extractor = ConstitutionEvidenceExtractor(real_codebase_repo)
        evidence = extractor.extract_all_evidence()

        # Verify no PENDING status
        assert evidence["article_vii"]["status"] != "PENDING"
        assert evidence["article_viii"]["status"] != "PENDING"
        assert evidence["article_ix"]["status"] != "PENDING"

        # Generate constitution check section
        section = extractor.generate_constitution_check_section(evidence)
        assert "PENDING" not in section

    def test_constitution_evidence_with_contracts(self, real_codebase_repo: Path) -> None:
        """Test that Article IX detects contracts in the codebase."""
        extractor = ConstitutionEvidenceExtractor(real_codebase_repo)
        article_ix = extractor.extract_article_ix_evidence()

        # Should detect contract decorators from the test code
        assert article_ix["contract_decorators"] >= 2  # At least 2 functions with contracts
        assert article_ix["total_functions"] > 0

        # If contracts are found, status should likely be PASS
        if article_ix["contract_decorators"] > 0:
            # Status could be PASS or FAIL depending on coverage threshold
            assert article_ix["status"] in ("PASS", "FAIL")
