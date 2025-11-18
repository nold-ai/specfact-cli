"""Unit tests for code analyzer.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import tempfile
from pathlib import Path
from textwrap import dedent

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer."""

    def test_should_skip_test_files(self):
        """Test that test files are skipped."""
        analyzer = CodeAnalyzer(Path("."))

        assert analyzer._should_skip_file(Path("tests/unit/test_foo.py"))
        assert analyzer._should_skip_file(Path("tests/integration/test_bar.py"))
        assert not analyzer._should_skip_file(Path("src/foo.py"))

    def test_should_skip_pycache(self):
        """Test that __pycache__ is skipped."""
        analyzer = CodeAnalyzer(Path("."))

        assert analyzer._should_skip_file(Path("src/__pycache__/foo.pyc"))
        assert not analyzer._should_skip_file(Path("src/foo.py"))

    def test_should_skip_venv(self):
        """Test that venv directories are skipped."""
        analyzer = CodeAnalyzer(Path("."))

        assert analyzer._should_skip_file(Path("venv/lib/python3.11/site-packages/foo.py"))
        assert analyzer._should_skip_file(Path(".venv/lib/foo.py"))
        assert not analyzer._should_skip_file(Path("src/foo.py"))

    def test_extract_technology_stack_from_requirements_txt(self):
        """Test technology stack extraction from requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text("class Service: pass")

            # Create requirements.txt
            (repo_path / "requirements.txt").write_text("python>=3.11\nfastapi==0.104.1\npydantic>=2.0.0\n")

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack was extracted
            assert plan_bundle.idea is not None
            constraints = plan_bundle.idea.constraints
            assert len(constraints) > 0

            constraint_str = " ".join(constraints).lower()
            assert "python" in constraint_str or "fastapi" in constraint_str

    def test_extract_technology_stack_from_pyproject_toml(self):
        """Test technology stack extraction from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text("class Service: pass")

            # Create pyproject.toml
            (repo_path / "pyproject.toml").write_text(
                '[project]\nrequires-python = ">=3.12"\ndependencies = ["django>=4.2.0"]\n'
            )

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack was extracted
            assert plan_bundle.idea is not None
            constraints = plan_bundle.idea.constraints
            assert len(constraints) > 0

            constraint_str = " ".join(constraints).lower()
            assert "python" in constraint_str or "django" in constraint_str

    def test_extract_technology_stack_fallback_to_defaults(self):
        """Test that defaults are used when no dependency files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text("class Service: pass")

            # No dependency files

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify defaults are used
            assert plan_bundle.idea is not None
            constraints = plan_bundle.idea.constraints
            # Should have some constraints (defaults)
            assert len(constraints) > 0

    def test_extract_themes_from_imports(self):
        """Test theme extraction from imports."""
        code = dedent(
            """
            import asyncio
            import typer
            from redis import Redis
            from pydantic import BaseModel
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent)
            analyzer._analyze_file(temp_file)

            assert "Async" in analyzer.themes
            assert "CLI" in analyzer.themes
            assert "Caching" in analyzer.themes
            assert "Validation" in analyzer.themes
        finally:
            temp_file.unlink()

    def test_extract_simple_class_as_feature(self):
        """Test extracting a simple class as a feature."""
        code = dedent(
            '''
            class UserManager:
                """Manages user operations."""

                def __init__(self):
                    """Initialize manager."""
                    pass

                def get_user(self, user_id):
                    """Get user by ID."""
                    pass

                def create_user(self, name):
                    """Create new user."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            assert feature.key == "FEATURE-USERMANAGER"
            assert feature.title == "User Manager"
            assert "Manages user operations" in feature.outcomes[0]
            assert len(feature.stories) > 0
        finally:
            temp_file.unlink()

    def test_extract_crud_stories(self):
        """Test that CRUD methods are grouped into stories."""
        code = dedent(
            '''
            class ProductCatalog:
                """Product catalog management."""

                def create_product(self, name):
                    """Create a new product."""
                    pass

                def get_product(self, product_id):
                    """Get product by ID."""
                    pass

                def list_products(self):
                    """List all products."""
                    pass

                def update_product(self, product_id, data):
                    """Update existing product."""
                    pass

                def delete_product(self, product_id):
                    """Delete a product."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            # Should have stories for Create, Read, Update, Delete
            story_titles = [s.title for s in feature.stories]

            # Check for CRUD operations
            assert any("create" in title.lower() for title in story_titles)
            assert any("view" in title.lower() or "read" in title.lower() for title in story_titles)
            assert any("update" in title.lower() for title in story_titles)
            assert any("delete" in title.lower() for title in story_titles)
        finally:
            temp_file.unlink()

    def test_story_has_points(self):
        """Test that stories have story points and value points."""
        code = dedent(
            '''
            class OrderService:
                """Order processing service."""

                def create_order(self, items):
                    """Create a new order."""
                    pass

                def process_order(self, order_id):
                    """Process an order."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            for story in feature.stories:
                assert story.story_points is not None
                assert story.value_points is not None
                assert story.story_points > 0
                assert story.value_points > 0
                assert isinstance(story.tasks, list)
                assert len(story.tasks) > 0
        finally:
            temp_file.unlink()

    def test_story_points_fibonacci(self):
        """Test that story points use Fibonacci sequence."""
        code = dedent(
            '''
            class ComplexService:
                """Service with many operations."""

                def op1(self): pass
                def op2(self): pass
                def op3(self): pass
                def op4(self): pass
                def op5(self): pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            for story in feature.stories:
                # Story points should be in Fibonacci sequence
                assert story.story_points in analyzer.FIBONACCI
                assert story.value_points in analyzer.FIBONACCI
        finally:
            temp_file.unlink()

    def test_skip_private_classes(self):
        """Test that private classes are skipped."""
        code = dedent(
            '''
            class _PrivateHelper:
                """Internal helper class."""
                pass

            class PublicService:
                """Public service class."""
                def do_something(self):
                    """Do something."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            # Should only have PublicService
            assert len(analyzer.features) == 1
            assert analyzer.features[0].title == "Public Service"
        finally:
            temp_file.unlink()

    def test_skip_test_classes(self):
        """Test that test classes are skipped."""
        code = dedent(
            '''
            class TestUserManager:
                """Test user manager."""
                def test_create(self):
                    pass

            class UserManager:
                """Real user manager."""
                def create(self):
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            # Should only have UserManager (not TestUserManager)
            assert len(analyzer.features) == 1
            assert analyzer.features[0].title == "User Manager"
        finally:
            temp_file.unlink()

    def test_confidence_below_threshold_filtered(self):
        """Test that features below confidence threshold are filtered."""
        code = dedent(
            """
            class UndocumentedService:
                def method1(self):
                    pass
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            # High threshold should filter out undocumented class
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.9)
            analyzer._analyze_file(temp_file)

            # Should be filtered out
            assert len(analyzer.features) == 0
        finally:
            temp_file.unlink()

    def test_analyze_returns_plan_bundle(self):
        """Test that analyze() returns a valid PlanBundle."""
        code = dedent(
            '''
            import typer

            class CommandHandler:
                """Handles CLI commands."""

                def execute(self, cmd):
                    """Execute a command."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "handler.py").write_text(code)

            analyzer = CodeAnalyzer(Path(tmpdir), confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            assert plan_bundle is not None
            assert plan_bundle.version == "1.0"
            assert plan_bundle.idea is not None
            assert plan_bundle.product is not None
            assert len(plan_bundle.features) > 0
            assert "CLI" in plan_bundle.product.themes

    def test_humanize_name_pascal_case(self):
        """Test humanizing PascalCase names."""
        analyzer = CodeAnalyzer(Path("."))

        assert analyzer._humanize_name("UserManager") == "User Manager"
        assert analyzer._humanize_name("HTTPClient") == "H T T P Client"  # Edge case

    def test_humanize_name_snake_case(self):
        """Test humanizing snake_case names."""
        analyzer = CodeAnalyzer(Path("."))

        assert analyzer._humanize_name("user_manager") == "User Manager"
        assert analyzer._humanize_name("http_client") == "Http Client"

    def test_validation_methods_grouped(self):
        """Test that validation methods are grouped together."""
        code = dedent(
            '''
            class DataValidator:
                """Validates data."""

                def validate_email(self, email):
                    """Validate email format."""
                    pass

                def validate_phone(self, phone):
                    """Validate phone number."""
                    pass

                def is_valid(self, data):
                    """Check if data is valid."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            # Should have a "Validation" story
            validation_stories = [s for s in feature.stories if "validate" in s.title.lower()]
            assert len(validation_stories) > 0

            # All validation methods should be in tasks
            validation_story = validation_stories[0]
            assert "validate_email()" in validation_story.tasks or "validate_phone()" in validation_story.tasks
        finally:
            temp_file.unlink()

    def test_user_centric_story_titles(self):
        """Test that story titles are user-centric (As a user/developer, I can...)."""
        code = dedent(
            '''
            class PaymentProcessor:
                """Processes payments."""

                def process_payment(self, amount):
                    """Process a payment."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            for story in feature.stories:
                # All stories should start with "As a user" or "As a developer"
                assert story.title.startswith("As a user") or story.title.startswith("As a developer")
        finally:
            temp_file.unlink()

    def test_story_tasks_are_method_names(self):
        """Test that story tasks list the actual method names."""
        code = dedent(
            '''
            class ReportGenerator:
                """Generates reports."""

                def generate_pdf(self):
                    """Generate PDF report."""
                    pass

                def generate_html(self):
                    """Generate HTML report."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            # Find generation story
            gen_stories = [s for s in feature.stories if "generate" in s.title.lower()]
            assert len(gen_stories) > 0

            # Tasks should include method names with ()
            gen_story = gen_stories[0]
            assert any("generate" in task.lower() for task in gen_story.tasks)
            assert all(task.endswith("()") for task in gen_story.tasks)
        finally:
            temp_file.unlink()

    def test_acceptance_criteria_from_docstrings(self):
        """Test that acceptance criteria are extracted from method docstrings."""
        code = dedent(
            '''
            class EmailService:
                """Sends emails."""

                def send_email(self, to, subject, body):
                    """Send an email to a recipient with subject and body."""
                    pass
        '''
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            analyzer = CodeAnalyzer(temp_file.parent, confidence_threshold=0.5)
            analyzer._analyze_file(temp_file)

            assert len(analyzer.features) == 1
            feature = analyzer.features[0]

            # Should have stories with acceptance criteria
            for story in feature.stories:
                assert len(story.acceptance) > 0
                # If the story has the send_email method, check its docstring is in acceptance
                if "send_email()" in story.tasks:
                    assert any("email" in criterion.lower() for criterion in story.acceptance)
        finally:
            temp_file.unlink()
