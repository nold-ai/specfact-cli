"""Integration tests for plan compare command."""

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Story
from specfact_cli.utils.yaml_utils import dump_yaml


runner = CliRunner()


@pytest.fixture
def tmp_plans(tmp_path):
    """Create temporary plan files for testing."""
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    return plans_dir


class TestPlanCompareCommand:
    """Test suite for plan compare command."""

    def test_compare_identical_plans(self, tmp_plans):
        """Test comparing identical plans produces no deviations."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=["AI"], releases=[])
        feature = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
        )

        plan = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[feature],
            metadata=None,
            clarifications=None,
        )

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0
        assert "No deviations found" in result.stdout
        assert "Plans are identical" in result.stdout

    def test_compare_with_missing_feature(self, tmp_plans):
        """Test detecting missing feature in auto plan."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["View metrics"],
            acceptance=["Dashboard loads"],
            stories=[],
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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert "1 deviation(s) found" in result.stdout
        assert "FEATURE-002" in result.stdout
        assert "HIGH" in result.stdout

    def test_compare_code_vs_plan_alias(self, tmp_plans):
        """Test --code-vs-plan convenience alias for code vs plan drift detection."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["View metrics"],
            acceptance=["Dashboard loads"],
            stories=[],
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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--code-vs-plan", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert "Code vs Plan Drift Detection" in result.stdout
        assert "intended design" in result.stdout.lower()
        assert "actual implementation" in result.stdout.lower()
        assert "1 deviation(s) found" in result.stdout
        assert "FEATURE-002" in result.stdout

    def test_compare_with_extra_feature(self, tmp_plans):
        """Test detecting extra feature in auto plan."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[],
        )

        feature2 = Feature(
            key="FEATURE-002",
            title="Dashboard",
            outcomes=["View metrics"],
            acceptance=["Dashboard loads"],
            stories=[],
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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert "1 deviation(s) found" in result.stdout
        assert "FEATURE-002" in result.stdout
        assert "MEDIUM" in result.stdout

    def test_compare_with_missing_story(self, tmp_plans):
        """Test detecting missing story in feature."""
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
        )

        feature_auto = Feature(
            key="FEATURE-001",
            title="User Auth",
            outcomes=["Secure login"],
            acceptance=["Login works"],
            stories=[story1],
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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert "1 deviation(s) found" in result.stdout
        assert "STORY-002" in result.stdout

    def test_compare_with_markdown_output(self, tmp_plans):
        """Test generating markdown report."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(key="FEATURE-001", title="Auth", outcomes=[], acceptance=[], stories=[])
        feature2 = Feature(key="FEATURE-002", title="Dashboard", outcomes=[], acceptance=[], stories=[])

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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"
        report_path = tmp_plans / "report.md"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            [
                "plan",
                "compare",
                "--manual",
                str(manual_path),
                "--auto",
                str(auto_path),
                "--output-format",
                "markdown",
                "--out",
                str(report_path),
            ],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert report_path.exists()
        assert "Report written to" in result.stdout

        # Verify report content
        content = report_path.read_text()
        assert "# Deviation Report" in content
        assert "FEATURE-002" in content

    def test_compare_with_json_output(self, tmp_plans):
        """Test generating JSON report."""
        idea = Idea(title="Test Project", narrative="A test project", metrics=None)
        product = Product(themes=[], releases=[])

        feature1 = Feature(key="FEATURE-001", title="Auth", outcomes=[], acceptance=[], stories=[])
        feature2 = Feature(key="FEATURE-002", title="Dashboard", outcomes=[], acceptance=[], stories=[])

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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"
        report_path = tmp_plans / "report.json"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            [
                "plan",
                "compare",
                "--manual",
                str(manual_path),
                "--auto",
                str(auto_path),
                "--output-format",
                "json",
                "--out",
                str(report_path),
            ],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert report_path.exists()

        # Verify JSON can be loaded
        import json

        data = json.loads(report_path.read_text())
        assert "manual_plan" in data
        assert "auto_plan" in data
        assert "deviations" in data
        assert len(data["deviations"]) == 1

    def test_compare_invalid_manual_plan(self, tmp_plans):
        """Test error handling for invalid manual plan."""
        manual_path = tmp_plans / "nonexistent.yaml"
        auto_path = tmp_plans / "auto.yaml"

        # Create valid auto plan
        idea = Idea(title="Test", narrative="Test", metrics=None)
        product = Product(themes=[], releases=[])
        plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product, features=[], metadata=None, clarifications=None
        )
        dump_yaml(plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 1  # Error: file not found
        assert "Manual plan not found" in result.stdout

    def test_compare_invalid_auto_plan(self, tmp_plans):
        """Test error handling for invalid auto plan."""
        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "nonexistent.yaml"

        # Create valid manual plan
        idea = Idea(title="Test", narrative="Test", metrics=None)
        product = Product(themes=[], releases=[])
        plan = PlanBundle(
            version="1.0", idea=idea, business=None, product=product, features=[], metadata=None, clarifications=None
        )
        dump_yaml(plan.model_dump(exclude_none=True), manual_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 1  # Error: file not found
        assert "Auto plan not found" in result.stdout

    def test_compare_multiple_deviations(self, tmp_plans):
        """Test detecting multiple deviations at once."""
        idea1 = Idea(title="Project A", narrative="Original", metrics=None)
        idea2 = Idea(title="Project B", narrative="Modified", metrics=None)

        product1 = Product(themes=["AI"], releases=[])
        product2 = Product(themes=["ML"], releases=[])

        feature1 = Feature(key="FEATURE-001", title="Auth", outcomes=[], acceptance=[], stories=[])
        feature2 = Feature(key="FEATURE-002", title="Dashboard", outcomes=[], acceptance=[], stories=[])

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

        manual_path = tmp_plans / "manual.yaml"
        auto_path = tmp_plans / "auto.yaml"

        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        result = runner.invoke(
            app,
            ["plan", "compare", "--manual", str(manual_path), "--auto", str(auto_path)],
        )

        assert result.exit_code == 0  # Succeeds even with deviations
        assert "deviation(s) found" in result.stdout
        # Should detect: idea title mismatch, theme mismatch, extra feature
        assert int(result.stdout.split("deviation(s) found")[0].split()[-1]) >= 3
