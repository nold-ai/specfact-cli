"""End-to-end tests for complete workflows with .specfact directory structure."""

from textwrap import dedent

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Idea, PlanBundle, Product
from specfact_cli.utils.yaml_utils import dump_yaml, load_yaml


runner = CliRunner()


class TestCompleteWorkflowWithNewStructure:
    """Test complete workflows using .specfact directory structure."""

    def test_greenfield_workflow_with_scaffold(self, tmp_path):
        """
        Test complete greenfield workflow:
        1. Init project with scaffold
        2. Verify structure created
        3. Edit plan manually
        4. Validate plan
        """
        import os

        # Step 1: Initialize project with scaffold (must run from target directory)
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
        assert "Directory structure created" in result.stdout or "Scaffolded" in result.stdout

        # Step 2: Verify structure
        specfact_dir = tmp_path / ".specfact"
        assert (specfact_dir / "plans" / "main.bundle.yaml").exists()
        assert (specfact_dir / "protocols").exists()
        assert (specfact_dir / "reports" / "brownfield").exists()
        assert (specfact_dir / "reports" / "comparison").exists()
        assert (specfact_dir / ".gitignore").exists()

        # Step 3: Verify .gitignore content
        gitignore = (specfact_dir / ".gitignore").read_text()
        assert "reports/" in gitignore
        assert "gates/results/" in gitignore
        assert "cache/" in gitignore

        # Step 4: Load and verify plan
        plan_path = specfact_dir / "plans" / "main.bundle.yaml"
        plan_data = load_yaml(plan_path)
        assert plan_data["version"] == "1.0"
        # In non-interactive mode, plan will have default/minimal data
        assert "idea" in plan_data or "product" in plan_data

    def test_brownfield_analysis_workflow(self, tmp_path):
        """
        Test complete brownfield workflow:
        1. Analyze existing codebase
        2. Verify plan generated in .specfact/plans/
        3. Create manual plan in .specfact/plans/
        4. Compare plans
        5. Verify comparison report in .specfact/reports/comparison/
        """
        import os

        # Step 1: Create sample codebase
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        sample_code = dedent(
            '''
            class UserService:
                """Manages user operations."""

                def create_user(self, name, email):
                    """Create a new user account."""
                    pass

                def get_user(self, user_id):
                    """Retrieve user by ID."""
                    pass

                def update_user(self, user_id, data):
                    """Update user information."""
                    pass

                def delete_user(self, user_id):
                    """Delete user account."""
                    pass
        '''
        )
        (src_dir / "users.py").write_text(sample_code)

        # Step 2: Run brownfield analysis
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.5",
            ],
        )

        assert result.exit_code == 0
        assert "Import complete" in result.stdout

        # Step 3: Verify auto-derived plan in .specfact/plans/
        plans_dir = tmp_path / ".specfact" / "plans"
        assert plans_dir.exists()

        auto_reports = list(plans_dir.glob("auto-derived.*.bundle.yaml"))
        assert len(auto_reports) > 0

        auto_plan_path = auto_reports[0]
        auto_plan_data = load_yaml(auto_plan_path)
        assert "features" in auto_plan_data
        assert len(auto_plan_data["features"]) > 0

        # Step 4: Create manual plan
        manual_plan = PlanBundle(
            version="1.0",
            idea=Idea(
                title="User Management System",
                narrative="System for managing user accounts",
                metrics=None,
            ),
            business=None,
            product=Product(themes=["User Management"], releases=[]),
            features=auto_plan_data["features"],  # Use discovered features
            metadata=None,
            clarifications=None,
        )

        manual_plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        dump_yaml(manual_plan.model_dump(exclude_none=True), manual_plan_path)

        # Step 5: Run plan comparison
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

        # Step 6: Verify comparison report in .specfact/reports/comparison/
        comparison_dir = tmp_path / ".specfact" / "reports" / "comparison"
        assert comparison_dir.exists()

        comparison_reports = list(comparison_dir.glob("report-*.md"))
        assert len(comparison_reports) > 0

    def test_full_lifecycle_workflow(self, tmp_path):
        """
        Test complete lifecycle:
        1. Init with scaffold
        2. Create code
        3. Analyze code
        4. Compare with manual plan
        5. Iterate and fix deviations
        """
        # Step 1: Initialize project
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

        # Step 2: Add features to manual plan
        manual_plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        plan_data = load_yaml(manual_plan_path)

        plan_data["features"] = [
            {
                "key": "FEATURE-001",
                "title": "Task CRUD",
                "outcomes": ["Users can manage tasks"],
                "acceptance": ["Create works", "Read works", "Update works", "Delete works"],
                "stories": [],
            },
            {
                "key": "FEATURE-002",
                "title": "Task Search",
                "outcomes": ["Users can search tasks"],
                "acceptance": ["Search works"],
                "stories": [],
            },
        ]
        dump_yaml(plan_data, manual_plan_path)

        # Step 3: Create partial implementation
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Only implement FEATURE-001 (missing FEATURE-002)
        task_code = dedent(
            '''
            class TaskManager:
                """Manages tasks."""

                def create_task(self, title):
                    """Create a new task."""
                    pass

                def get_task(self, task_id):
                    """Get task by ID."""
                    pass

                def update_task(self, task_id, data):
                    """Update task."""
                    pass

                def delete_task(self, task_id):
                    """Delete task."""
                    pass
        '''
        )
        (src_dir / "tasks.py").write_text(task_code)

        # Step 4: Analyze implementation
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

        # Step 5: Compare plans (should find missing FEATURE-002)
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

        # Should complete successfully (even with deviations)
        assert result.exit_code == 0
        assert "deviation(s) found" in result.stdout
        assert "FEATURE-002" in result.stdout or "Task Search" in result.stdout

        # Step 6: Verify deviation report generated
        comparison_dir = tmp_path / ".specfact" / "reports" / "comparison"
        reports = list(comparison_dir.glob("report-*.md"))
        assert len(reports) > 0

        report_content = reports[0].read_text()
        assert "FEATURE-002" in report_content or "Task Search" in report_content

    def test_multi_plan_repository_support(self, tmp_path):
        """
        Test that .specfact structure supports multiple plan bundles.
        """
        # Step 1: Initialize main plan
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
                    "--out",
                    str(tmp_path / ".specfact" / "plans" / "main.bundle.yaml"),
                ],
            )
            assert result.exit_code == 0

            # Step 2: Create additional plan
            result = runner.invoke(
                app,
                [
                    "plan",
                    "init",
                    "--no-interactive",
                    "--out",
                    str(tmp_path / ".specfact" / "plans" / "alternative.bundle.yaml"),
                ],
            )
            assert result.exit_code == 0
        finally:
            os.chdir(old_cwd)

        # Step 3: Verify both plans exist
        plans_dir = tmp_path / ".specfact" / "plans"
        assert (plans_dir / "main.bundle.yaml").exists()
        assert (plans_dir / "alternative.bundle.yaml").exists()

        # Step 4: Verify plans exist and are valid
        main_data = load_yaml(plans_dir / "main.bundle.yaml")
        alt_data = load_yaml(plans_dir / "alternative.bundle.yaml")

        # Both plans should have version and product (minimal plan structure)
        assert main_data["version"] == "1.0"
        assert "product" in main_data
        assert alt_data["version"] == "1.0"
        assert "product" in alt_data

        # Note: --no-interactive creates minimal plans without idea section

    def test_gitignore_prevents_ephemeral_tracking(self, tmp_path):
        """
        Test that .gitignore correctly prevents tracking ephemeral files.
        """
        # Step 1: Scaffold project
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

        # Step 2: Create ephemeral files that should be ignored
        specfact_dir = tmp_path / ".specfact"

        # Create report (should be ignored)
        reports_dir = specfact_dir / "reports" / "brownfield"
        (reports_dir / "auto-derived.2025-01-01.yaml").write_text("test")

        # Create cache file (should be ignored)
        cache_dir = specfact_dir / "cache"
        (cache_dir / "test.cache").write_text("test")

        # Create gate results (should be ignored)
        gates_results_dir = specfact_dir / "gates" / "results"
        (gates_results_dir / "result.json").write_text("{}")

        # Step 3: Verify .gitignore rules
        gitignore = (specfact_dir / ".gitignore").read_text()
        assert "reports/" in gitignore
        assert "cache/" in gitignore
        assert "gates/results/" in gitignore

        # Plans and protocols should be kept (negated in gitignore with !)
        assert "!plans/" in gitignore  # Negation means it IS versioned
        assert "!protocols/" in gitignore  # Negation means it IS versioned
        assert "!config.yaml" in gitignore


