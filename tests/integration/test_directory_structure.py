"""Integration tests for .specfact directory structure."""

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.structure import SpecFactStructure


runner = CliRunner()


class TestDirectoryStructure:
    """Test suite for .specfact directory structure management."""

    def test_ensure_structure_creates_directories(self, tmp_path):
        """Test that ensure_structure creates all required directories."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Ensure structure
        SpecFactStructure.ensure_structure(repo_path)

        # Verify all directories exist
        specfact_dir = repo_path / ".specfact"
        assert specfact_dir.exists()
        assert (specfact_dir / "plans").exists()
        assert (specfact_dir / "protocols").exists()
        assert (specfact_dir / "reports" / "brownfield").exists()
        assert (specfact_dir / "reports" / "comparison").exists()
        assert (specfact_dir / "gates" / "results").exists()
        assert (specfact_dir / "cache").exists()

    def test_ensure_structure_idempotent(self, tmp_path):
        """Test that ensure_structure can be called multiple times safely."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Call twice
        SpecFactStructure.ensure_structure(repo_path)
        SpecFactStructure.ensure_structure(repo_path)

        # Should still work
        assert (repo_path / ".specfact" / "plans").exists()

    def test_scaffold_project_creates_full_structure(self, tmp_path):
        """Test that scaffold_project creates complete directory structure."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Scaffold project
        SpecFactStructure.scaffold_project(repo_path)

        # Verify all directories
        specfact_dir = repo_path / ".specfact"
        assert (specfact_dir / "plans").exists()
        assert (specfact_dir / "protocols").exists()
        assert (specfact_dir / "reports" / "brownfield").exists()
        assert (specfact_dir / "reports" / "comparison").exists()
        assert (specfact_dir / "gates" / "config").exists()
        assert (specfact_dir / "gates" / "results").exists()
        assert (specfact_dir / "cache").exists()

        # Verify .gitignore exists
        gitignore = specfact_dir / ".gitignore"
        assert gitignore.exists()

        gitignore_content = gitignore.read_text()
        assert "reports/" in gitignore_content
        assert "gates/results/" in gitignore_content
        assert "cache/" in gitignore_content

    def test_get_default_plan_path(self, tmp_path):
        """Test getting default plan path."""
        plan_path = SpecFactStructure.get_default_plan_path(tmp_path)
        assert plan_path == tmp_path / ".specfact" / "plans" / "main.bundle.yaml"

    def test_get_timestamped_report_path(self, tmp_path):
        """Test getting timestamped report paths."""
        brownfield_path = SpecFactStructure.get_timestamped_brownfield_report(tmp_path)
        assert ".specfact/plans" in str(brownfield_path)
        assert brownfield_path.suffix == ".yaml"
        assert "auto-derived" in brownfield_path.name

    def test_get_latest_brownfield_report_no_reports(self, tmp_path):
        """Test getting latest brownfield report when none exist."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        SpecFactStructure.ensure_structure(repo_path)

        latest = SpecFactStructure.get_latest_brownfield_report(repo_path)
        assert latest is None

    def test_get_latest_brownfield_report_with_reports(self, tmp_path):
        """Test getting latest brownfield report with multiple reports."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        SpecFactStructure.ensure_structure(repo_path)

        plans_dir = repo_path / ".specfact" / "plans"

        # Create multiple reports with different timestamps
        report1 = plans_dir / "auto-derived.2025-01-01T10-00-00.bundle.yaml"
        report2 = plans_dir / "auto-derived.2025-01-02T10-00-00.bundle.yaml"
        report3 = plans_dir / "auto-derived.2025-01-03T10-00-00.bundle.yaml"

        report1.write_text("version: '1.0'")
        report2.write_text("version: '1.0'")
        report3.write_text("version: '1.0'")

        # Get latest
        latest = SpecFactStructure.get_latest_brownfield_report(repo_path)
        assert latest == report3


class TestPlanInitWithScaffold:
    """Test suite for plan init command with scaffold option."""

    def test_plan_init_basic(self, tmp_path):
        """Test basic plan init without scaffold."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "plan",
                    "init",
                    "--no-interactive",
                    "--no-scaffold",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Plan initialized" in result.stdout or "created" in result.stdout.lower()

        # Verify plan file created
        plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        assert plan_path.exists()

    def test_plan_init_with_scaffold(self, tmp_path):
        """Test plan init with scaffold creates full directory structure."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "plan",
                    "init",
                    "--no-interactive",
                    "--scaffold",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Directory structure created" in result.stdout or "Scaffolded" in result.stdout.lower()

        # Verify full structure created
        specfact_dir = tmp_path / ".specfact"
        assert (specfact_dir / "plans").exists()
        assert (specfact_dir / "protocols").exists()
        assert (specfact_dir / "reports" / "brownfield").exists()
        assert (specfact_dir / "reports" / "comparison").exists()
        assert (specfact_dir / "gates" / "config").exists()
        assert (specfact_dir / "gates" / "results").exists()
        assert (specfact_dir / ".gitignore").exists()

    def test_plan_init_custom_output(self, tmp_path):
        """Test plan init with custom output path."""
        import os

        custom_path = tmp_path / "custom" / "plan.yaml"
        custom_path.parent.mkdir(parents=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "plan",
                    "init",
                    "--no-interactive",
                    "--out",
                    str(custom_path),
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert custom_path.exists()


class TestAnalyzeWithNewStructure:
    """Test analyze command uses new directory structure."""

    def test_analyze_default_paths(self, tmp_path):
        """Test that analyze uses .specfact/ paths by default."""
        # Create a simple Python file to analyze
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        test_code = '''
class TestService:
    """Test service."""
    def test_method(self):
        """Test method."""
        pass
'''
        (src_dir / "test.py").write_text(test_code)

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "--repo",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0

        # Verify files created in .specfact/
        assert (tmp_path / ".specfact" / "plans").exists()

        # Find the generated report
        plans_dir = tmp_path / ".specfact" / "plans"
        reports = list(plans_dir.glob("auto-derived.*.bundle.yaml"))
        assert len(reports) > 0

    def test_analyze_creates_structure(self, tmp_path):
        """Test that analyze creates .specfact/ structure automatically."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        test_code = '''
