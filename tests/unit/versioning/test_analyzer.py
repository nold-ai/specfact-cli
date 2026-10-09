"""Unit tests for version change analyzer."""

from pathlib import Path

import yaml
from git import Repo

from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.utils.bundle_loader import save_project_bundle
from specfact_cli.versioning import ChangeAnalyzer, ChangeType


def _create_sample_bundle(base_path: Path, bundle_name: str = "test-bundle") -> Path:
    projects_dir = base_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = projects_dir / bundle_name

    manifest = BundleManifest(schema_metadata=None, project_metadata=None)
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Story Title",
                acceptance=["Given ..."],
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
    bundle.add_feature(feature)

    save_project_bundle(bundle, bundle_dir, atomic=True)
    return bundle_dir


def _init_repo(base_path: Path) -> Repo:
    repo = Repo.init(base_path)
    repo.index.add([str(p) for p in base_path.rglob("*") if p.is_file()])
    repo.index.commit("init")
    return repo


class TestChangeAnalyzer:
    """Change detection scenarios."""

    def test_detects_patch_changes(self, tmp_path: Path) -> None:
        bundle_dir = _create_sample_bundle(tmp_path)
        _init_repo(tmp_path)

        feature_path = bundle_dir / "features" / "FEATURE-001.yaml"
        feature_data = yaml.safe_load(feature_path.read_text())
        feature_data["title"] = "Updated Feature"
        feature_path.write_text(yaml.safe_dump(feature_data))

        analysis = ChangeAnalyzer(repo_path=tmp_path).analyze(bundle_dir)

        assert analysis.change_type == ChangeType.PATCH
        assert analysis.recommended_bump == "patch"
        assert any("FEATURE-001.yaml" in path for path in analysis.changed_files)

    def test_detects_additive_changes(self, tmp_path: Path) -> None:
        bundle_dir = _create_sample_bundle(tmp_path)
        _init_repo(tmp_path)

        bundle = ProjectBundle.load_from_directory(bundle_dir)
        new_feature = Feature(
            key="FEATURE-002",
            title="New Feature",
            outcomes=["Outcome"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        bundle.add_feature(new_feature)
        save_project_bundle(bundle, bundle_dir, atomic=True)

        analysis = ChangeAnalyzer(repo_path=tmp_path).analyze(bundle_dir)

        assert analysis.change_type == ChangeType.ADDITIVE
        assert analysis.recommended_bump == "minor"
        assert any("FEATURE-002.yaml" in path for path in analysis.changed_files)

    def test_detects_breaking_changes(self, tmp_path: Path) -> None:
        bundle_dir = _create_sample_bundle(tmp_path)
        _init_repo(tmp_path)

        bundle = ProjectBundle.load_from_directory(bundle_dir)
        # Remove feature to force deletion in saved bundle
        bundle.features.pop("FEATURE-001", None)
        save_project_bundle(bundle, bundle_dir, atomic=True)

        analysis = ChangeAnalyzer(repo_path=tmp_path).analyze(bundle_dir)

        assert analysis.change_type == ChangeType.BREAKING
        assert analysis.recommended_bump == "major"
        assert any("FEATURE-001.yaml" in path for path in analysis.changed_files)