class TestMigrationScenarios:
    """Test migration from old structure to new .specfact structure."""

    def test_migrate_from_old_structure(self, tmp_path):
        """
        Test migrating from old 'contracts/' structure to new '.specfact/' structure.
        """
        # Step 1: Create old structure
        old_contracts_dir = tmp_path / "contracts" / "plans"
        old_contracts_dir.mkdir(parents=True)

        old_reports_dir = tmp_path / "reports"
        old_reports_dir.mkdir()

        # Create old plan
        old_plan = PlanBundle(
            version="1.0",
            idea=Idea(title="Legacy Plan", narrative="Old structure", metrics=None),
            business=None,
            product=Product(themes=["Legacy"], releases=[]),
            features=[],
            clarifications=None,
            metadata=None,
        )

        old_plan_path = old_contracts_dir / "plan.bundle.yaml"
        dump_yaml(old_plan.model_dump(exclude_none=True), old_plan_path)

        # Create old report
        old_report_path = old_reports_dir / "auto-derived.yaml"
        dump_yaml(old_plan.model_dump(exclude_none=True), old_report_path)

        # Step 2: Initialize new structure
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

        # Step 3: Copy old plan to new location
        import shutil

        new_plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        shutil.copy(old_plan_path, new_plan_path)

        # Step 4: Verify plan works in new structure
        plan_data = load_yaml(new_plan_path)
        assert plan_data["idea"]["title"] == "Legacy Plan"

        # Step 5: Verify new commands work with migrated plan
        # Create test code
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text(
            '''
class Test:
    """Test."""
    def method(self):
        """Method."""
        pass
'''
        )

        # Analyze
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

        # Compare
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

        # Should work regardless of deviations
        assert result.exit_code in [0, 1]


