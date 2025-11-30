"""Unit tests for PlanComparator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from specfact_cli.comparators.plan_comparator import PlanComparator
from specfact_cli.models.deviation import DeviationSeverity, DeviationType
from specfact_cli.models.plan import Business, Feature, Idea, PlanBundle, Product, Story


class TestPlanComparator:
    """Test suite for PlanComparator."""

    def test_identical_plans_no_deviations(self):
        """Test that identical plans produce no deviations."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=["AI"], releases=[])
        feature = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        plan1 = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature],
            metadata=None,
            clarifications=None,
        )

        plan2 = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(plan1, plan2)

        assert report.total_deviations == 0
        assert len(report.deviations) == 0

    def test_missing_feature_in_auto_plan(self):
        """Test detection of feature missing in auto-derived plan."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["View metrics"],
            acceptance=["Dashboard loads"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1, feature2],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations == 1
        assert report.deviations[0].type == DeviationType.MISSING_FEATURE
        # Feature with no stories gets MEDIUM severity
        assert report.deviations[0].severity == DeviationSeverity.MEDIUM
        assert "FEATURE-002" in report.deviations[0].description

    def test_extra_feature_in_auto_plan(self):
        """Test detection of extra feature in auto-derived plan."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["View metrics"],
            acceptance=["Dashboard loads"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1, feature2],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations == 1
        assert report.deviations[0].type == DeviationType.EXTRA_IMPLEMENTATION
        # Feature with default confidence (1.0) >= 0.8 gets HIGH severity
        assert report.deviations[0].severity == DeviationSeverity.HIGH
        assert "FEATURE-002" in report.deviations[0].description

    def test_modified_feature_title(self):
        """Test detection of modified feature title."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature_manual = Feature(
            key="FEATURE-001",
            title="User Authentication",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature_auto = Feature(
            key="FEATURE-001",
            title="User Auth",  # Different title
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature_manual],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature_auto],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations == 1
        assert report.deviations[0].type == DeviationType.MISMATCH
        assert report.deviations[0].severity == DeviationSeverity.LOW
        assert "title" in report.deviations[0].description.lower()

    def test_missing_story_in_feature(self):
        """Test detection of missing story in feature."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        story1 = Story(
            key="STORY-001",
            title="Login API",
            acceptance=["API works"],
            story_points=None,
            value_points=None,
            scenarios=None,
            contracts=None,
        )
        story2 = Story(
            key="STORY-002",
            title="Login UI",
            acceptance=["UI works"],
            story_points=None,
            value_points=None,
            scenarios=None,
            contracts=None,
        )

        feature_manual = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[story1, story2],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature_auto = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[story1],  # Missing story2
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature_manual],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature_auto],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations == 1
        assert report.deviations[0].type == DeviationType.MISSING_STORY
        # Story with no value_points or draft=True gets MEDIUM severity
        # Story with draft=False gets HIGH severity
        assert report.deviations[0].severity in (DeviationSeverity.MEDIUM, DeviationSeverity.HIGH)
        assert "STORY-002" in report.deviations[0].description

    def test_idea_mismatch(self):
        """Test detection of idea differences."""
        idea1 = Idea(title="Project A", narrative="Build something", metrics=None)
        idea2 = Idea(title="Project B", narrative="Build something else", metrics=None)

        product = Product(themes=[], releases=[])

        manual_plan = PlanBundle(
            version="1.0", idea=idea1, business=None, product=product, features=[], metadata=None, clarifications=None
        )

        auto_plan = PlanBundle(
            version="1.0", idea=idea2, business=None, product=product, features=[], metadata=None, clarifications=None
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations >= 1
        assert any(d.type == DeviationType.MISMATCH for d in report.deviations)
        assert any("idea" in d.description.lower() or "title" in d.description.lower() for d in report.deviations)

    def test_product_theme_differences(self):
        """Test detection of product theme differences."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)

        product1 = Product(themes=["AI", "Security"], releases=[])
        product2 = Product(themes=["AI", "Performance"], releases=[])

        manual_plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product1, features=[], metadata=None, clarifications=None
        )

        auto_plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product2, features=[], metadata=None, clarifications=None
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations >= 1
        assert any("theme" in d.description.lower() for d in report.deviations)

    def test_business_context_missing(self):
        """Test detection of missing business context."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])
        business = Business(
            segments=["Enterprise"],
            problems=["Slow deployment"],
            solutions=["Automation"],
            differentiation=["AI-powered"],
            risks=["Competition"],
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=business,
            product=product,
            features=[],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product, features=[], metadata=None, clarifications=None
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        assert report.total_deviations >= 1
        assert any(d.type == DeviationType.MISSING_BUSINESS_CONTEXT for d in report.deviations)

    def test_compare_with_custom_labels(self):
        """Test comparison with custom plan labels."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        manual_plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product, features=[], metadata=None, clarifications=None
        )

        auto_plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product, features=[], metadata=None, clarifications=None
        )

        comparator = PlanComparator()
        report = comparator.compare(
            manual_plan,
            auto_plan,
            manual_label=".specfact/plans/main.bundle.yaml",
            auto_label=".specfact/plans/auto-derived.bundle.yaml",
        )

        assert report.manual_plan == ".specfact/plans/main.bundle.yaml"
        assert report.auto_plan == ".specfact/plans/auto-derived.bundle.yaml"

    def test_multiple_deviation_types(self):
        """Test detection of multiple deviation types in one comparison."""
        idea1 = Idea(title="Project A", narrative="Original", metrics=None)
        idea2 = Idea(title="Project B", narrative="Modified", metrics=None)

        product1 = Product(themes=["AI"], releases=[])
        product2 = Product(themes=["ML"], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="Auth",
            outcomes=["Login"],
            acceptance=["Works"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["Metrics"],
            acceptance=["Loads"],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea1,
            business=None,
            product=product1,
            features=[feature1],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea2,
            business=None,
            product=product2,
            features=[feature1, feature2],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        # Should detect: idea mismatch, theme mismatch, extra feature
        assert report.total_deviations >= 3
        deviation_types = {d.type for d in report.deviations}
        assert DeviationType.MISMATCH in deviation_types
        assert DeviationType.EXTRA_IMPLEMENTATION in deviation_types

    def test_severity_counts(self):
        """Test that severity counts are calculated correctly."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="Auth",
            outcomes=[],
            acceptance=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=[],
            acceptance=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        feature3 = Feature(
            key="FEATURE-003",
            title="Reports",
            outcomes=[],
            acceptance=[],
            stories=[],
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        manual_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1],
            metadata=None,
            clarifications=None,
        )

        auto_plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature1, feature2, feature3],
            metadata=None,
            clarifications=None,
        )

        comparator = PlanComparator()
        report = comparator.compare(manual_plan, auto_plan)

        # Features with no stories get MEDIUM severity, but default confidence (1.0) >= 0.8 gives HIGH
        # Since these features have empty stories and confidence defaults to 1.0, they get HIGH severity
        assert report.high_count == 2
        assert report.medium_count == 0
        assert report.low_count == 0
