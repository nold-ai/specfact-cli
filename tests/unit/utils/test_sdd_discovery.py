"""
Unit tests for SDD discovery utilities.
"""

from pathlib import Path

import pytest

from specfact_cli.models.sdd import (
    SDDCoverageThresholds,
    SDDEnforcementBudget,
    SDDHow,
    SDDManifest,
    SDDWhat,
    SDDWhy,
)
from specfact_cli.utils.sdd_discovery import (
    find_sdd_for_bundle,
    get_default_sdd_path_for_bundle,
    get_sdd_by_hash,
    list_all_sdds,
)


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository structure."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".specfact").mkdir()
    (repo / ".specfact" / "sdd").mkdir()
    return repo


@pytest.fixture
def sample_sdd_manifest() -> SDDManifest:
    """Create a sample SDD manifest for testing."""
    return SDDManifest(
        version="1.0.0",
        plan_bundle_id="test-bundle-id",
        plan_bundle_hash="test-hash-1234567890abcdef",
        why=SDDWhy(intent="Test intent", constraints=["Constraint 1"], target_users=None, value_hypothesis=None),
        what=SDDWhat(capabilities=["Capability 1"], acceptance_criteria=["AC 1"]),
        how=SDDHow(architecture="Test architecture", invariants=["Invariant 1"], contracts=["Contract 1"]),
        coverage_thresholds=SDDCoverageThresholds(
            contracts_per_story=1.0, invariants_per_feature=1.0, architecture_facets=3
        ),
        enforcement_budget=SDDEnforcementBudget(
            shadow_budget_seconds=300, warn_budget_seconds=180, block_budget_seconds=90
        ),
        promotion_status="draft",
    )


def test_find_sdd_for_bundle_multi_sdd_yaml(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD in multi-SDD layout (YAML)."""
    import yaml

    bundle_name = "test-bundle"
    sdd_path = temp_repo / ".specfact" / "sdd" / f"{bundle_name}.yaml"
    sdd_path.write_text(yaml.dump(sample_sdd_manifest.model_dump(exclude_none=True)))

    result = find_sdd_for_bundle(bundle_name, temp_repo)
    assert result is not None
    assert result == sdd_path.resolve()


def test_find_sdd_for_bundle_multi_sdd_json(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD in multi-SDD layout (JSON)."""
    import json

    bundle_name = "test-bundle"
    sdd_path = temp_repo / ".specfact" / "sdd" / f"{bundle_name}.json"
    sdd_path.write_text(json.dumps(sample_sdd_manifest.model_dump(exclude_none=True), indent=2))

    result = find_sdd_for_bundle(bundle_name, temp_repo)
    assert result is not None
    assert result == sdd_path.resolve()


def test_find_sdd_for_bundle_legacy_single_sdd_yaml(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD in legacy single-SDD layout (YAML)."""
    import yaml

    bundle_name = "test-bundle"
    sdd_path = temp_repo / ".specfact" / "sdd.yaml"
    sdd_path.write_text(yaml.dump(sample_sdd_manifest.model_dump(exclude_none=True)))

    result = find_sdd_for_bundle(bundle_name, temp_repo)
    assert result is not None
    assert result == sdd_path.resolve()


def test_find_sdd_for_bundle_not_found(temp_repo: Path) -> None:
    """Test finding SDD when none exists."""
    bundle_name = "nonexistent-bundle"
    result = find_sdd_for_bundle(bundle_name, temp_repo)
    assert result is None


def test_find_sdd_for_bundle_explicit_path(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD with explicit path."""
    import yaml

    bundle_name = "test-bundle"
    explicit_path = temp_repo / "custom" / "sdd.yaml"
    explicit_path.parent.mkdir(parents=True)
    explicit_path.write_text(yaml.dump(sample_sdd_manifest.model_dump(exclude_none=True)))

    result = find_sdd_for_bundle(bundle_name, temp_repo, explicit_path)
    assert result is not None
    assert result == explicit_path.resolve()


def test_list_all_sdds_multi_sdd(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test listing all SDDs in multi-SDD layout."""
    import yaml

    # Create multiple SDD manifests
    bundle1_path = temp_repo / ".specfact" / "sdd" / "bundle1.yaml"
    bundle2_path = temp_repo / ".specfact" / "sdd" / "bundle2.yaml"

    manifest1 = sample_sdd_manifest.model_copy(update={"plan_bundle_hash": "hash1"})
    manifest2 = sample_sdd_manifest.model_copy(update={"plan_bundle_hash": "hash2"})

    bundle1_path.write_text(yaml.dump(manifest1.model_dump(exclude_none=True)))
    bundle2_path.write_text(yaml.dump(manifest2.model_dump(exclude_none=True)))

    results = list_all_sdds(temp_repo)
    assert len(results) == 2

    paths = [path for path, _ in results]
    assert bundle1_path.resolve() in paths
    assert bundle2_path.resolve() in paths


def test_list_all_sdds_legacy_single_sdd(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test listing SDD in legacy single-SDD layout."""
    import yaml

    sdd_path = temp_repo / ".specfact" / "sdd.yaml"
    sdd_path.write_text(yaml.dump(sample_sdd_manifest.model_dump(exclude_none=True)))

    results = list_all_sdds(temp_repo)
    assert len(results) == 1
    assert results[0][0] == sdd_path.resolve()


def test_list_all_sdds_empty(temp_repo: Path) -> None:
    """Test listing SDDs when none exist."""
    results = list_all_sdds(temp_repo)
    assert len(results) == 0


def test_get_sdd_by_hash(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD by hash."""
    import yaml

    target_hash = "target-hash-1234567890abcdef"
    manifest = sample_sdd_manifest.model_copy(update={"plan_bundle_hash": target_hash})

    sdd_path = temp_repo / ".specfact" / "sdd" / "test-bundle.yaml"
    sdd_path.write_text(yaml.dump(manifest.model_dump(exclude_none=True)))

    result = get_sdd_by_hash(target_hash, temp_repo)
    assert result is not None
    assert result == sdd_path.resolve()


def test_get_sdd_by_hash_not_found(temp_repo: Path, sample_sdd_manifest: SDDManifest) -> None:
    """Test finding SDD by hash when hash doesn't match."""
    import yaml

    sdd_path = temp_repo / ".specfact" / "sdd" / "test-bundle.yaml"
    sdd_path.write_text(yaml.dump(sample_sdd_manifest.model_dump(exclude_none=True)))

    result = get_sdd_by_hash("nonexistent-hash", temp_repo)
    assert result is None


def test_get_default_sdd_path_for_bundle_yaml(temp_repo: Path) -> None:
    """Test getting default SDD path for bundle (YAML)."""
    bundle_name = "test-bundle"
    result = get_default_sdd_path_for_bundle(bundle_name, temp_repo, "yaml")
    expected = temp_repo / ".specfact" / "sdd" / "test-bundle.yaml"
    assert result == expected


def test_get_default_sdd_path_for_bundle_json(temp_repo: Path) -> None:
    """Test getting default SDD path for bundle (JSON)."""
    bundle_name = "test-bundle"
    result = get_default_sdd_path_for_bundle(bundle_name, temp_repo, "json")
    expected = temp_repo / ".specfact" / "sdd" / "test-bundle.json"
    assert result == expected
