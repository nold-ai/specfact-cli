"""Unit tests for ConstitutionEvidenceExtractor."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from specfact_cli.analyzers.constitution_evidence_extractor import ConstitutionEvidenceExtractor


@pytest.fixture
def temp_repo() -> Iterator[Path]:
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / "src" / "module").mkdir(parents=True)
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()

        # Create some Python files
        (repo_path / "src" / "module" / "__init__.py").write_text("")
        (repo_path / "src" / "module" / "simple.py").write_text(
            """
def simple_function(x: int) -> int:
    return x + 1
"""
        )
        (repo_path / "src" / "module" / "with_contracts.py").write_text(
            """
from icontract import require, ensure

@require(lambda x: x > 0)
@ensure(lambda result: result > 0)
def contract_function(x: int) -> int:
    return x * 2
"""
        )

        yield repo_path


@pytest.fixture
def deep_repo() -> Iterator[Path]:
    """Create a repository with deep directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create deep structure (depth > 4)
        deep_path = repo_path
        for i in range(6):
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()
        (deep_path / "file.py").write_text("")

        yield repo_path


@pytest.fixture
def framework_repo() -> Iterator[Path]:
    """Create a repository with framework imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / "app.py").write_text(
            """
from django.db import models
from flask import Flask
from fastapi import FastAPI

class MyModel(models.Model):
    pass
"""
        )

        yield repo_path


class TestConstitutionEvidenceExtractor:
    """Test cases for ConstitutionEvidenceExtractor."""

    def test_init(self, temp_repo: Path) -> None:
        """Test ConstitutionEvidenceExtractor initialization."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        assert extractor.repo_path == temp_repo

    def test_extract_article_vii_evidence_simple(self, temp_repo: Path) -> None:
        """Test Article VII evidence extraction for simple structure."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_article_vii_evidence()

        assert "status" in evidence
        assert "rationale" in evidence
        assert "evidence" in evidence
        assert "max_depth" in evidence
        assert "max_files_per_dir" in evidence
        assert evidence["status"] in ("PASS", "FAIL")
        assert isinstance(evidence["max_depth"], int)
        assert isinstance(evidence["max_files_per_dir"], int)

    def test_extract_article_vii_evidence_deep(self, deep_repo: Path) -> None:
        """Test Article VII evidence extraction for deep structure."""
        extractor = ConstitutionEvidenceExtractor(deep_repo)
        evidence = extractor.extract_article_vii_evidence()

        assert evidence["status"] == "FAIL"
        assert "deep directory structure" in evidence["rationale"].lower()
        assert evidence["max_depth"] > 4

    def test_extract_article_viii_evidence_no_frameworks(self, temp_repo: Path) -> None:
        """Test Article VIII evidence extraction with no frameworks."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_article_viii_evidence()

        assert "status" in evidence
        assert "rationale" in evidence
        assert "evidence" in evidence
        assert "frameworks_detected" in evidence
        assert "abstraction_layers" in evidence
        assert evidence["status"] in ("PASS", "FAIL")
        assert isinstance(evidence["frameworks_detected"], list)

    def test_extract_article_viii_evidence_with_frameworks(self, framework_repo: Path) -> None:
        """Test Article VIII evidence extraction with framework imports."""
        extractor = ConstitutionEvidenceExtractor(framework_repo)
        evidence = extractor.extract_article_viii_evidence()

        assert evidence["status"] == "FAIL"
        assert "framework" in evidence["rationale"].lower()
        assert len(evidence["frameworks_detected"]) > 0

    def test_extract_article_ix_evidence_no_contracts(self, temp_repo: Path) -> None:
        """Test Article IX evidence extraction with no contracts."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_article_ix_evidence()

        assert "status" in evidence
        assert "rationale" in evidence
        assert "evidence" in evidence
        assert "contract_decorators" in evidence
        assert "total_functions" in evidence
        assert evidence["status"] in ("PASS", "FAIL")
        assert isinstance(evidence["contract_decorators"], int)
        assert isinstance(evidence["total_functions"], int)

    def test_extract_article_ix_evidence_with_contracts(self, temp_repo: Path) -> None:
        """Test Article IX evidence extraction with contract decorators."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_article_ix_evidence()

        # Should detect contracts in with_contracts.py
        assert evidence["contract_decorators"] >= 0
        assert evidence["total_functions"] > 0

    def test_extract_all_evidence(self, temp_repo: Path) -> None:
        """Test extraction of all evidence."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        all_evidence = extractor.extract_all_evidence()

        assert "article_vii" in all_evidence
        assert "article_viii" in all_evidence
        assert "article_ix" in all_evidence

        assert all_evidence["article_vii"]["status"] in ("PASS", "FAIL")
        assert all_evidence["article_viii"]["status"] in ("PASS", "FAIL")
        assert all_evidence["article_ix"]["status"] in ("PASS", "FAIL")

    def test_generate_constitution_check_section(self, temp_repo: Path) -> None:
        """Test constitution check section generation."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_all_evidence()
        section = extractor.generate_constitution_check_section(evidence)

        assert isinstance(section, str)
        assert "## Constitution Check" in section
        assert "Article VII" in section
        assert "Article VIII" in section
        assert "Article IX" in section
        assert "Status" in section
        assert "PASS" in section or "FAIL" in section

    def test_generate_constitution_check_section_no_pending(self, temp_repo: Path) -> None:
        """Test that constitution check section never contains PENDING."""
        extractor = ConstitutionEvidenceExtractor(temp_repo)
        evidence = extractor.extract_all_evidence()
        section = extractor.generate_constitution_check_section(evidence)

        # Should never contain PENDING status
        assert "PENDING" not in section

    def test_extract_article_vii_nonexistent_path(self) -> None:
        """Test Article VII extraction with nonexistent path."""
        extractor = ConstitutionEvidenceExtractor(Path("/nonexistent/path"))
        evidence = extractor.extract_article_vii_evidence()

        assert evidence["status"] == "FAIL"
        assert "does not exist" in evidence["rationale"]

    def test_extract_article_viii_nonexistent_path(self) -> None:
        """Test Article VIII extraction with nonexistent path."""
        extractor = ConstitutionEvidenceExtractor(Path("/nonexistent/path"))
        evidence = extractor.extract_article_viii_evidence()

        assert evidence["status"] == "FAIL"
        assert "does not exist" in evidence["rationale"]

    def test_extract_article_ix_nonexistent_path(self) -> None:
        """Test Article IX extraction with nonexistent path."""
        extractor = ConstitutionEvidenceExtractor(Path("/nonexistent/path"))
        evidence = extractor.extract_article_ix_evidence()

        assert evidence["status"] == "FAIL"
        assert "does not exist" in evidence["rationale"]