class Service:
    """Service."""
    def method(self):
        """Method."""
        pass
'''
        (src_dir / "service.py").write_text(test_code)

        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "--repo",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0

        # Verify .specfact/ was created
        assert (tmp_path / ".specfact").exists()
        assert (tmp_path / ".specfact" / "plans").exists()


class TestPlanCompareWithNewStructure:
    """Test plan compare command uses new directory structure."""

    def test_compare_with_smart_defaults(self, tmp_path):
        """Test plan compare finds plans using smart defaults."""
        import os

        from specfact_cli.models.plan import Idea, PlanBundle, Product
        from specfact_cli.utils.yaml_utils import dump_yaml

        # Create manual plan
        manual_plan = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test", metrics=None),
            business=None,
            product=Product(themes=[], releases=[]),
            features=[],
            metadata=None,
        )

        manual_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        manual_path.parent.mkdir(parents=True)
        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)

        # Create auto-derived plan
        auto_plan = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test", metrics=None),
            business=None,
            product=Product(themes=[], releases=[]),
            features=[],
            metadata=None,
        )

        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)
        auto_path = plans_dir / "auto-derived.2025-01-01T10-00-00.bundle.yaml"
        dump_yaml(auto_plan.model_dump(exclude_none=True), auto_path)

        # Run compare from the target directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "plan",
                    "compare",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "No deviations found" in result.stdout

    def test_compare_output_to_specfact_reports(self, tmp_path):
        """Test plan compare saves report to .specfact/reports/comparison/."""
        import os

        from specfact_cli.models.plan import Idea, PlanBundle, Product
        from specfact_cli.utils.yaml_utils import dump_yaml

        # Create plans
        plan = PlanBundle(
            version="1.0",
            idea=Idea(title="Test", narrative="Test", metrics=None),
            business=None,
            product=Product(themes=[], releases=[]),
            features=[],
            metadata=None,
        )

        manual_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        manual_path.parent.mkdir(parents=True)
        dump_yaml(plan.model_dump(exclude_none=True), manual_path)

        brownfield_dir = tmp_path / ".specfact" / "reports" / "brownfield"
        brownfield_dir.mkdir(parents=True)
        auto_path = brownfield_dir / "auto-derived.2025-01-01T10-00-00.bundle.yaml"
        dump_yaml(plan.model_dump(exclude_none=True), auto_path)

        # Run compare from the target directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                ["plan", "compare"],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify report created in .specfact/reports/comparison/
        comparison_dir = tmp_path / ".specfact" / "reports" / "comparison"
        assert comparison_dir.exists()
        reports = list(comparison_dir.glob("report-*.md"))
        assert len(reports) > 0
