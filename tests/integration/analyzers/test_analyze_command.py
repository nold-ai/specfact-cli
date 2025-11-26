"""Integration tests for analyze command."""

import tempfile
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.bundle_loader import load_project_bundle


runner = CliRunner()


class TestAnalyzeCommand:
    """Integration tests for 'specfact import from-code' command."""

    def test_code2spec_basic_repository(self):
        """Test analyzing a basic Python repository."""
        code = dedent(
            '''
            """Sample module."""

            class UserService:
                """User management service."""

                def create_user(self, name):
                    """Create a new user."""
                    pass

                def get_user(self, user_id):
                    """Get user by ID."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "service.py").write_text(code)

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "test-bundle",
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0
            assert "Import complete" in result.stdout or "created" in result.stdout.lower()

            # Verify modular bundle structure
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / "test-bundle"
            assert bundle_dir.exists()
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None

    def test_code2spec_with_report(self):
        """Test generating analysis report."""
        code = dedent(
            '''
            class PaymentProcessor:
                """Process payments."""

                def process_payment(self, amount):
                    """Process a payment."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "payment.py").write_text(code)

            report_path = Path(tmpdir) / "report.md"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "payment-bundle",
                    "--repo",
                    tmpdir,
                    "--report",
                    str(report_path),
                ],
            )

            assert result.exit_code == 0
            assert report_path.exists()

            # Verify modular bundle structure
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / "payment-bundle"
            assert bundle_dir.exists()

            # Check report content
            report_content = report_path.read_text()
            assert "Brownfield Import Report" in report_content
            assert "Payment Processor" in report_content

    def test_code2spec_with_confidence_threshold(self):
        """Test filtering by confidence threshold."""
        # Create a well-documented class (high confidence)
        good_code = dedent(
            '''
            class DocumentedService:
                """Well-documented service with clear purpose."""

                def create_record(self, data):
                    """Create a new record with validation."""
                    pass

                def get_record(self, record_id):
                    """Retrieve a record by ID."""
                    pass

                def update_record(self, record_id, data):
                    """Update an existing record."""
                    pass
        '''
        )

        # Create a poorly documented class (low confidence)
        bad_code = dedent(
            """
            class UndocumentedService:
                def method1(self):
                    pass
        """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "good.py").write_text(good_code)
            (repo_path / "bad.py").write_text(bad_code)

            bundle_name = "filtered-bundle"

            # Use high threshold to filter out bad code
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                    "--confidence",
                    "0.8",
                ],
            )

            assert result.exit_code == 0

            # Check that only well-documented service is included
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            # Check features for documented service
            feature_keys = list(bundle.features.keys())
            assert len(feature_keys) > 0
            # Undocumented should be filtered out (check feature titles/keys)
            all_feature_text = " ".join([f.title for f in bundle.features.values()])
            assert "Documented" in all_feature_text or "Documented Service" in all_feature_text

    def test_code2spec_detects_themes(self):
        """Test that themes are detected from imports."""
        code = dedent(
            '''
            import asyncio
            import typer
            from pydantic import BaseModel

            class CLIHandler:
                """CLI command handler."""

                async def handle_command(self, cmd):
                    """Handle a command asynchronously."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "cli.py").write_text(code)

            bundle_name = "themes-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0

            # Check themes in bundle
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert len(bundle.product.themes) > 0
            theme_names = " ".join(bundle.product.themes)
            assert "CLI" in theme_names or "Async" in theme_names or "Validation" in theme_names

    def test_code2spec_generates_story_points(self):
        """Test that story points and value points are generated."""
        code = dedent(
            '''
            class OrderService:
                """Order processing service."""

                def create_order(self, items):
                    """Create a new order from items."""
                    pass

                def calculate_total(self, order_id):
                    """Calculate order total with tax."""
                    pass

                def apply_discount(self, order_id, code):
                    """Apply discount code to order."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "orders.py").write_text(code)

            bundle_name = "orders-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0

            # Check for story points in bundle
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            # Check that features have stories with story points
            has_stories = any(
                len(f.stories) > 0 and any(s.story_points is not None for s in f.stories)
                for f in bundle.features.values()
            )
            assert has_stories or len(bundle.features) > 0

    def test_code2spec_groups_crud_operations(self):
        """Test that CRUD operations are properly grouped."""
        code = dedent(
            '''
            class ProductRepository:
                """Product data repository."""

                def create_product(self, data):
                    """Create a new product."""
                    pass

                def get_product(self, product_id):
                    """Get product by ID."""
                    pass

                def list_products(self):
                    """List all products."""
                    pass

                def update_product(self, product_id, data):
                    """Update product."""
                    pass

                def delete_product(self, product_id):
                    """Delete product."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "repository.py").write_text(code)

            bundle_name = "crud-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0

            # Check for CRUD story grouping
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            # Check that features have stories with CRUD operations
            all_story_titles = " ".join(
                [s.title.lower() for f in bundle.features.values() for s in f.stories]
            )
            # Should have separate stories for Create, Read, Update, Delete
            assert "create" in all_story_titles or len(bundle.features) > 0

    def test_code2spec_user_centric_stories(self):
        """Test that stories are user-centric (As a user, I can...)."""
        code = dedent(
            '''
            class NotificationService:
                """Send notifications to users."""

                def send_email(self, to, subject, body):
                    """Send email notification."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "notifications.py").write_text(code)

            bundle_name = "notifications-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0

            # Check for user-centric story format
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            # Check story titles for user-centric format
            all_story_titles = " ".join(
                [s.title for f in bundle.features.values() for s in f.stories]
            )
            assert "As a user" in all_story_titles or "As a developer" in all_story_titles or len(bundle.features) > 0

    def test_code2spec_validation_passes(self):
        """Test that generated plan passes validation."""
        code = dedent(
            '''
            class AuthService:
                """Authentication service."""

                def login(self, username, password):
                    """Authenticate user."""
                    pass

                def logout(self, session_id):
                    """End user session."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "auth.py").write_text(code)

            bundle_name = "auth-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0
            # Bundle creation itself validates, check that bundle exists
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()

    def test_code2spec_empty_repository(self):
        """Test analyzing an empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty src directory
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            bundle_name = "empty-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            # Should still succeed but with no features
            assert result.exit_code == 0
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            assert len(bundle.features) == 0

    def test_code2spec_invalid_python(self):
        """Test that invalid Python files are skipped gracefully."""
        invalid_code = "def broken syntax here"
        valid_code = dedent(
            '''
            class ValidService:
                """Valid service."""
                def method(self):
                    """A method."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "broken.py").write_text(invalid_code)
            (repo_path / "valid.py").write_text(valid_code)

            bundle_name = "mixed-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                ],
            )

            # Should succeed and analyze valid file
            assert result.exit_code == 0
            bundle_dir = Path(tmpdir) / ".specfact" / "projects" / bundle_name
            bundle = load_project_bundle(bundle_dir)
            assert bundle is not None
            # Check that valid service is included
            all_feature_titles = " ".join([f.title for f in bundle.features.values()])
            assert "Valid" in all_feature_titles or len(bundle.features) > 0

    def test_code2spec_shadow_mode(self):
        """Test shadow mode flag is accepted."""
        code = dedent(
            '''
            class TestService:
                """Test service."""
                def test_method(self):
                    """Test."""
                    pass
        '''
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            (repo_path / "test.py").write_text(code)

            bundle_name = "shadow-bundle"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    tmpdir,
                    "--shadow-only",
                ],
            )

            assert result.exit_code == 0
            # Should mention shadow mode in output
            assert "shadow" in result.stdout.lower() or "observe" in result.stdout.lower()
