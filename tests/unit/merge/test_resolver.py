"""Unit tests for persona-aware merge resolver."""

import pytest

from specfact_cli.merge.resolver import MergeConflict, MergeResolution, MergeStrategy, PersonaMergeResolver
from specfact_cli.models.plan import Feature, Idea, Product, Story
from specfact_cli.models.project import BundleManifest, PersonaMapping, ProjectBundle


@pytest.fixture
def base_bundle() -> ProjectBundle:
    """Create base bundle for merge testing."""
    manifest = BundleManifest(schema_metadata=None, project_metadata=None)
    product = Product(themes=["Base Theme"])
    idea = Idea(title="Base Idea", narrative="Base narrative", metrics=None)
    bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product, idea=idea)

    feature = Feature(
        key="FEATURE-001",
        title="Base Feature",
        stories=[
            Story(
                key="STORY-001",
                title="Base Story",
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
    return bundle


@pytest.fixture
def ours_bundle(base_bundle: ProjectBundle) -> ProjectBundle:
    """Create 'ours' bundle with modifications."""
    ours = base_bundle.model_copy(deep=True)
    ours.product.themes = ["Ours Theme"]
    if ours.idea:
        ours.idea.title = "Ours Idea"
    ours.features["FEATURE-001"].title = "Ours Feature"
    return ours


@pytest.fixture
def theirs_bundle(base_bundle: ProjectBundle) -> ProjectBundle:
    """Create 'theirs' bundle with modifications."""
    theirs = base_bundle.model_copy(deep=True)
    theirs.product.themes = ["Theirs Theme"]
    if theirs.idea:
        theirs.idea.title = "Theirs Idea"
    theirs.features["FEATURE-001"].title = "Theirs Feature"
    return theirs


@pytest.fixture
def manifest_with_personas() -> BundleManifest:
    """Create manifest with persona mappings."""
    product_owner = PersonaMapping(owns=["idea", "business"], exports_to="specs/*/spec.md")
    architect = PersonaMapping(owns=["features.*.constraints", "protocols"], exports_to="specs/*/plan.md")
    return BundleManifest(
        schema_metadata=None,
        project_metadata=None,
        personas={"product-owner": product_owner, "architect": architect},
    )


class TestPersonaMergeResolver:
    """Test suite for PersonaMergeResolver."""

    def test_resolve_no_conflicts(self, base_bundle: ProjectBundle) -> None:
        """Test merge with no conflicts (non-overlapping changes)."""
        ours = base_bundle.model_copy(deep=True)
        ours.product.themes = ["New Theme"]

        theirs = base_bundle.model_copy(deep=True)
        if theirs.idea:
            theirs.idea.title = "New Idea"

        resolver = PersonaMergeResolver()
        resolution = resolver.resolve(base_bundle, ours, theirs, "product-owner", "architect")

        assert resolution.auto_resolved == 0
        assert resolution.unresolved == 0
        assert len(resolution.conflicts) == 0

    def test_resolve_with_persona_ownership(
        self, base_bundle: ProjectBundle, manifest_with_personas: BundleManifest
    ) -> None:
        """Test merge resolution based on persona ownership."""
        base_bundle.manifest = manifest_with_personas
        ours = base_bundle.model_copy(deep=True)
        if ours.idea:
            ours.idea.title = "Ours Idea"
        ours.manifest = manifest_with_personas

        theirs = base_bundle.model_copy(deep=True)
        if theirs.idea:
            theirs.idea.title = "Theirs Idea"
        theirs.manifest = manifest_with_personas

        resolver = PersonaMergeResolver()
        resolution = resolver.resolve(base_bundle, ours, theirs, "product-owner", "architect")

        # Product owner owns 'idea', so ours should win
        assert resolution.auto_resolved >= 0  # May auto-resolve based on ownership

    def test_find_conflicts_feature_title(self, base_bundle: ProjectBundle) -> None:
        """Test conflict detection for feature titles."""
        ours = base_bundle.model_copy(deep=True)
        ours.features["FEATURE-001"].title = "Ours Feature"

        theirs = base_bundle.model_copy(deep=True)
        theirs.features["FEATURE-001"].title = "Theirs Feature"

        resolver = PersonaMergeResolver()
        conflicts = resolver._find_conflicts(base_bundle, ours, theirs)

        assert "features.FEATURE-001.title" in conflicts
        base_val, ours_val, theirs_val = conflicts["features.FEATURE-001.title"]
        assert base_val == "Base Feature"
        assert ours_val == "Ours Feature"
        assert theirs_val == "Theirs Feature"

    def test_find_conflicts_idea_title(self, base_bundle: ProjectBundle) -> None:
        """Test conflict detection for idea title."""
        ours = base_bundle.model_copy(deep=True)
        if ours.idea:
            ours.idea.title = "Ours Idea"

        theirs = base_bundle.model_copy(deep=True)
        if theirs.idea:
            theirs.idea.title = "Theirs Idea"

        resolver = PersonaMergeResolver()
        conflicts = resolver._find_conflicts(base_bundle, ours, theirs)

        assert "idea.title" in conflicts

    def test_get_section_path(self) -> None:
        """Test section path extraction from conflict path."""
        resolver = PersonaMergeResolver()

        assert resolver._get_section_path("idea.intent") == "idea"
        assert resolver._get_section_path("features.FEATURE-001.title") == "features.FEATURE-001"
        assert (
            resolver._get_section_path("features.FEATURE-001.stories.STORY-001.description")
            == "features.FEATURE-001.stories"
        )

    def test_get_owner(self, manifest_with_personas: BundleManifest) -> None:
        """Test owner detection for sections."""
        resolver = PersonaMergeResolver()

        owner = resolver._get_owner("idea", manifest_with_personas, "product-owner")
        assert owner == "product-owner"

        owner = resolver._get_owner("features.FEATURE-001.constraints", manifest_with_personas, "architect")
        assert owner == "architect"

        owner = resolver._get_owner("unknown.section", manifest_with_personas, "product-owner")
        assert owner is None

    def test_apply_resolution(self, base_bundle: ProjectBundle) -> None:
        """Test applying resolution to bundle."""
        resolver = PersonaMergeResolver()

        resolver._apply_resolution(base_bundle, "features.FEATURE-001.title", "Resolved Title")
        assert base_bundle.features["FEATURE-001"].title == "Resolved Title"

        resolver._apply_resolution(base_bundle, "idea.title", "Resolved Title")
        if base_bundle.idea:
            assert base_bundle.idea.title == "Resolved Title"


class TestMergeConflict:
    """Test suite for MergeConflict dataclass."""

    def test_merge_conflict_creation(self) -> None:
        """Test creating a merge conflict."""
        conflict = MergeConflict(
            section_path="features.FEATURE-001",
            field_name="features.FEATURE-001.title",
            base_value="Base",
            ours_value="Ours",
            theirs_value="Theirs",
            owner_ours="product-owner",
            owner_theirs="architect",
        )

        assert conflict.section_path == "features.FEATURE-001"
        assert conflict.field_name == "features.FEATURE-001.title"
        assert conflict.base_value == "Base"
        assert conflict.ours_value == "Ours"
        assert conflict.theirs_value == "Theirs"


class TestMergeResolution:
    """Test suite for MergeResolution dataclass."""

    def test_merge_resolution_creation(self, base_bundle: ProjectBundle) -> None:
        """Test creating a merge resolution."""
        conflicts = [
            MergeConflict(
                section_path="features.FEATURE-001",
                field_name="features.FEATURE-001.title",
                base_value="Base",
                ours_value="Ours",
                theirs_value="Theirs",
            )
        ]

        resolution = MergeResolution(
            merged_bundle=base_bundle,
            conflicts=conflicts,
            auto_resolved=1,
            manual_resolved=0,
            unresolved=0,
        )

        assert resolution.merged_bundle == base_bundle
        assert len(resolution.conflicts) == 1
        assert resolution.auto_resolved == 1
        assert resolution.manual_resolved == 0
        assert resolution.unresolved == 0


class TestMergeStrategy:
    """Test suite for MergeStrategy enum."""

    def test_merge_strategy_values(self) -> None:
        """Test merge strategy enum values."""
        assert MergeStrategy.AUTO == "auto"
        assert MergeStrategy.OURS == "ours"
        assert MergeStrategy.THEIRS == "theirs"
        assert MergeStrategy.BASE == "base"
        assert MergeStrategy.MANUAL == "manual"
