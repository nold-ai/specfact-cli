"""
Unit tests for feature validation in import command.

Tests the _validate_existing_features function and related validation logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.commands.import_cmd import _validate_existing_features
from specfact_cli.models.plan import Feature, PlanBundle, Product, SourceTracking, Story


@pytest.fixture
def sample_repo_path(tmp_path: Path) -> Path:
    """Create a sample repository with some files."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Create some source files
    (repo / "src").mkdir()
    (repo / "src" / "service.py").write_text("class Service: pass\n")
    (repo / "src" / "utils.py").write_text("def helper(): pass\n")

    # Create some test files
    (repo / "tests").mkdir()
    (repo / "tests" / "test_service.py").write_text("def test_service(): pass\n")

    return repo


@pytest.fixture
def valid_plan_bundle(sample_repo_path: Path) -> PlanBundle:
    """Create a plan bundle with valid features (all source files exist)."""
    return PlanBundle(
        version="1.0",
        product=Product(themes=["Testing"]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Valid Feature",
                outcomes=["Outcome 1"],
                acceptance=["AC 1"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Valid Story",
                        acceptance=["Story AC 1"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/service.py"],
                    test_files=["tests/test_service.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            )
        ],
        idea=None,
        business=None,
        metadata=None,
        clarifications=None,
    )


@pytest.fixture
def orphaned_plan_bundle(sample_repo_path: Path) -> PlanBundle:
    """Create a plan bundle with orphaned features (all source files missing)."""
    return PlanBundle(
        version="1.0",
        product=Product(themes=["Testing"]),
        features=[
            Feature(
                key="FEATURE-002",
                title="Orphaned Feature",
                outcomes=["Outcome 1"],
                acceptance=["AC 1"],
                stories=[
                    Story(
                        key="STORY-002",
                        title="Orphaned Story",
                        acceptance=["Story AC 1"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/nonexistent.py"],
                    test_files=["tests/nonexistent_test.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            )
        ],
        idea=None,
        business=None,
        metadata=None,
        clarifications=None,
    )


@pytest.fixture
def invalid_plan_bundle(sample_repo_path: Path) -> PlanBundle:
    """Create a plan bundle with invalid features (some files missing)."""
    return PlanBundle(
        version="1.0",
        product=Product(themes=["Testing"]),
        features=[
            Feature(
                key="FEATURE-003",
                title="Invalid Feature",
                outcomes=["Outcome 1"],
                acceptance=["AC 1"],
                stories=[
                    Story(
                        key="STORY-003",
                        title="Invalid Story",
                        acceptance=["Story AC 1"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/service.py", "src/missing.py"],
                    test_files=["tests/test_service.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            )
        ],
        idea=None,
        business=None,
        metadata=None,
        clarifications=None,
    )


@pytest.fixture
def mixed_plan_bundle(sample_repo_path: Path) -> PlanBundle:
    """Create a plan bundle with mixed valid, orphaned, and invalid features."""
    return PlanBundle(
        version="1.0",
        product=Product(themes=["Testing"]),
        features=[
            # Valid feature
            Feature(
                key="FEATURE-001",
                title="Valid Feature",
                outcomes=["Outcome 1"],
                acceptance=["AC 1"],
                stories=[
                    Story(
                        key="STORY-001",
                        title="Valid Story",
                        acceptance=["Story AC 1"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/service.py"],
                    test_files=["tests/test_service.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            ),
            # Orphaned feature
            Feature(
                key="FEATURE-002",
                title="Orphaned Feature",
                outcomes=["Outcome 2"],
                acceptance=["AC 2"],
                stories=[
                    Story(
                        key="STORY-002",
                        title="Orphaned Story",
                        acceptance=["Story AC 2"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/nonexistent.py"],
                    test_files=["tests/nonexistent_test.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            ),
            # Invalid feature (some files missing)
            Feature(
                key="FEATURE-003",
                title="Invalid Feature",
                outcomes=["Outcome 3"],
                acceptance=["AC 3"],
                stories=[
                    Story(
                        key="STORY-003",
                        title="Invalid Story",
                        acceptance=["Story AC 3"],
                        story_points=None,
                        value_points=None,
                        scenarios=None,
                        contracts=None,
                    )
                ],
                source_tracking=SourceTracking(
                    implementation_files=["src/service.py", "src/missing.py"],
                    test_files=["tests/test_service.py"],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            ),
            # Feature without source tracking
            Feature(
                key="FEATURE-004",
                title="No Source Tracking",
                outcomes=["Outcome 4"],
                acceptance=["AC 4"],
                stories=[],
                source_tracking=None,
                contract=None,
                protocol=None,
            ),
            # Feature with empty stories (structure issue)
            Feature(
                key="FEATURE-005",
                title="Empty Stories",
                outcomes=["Outcome 5"],
                acceptance=["AC 5"],
                stories=[],
                source_tracking=SourceTracking(
                    implementation_files=["src/service.py"],
                    test_files=[],
                    source_functions=[],
                    test_functions=[],
                ),
                contract=None,
                protocol=None,
            ),
        ],
        idea=None,
        business=None,
        metadata=None,
        clarifications=None,
    )


class TestValidateExistingFeatures:
    """Test suite for _validate_existing_features function."""

    def test_validate_all_valid_features(self, valid_plan_bundle: PlanBundle, sample_repo_path: Path) -> None:
        """Test validation with all valid features."""
        results = _validate_existing_features(valid_plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 1
        assert results["valid_features"] == ["FEATURE-001"]
        assert len(results["orphaned_features"]) == 0
        assert len(results["invalid_features"]) == 0
        assert len(results["missing_files"]) == 0

    def test_validate_orphaned_features(self, orphaned_plan_bundle: PlanBundle, sample_repo_path: Path) -> None:
        """Test validation with orphaned features (all files missing)."""
        results = _validate_existing_features(orphaned_plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 1
        assert results["orphaned_features"] == ["FEATURE-002"]
        assert len(results["invalid_features"]) == 0
        assert "FEATURE-002" in results["missing_files"]
        assert len(results["missing_files"]["FEATURE-002"]) == 2  # Both files missing

    def test_validate_invalid_features(self, invalid_plan_bundle: PlanBundle, sample_repo_path: Path) -> None:
        """Test validation with invalid features (some files missing)."""
        results = _validate_existing_features(invalid_plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 0
        assert len(results["invalid_features"]) == 1
        assert results["invalid_features"] == ["FEATURE-003"]
        assert "FEATURE-003" in results["missing_files"]
        assert len(results["missing_files"]["FEATURE-003"]) == 1  # One file missing
        assert "src/missing.py" in results["missing_files"]["FEATURE-003"]

    def test_validate_mixed_features(self, mixed_plan_bundle: PlanBundle, sample_repo_path: Path) -> None:
        """Test validation with mixed valid, orphaned, and invalid features."""
        results = _validate_existing_features(mixed_plan_bundle, sample_repo_path)

        assert results["total_checked"] == 5
        assert len(results["valid_features"]) == 1
        assert results["valid_features"] == ["FEATURE-001"]
        assert len(results["orphaned_features"]) == 1
        assert results["orphaned_features"] == ["FEATURE-002"]
        assert len(results["invalid_features"]) == 3  # FEATURE-003, FEATURE-004, FEATURE-005
        assert "FEATURE-003" in results["invalid_features"]
        assert "FEATURE-004" in results["invalid_features"]  # No source tracking
        assert "FEATURE-005" in results["invalid_features"]  # Empty stories

    def test_validate_feature_without_source_tracking(self, sample_repo_path: Path) -> None:
        """Test validation with feature that has no source tracking."""
        plan_bundle = PlanBundle(
            version="1.0",
            product=Product(themes=["Testing"]),
            features=[
                Feature(
                    key="FEATURE-006",
                    title="No Source Tracking",
                    outcomes=["Outcome 1"],
                    acceptance=["AC 1"],
                    stories=[
                        Story(
                            key="STORY-006",
                            title="Story",
                            acceptance=["Story AC 1"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        )
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        results = _validate_existing_features(plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 0
        assert len(results["invalid_features"]) == 1
        assert results["invalid_features"] == ["FEATURE-006"]

    def test_validate_feature_with_empty_stories(self, sample_repo_path: Path) -> None:
        """Test validation with feature that has empty stories."""
        plan_bundle = PlanBundle(
            version="1.0",
            product=Product(themes=["Testing"]),
            features=[
                Feature(
                    key="FEATURE-007",
                    title="Empty Stories",
                    outcomes=["Outcome 1"],
                    acceptance=["AC 1"],
                    stories=[],
                    source_tracking=SourceTracking(
                        implementation_files=["src/service.py"],
                        test_files=["tests/test_service.py"],
                        source_functions=[],
                        test_functions=[],
                    ),
                    contract=None,
                    protocol=None,
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        results = _validate_existing_features(plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 0
        assert len(results["invalid_features"]) == 1
        assert results["invalid_features"] == ["FEATURE-007"]

    def test_validate_feature_with_partial_files(self, sample_repo_path: Path) -> None:
        """Test validation with feature that has some existing and some missing files."""
        plan_bundle = PlanBundle(
            version="1.0",
            product=Product(themes=["Testing"]),
            features=[
                Feature(
                    key="FEATURE-008",
                    title="Partial Files",
                    outcomes=["Outcome 1"],
                    acceptance=["AC 1"],
                    stories=[
                        Story(
                            key="STORY-008",
                            title="Story",
                            acceptance=["Story AC 1"],
                            story_points=None,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        )
                    ],
                    source_tracking=SourceTracking(
                        implementation_files=["src/service.py", "src/missing.py"],
                        test_files=["tests/test_service.py"],
                        source_functions=[],
                        test_functions=[],
                    ),
                    contract=None,
                    protocol=None,
                )
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        results = _validate_existing_features(plan_bundle, sample_repo_path)

        assert results["total_checked"] == 1
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 0  # Not orphaned because some files exist
        assert len(results["invalid_features"]) == 1
        assert results["invalid_features"] == ["FEATURE-008"]
        assert "FEATURE-008" in results["missing_files"]
        assert "src/missing.py" in results["missing_files"]["FEATURE-008"]

    def test_validate_empty_bundle(self, sample_repo_path: Path) -> None:
        """Test validation with empty bundle."""
        plan_bundle = PlanBundle(
            version="1.0",
            product=Product(themes=[]),
            features=[],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        results = _validate_existing_features(plan_bundle, sample_repo_path)

        assert results["total_checked"] == 0
        assert len(results["valid_features"]) == 0
        assert len(results["orphaned_features"]) == 0
        assert len(results["invalid_features"]) == 0
        assert len(results["missing_files"]) == 0