class TestRealWorldScenarios:
    """Test real-world usage scenarios with .specfact structure."""

    def test_continuous_integration_workflow(self, tmp_path):
        """
        Simulate CI/CD workflow:
        1. Checkout repository
        2. Analyze code (brownfield)
        3. Compare with manual plan
        4. Fail if high-severity deviations
        """
        # Step 1: Setup repository with .specfact/
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

        # Step 2: Add required features to manual plan
        manual_plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        plan_data = load_yaml(manual_plan_path)
        plan_data["features"] = [
            {
                "key": "FEATURE-001",
                "title": "Authentication",
                "outcomes": ["Secure login"],
                "acceptance": ["Login works", "Logout works"],
                "stories": [],
            }
        ]
        dump_yaml(plan_data, manual_plan_path)

        # Step 3: Create code (missing logout)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "auth.py").write_text(
            '''
class AuthService:
    """Authentication service."""
    def login(self, username, password):
        """User login."""
        pass
    # Missing logout!
'''
        )

        # Step 4: CI/CD: Analyze code
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

        # Step 5: CI/CD: Compare with plan
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

        # Comparison succeeds (exit 0) even with deviations
        # Note: For CI/CD, check the report file or use a future --fail-on-deviations flag
        assert result.exit_code == 0
        assert "deviation(s) found" in result.stdout

    def test_team_collaboration_workflow(self, tmp_path):
        """
        Test team collaboration scenario:
        1. Developer A: Creates manual plan (versioned)
        2. Developer B: Pulls plan, implements features
        3. Developer B: Runs brownfield analysis (not versioned)
        4. Developer B: Compares and fixes deviations
        5. Developer A: Reviews comparison report
        """
        # Step 1: Developer A creates plan
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

        # Verify versioned files exist
        plans_dir = tmp_path / ".specfact" / "plans"
        assert (plans_dir / "main.bundle.yaml").exists()

        # Step 2: Developer B implements features
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "feature.py").write_text(
            '''
class FeatureService:
    """Feature implementation."""
    def execute(self):
        """Execute feature."""
        pass
'''
        )

        # Step 3: Developer B analyzes code
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

        # Verify auto-derived plans are in .specfact/plans/ (not reports/brownfield/)
        plans_dir = tmp_path / ".specfact" / "plans"
        assert plans_dir.exists()
        auto_reports = list(plans_dir.glob("auto-derived.*.bundle.yaml"))
        assert len(auto_reports) > 0

        # Step 4: Developer B compares
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

        # May pass or fail depending on implementation
        assert result.exit_code in [0, 1]

        # Step 5: Verify comparison report available for review
        comparison_dir = tmp_path / ".specfact" / "reports" / "comparison"
        comparison_reports = list(comparison_dir.glob("report-*.md"))
        assert len(comparison_reports) > 0
