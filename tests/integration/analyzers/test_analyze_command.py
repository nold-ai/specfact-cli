"""Integration tests for analyze command."""

import tempfile
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from specfact_cli.cli import app

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            assert "Import complete" in result.stdout

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

            output_path = Path(tmpdir) / "plan.yaml"
            report_path = Path(tmpdir) / "report.md"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                    "--report",
                    str(report_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            assert report_path.exists()

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

            output_path = Path(tmpdir) / "plan.yaml"

            # Use high threshold to filter out bad code
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                    "--confidence",
                    "0.8",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            # Check that only well-documented service is included
            plan_content = output_path.read_text()
            assert "DocumentedService" in plan_content or "Documented Service" in plan_content
            # Undocumented should be filtered out
            assert "UndocumentedService" not in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0

            # Check themes in output
            plan_content = output_path.read_text()
            assert "CLI" in plan_content
            assert "Async" in plan_content
            assert "Validation" in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0

            # Check for story points in YAML
            plan_content = output_path.read_text()
            assert "story_points:" in plan_content
            assert "value_points:" in plan_content
            assert "tasks:" in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0

            # Check for CRUD story grouping
            plan_content = output_path.read_text()
            # Should have separate stories for Create, Read, Update, Delete
            assert "create" in plan_content.lower()
            assert "view" in plan_content.lower() or "read" in plan_content.lower()
            assert "update" in plan_content.lower()
            assert "delete" in plan_content.lower()

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0

            # Check for user-centric story format
            plan_content = output_path.read_text()
            assert "As a user" in plan_content or "As a developer" in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            # Should show validation success
            assert "validation passed" in result.stdout.lower()

    def test_code2spec_empty_repository(self):
        """Test analyzing an empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty src directory
            repo_path = Path(tmpdir) / "src"
            repo_path.mkdir()

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            # Should still succeed but with no features
            assert result.exit_code == 0
            assert output_path.exists()

            plan_content = output_path.read_text()
            assert "features: []" in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                ],
            )

            # Should succeed and analyze valid file
            assert result.exit_code == 0
            plan_content = output_path.read_text()
            assert "ValidService" in plan_content or "Valid Service" in plan_content

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

            output_path = Path(tmpdir) / "plan.yaml"

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    tmpdir,
                    "--out",
                    str(output_path),
                    "--shadow-only",
                ],
            )

            assert result.exit_code == 0
            # Should mention shadow mode in output
            assert "shadow" in result.stdout.lower() or "observe" in result.stdout.lower()
