"""E2E tests for built-in pattern analysis in CodeAnalyzer."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.cli import app
from specfact_cli.models.plan import PlanBundle


runner = CliRunner()


class TestPythonPatternsE2E:
    """End-to-end tests for built-in pattern analysis in CodeAnalyzer."""

    @pytest.mark.timeout(30)
    def test_patterns_detects_fastapi_routes(self):
        """Test that the built-in scanner detects FastAPI routes and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create FastAPI application
            fastapi_code = dedent(
                '''
                """FastAPI application."""
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/api/users")
                def get_users():
                    """Get all users."""
                    return []

                @app.post("/api/users")
                def create_user():
                    """Create a new user."""
                    return {}

                @app.put("/api/users/{user_id}")
                def update_user(user_id: int):
                    """Update user."""
                    return {}

                @app.delete("/api/users/{user_id}")
                def delete_user(user_id: int):
                    """Delete user."""
                    return {}
                '''
            )
            (src_path / "main.py").write_text(fastapi_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            assert "API" in plan_bundle.product.themes

    @pytest.mark.timeout(30)
    def test_patterns_detects_flask_routes(self):
        """Test that the built-in scanner detects Flask routes and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create Flask application
            flask_code = dedent(
                '''
                """Flask application."""
                from flask import Flask

                app = Flask(__name__)

                @app.route("/items", methods=["GET"])
                def get_items():
                    """Get all items."""
                    return []

                @app.route("/items", methods=["POST"])
                def create_item():
                    """Create a new item."""
                    return {}
                '''
            )
            (src_path / "app.py").write_text(flask_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            # Should detect API theme
            assert "API" in plan_bundle.product.themes

    @pytest.mark.timeout(30)
    def test_patterns_detects_sqlalchemy_models(self):
        """Test that the built-in scanner detects SQLAlchemy models and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create SQLAlchemy models
            model_code = dedent(
                '''
                """Database models."""
                from sqlalchemy import Column, Integer, String, DateTime
                from sqlalchemy.ext.declarative import declarative_base

                Base = declarative_base()

                class Product(Base):
                    """Product model."""
                    __tablename__ = "products"
                    id = Column(Integer, primary_key=True)
                    name = Column(String(100))
                    price = Column(Integer)

                class Order(Base):
                    """Order model."""
                    __tablename__ = "orders"
                    id = Column(Integer, primary_key=True)
                    product_id = Column(Integer)
                    quantity = Column(Integer)
                '''
            )
            (src_path / "models.py").write_text(model_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            assert plan_bundle.idea is not None
            assert any("SQLAlchemy" in constraint for constraint in plan_bundle.idea.constraints or [])

    def test_patterns_detects_auth_patterns(self):
        """Test that the built-in scanner detects authentication patterns and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create code with auth decorators
            auth_code = dedent(
                '''
                """Protected API endpoints."""
                from fastapi import FastAPI, Depends
                from fastapi.security import HTTPBearer

                app = FastAPI()
                security = HTTPBearer()

                def require_auth():
                    """Auth dependency."""
                    pass

                @app.get("/protected", dependencies=[Depends(require_auth)])
                def protected_endpoint():
                    """Protected endpoint."""
                    return {}
                '''
            )
            (src_path / "auth.py").write_text(auth_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            assert "API" in plan_bundle.product.themes

    def test_patterns_cli_integration(self):
        """Test built-in pattern analysis via CLI import command."""
        import os

        # Ensure TEST_MODE is set to keep the CLI fixture local
        os.environ["TEST_MODE"] = "true"

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create code with FastAPI routes
            fastapi_code = dedent(
                '''
                """FastAPI application."""
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/users")
                def get_users():
                    """Get all users."""
                    return []

                class UserService:
                    """User service."""
                    def create_user(self):
                        """Create user."""
                        pass
                '''
            )
            (src_path / "api.py").write_text(fastapi_code)

            # Run CLI import command
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "test-semgrep-bundle",
                    "--repo",
                    str(repo_path),
                    "--confidence",
                    "0.3",
                ],
            )

            # Command should succeed
            assert result.exit_code == 0 or "Import complete" in result.stdout or "created" in result.stdout.lower()

            # Verify bundle was created
            bundle_dir = repo_path / ".specfact" / "projects" / "test-semgrep-bundle"
            if bundle_dir.exists():
                from specfact_cli.utils.bundle_loader import load_project_bundle

                bundle = load_project_bundle(bundle_dir)
                assert bundle is not None
                assert len(bundle.features) >= 1

                # Verify themes were detected
                assert len(bundle.product.themes) > 0

    def test_patterns_parallel_execution_performance(self):
        """Test that built-in pattern analysis doesn't significantly slow down parallel execution."""
        import os
        import time

        # Ensure TEST_MODE is set to skip Semgrep (test still validates parallel execution)
        os.environ["TEST_MODE"] = "true"

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create multiple files for parallel processing
            for i in range(10):
                code = dedent(
                    f'''
                    """Service {i}."""
                    class Service{i}:
                        """Service class {i}."""
                        def method(self):
                            """Method."""
                            pass
                    '''
                )
                (src_path / f"service_{i}.py").write_text(code)

            # Measure analysis time
            start_time = time.time()
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            analyzer.analyze()  # Analyze to test parallel execution
            elapsed_time = time.time() - start_time

            # Should complete in reasonable time (< 30 seconds for 10 files)
            assert elapsed_time < 30.0, f"Analysis took too long: {elapsed_time:.2f}s"

            # Should analyze all files
            assert len(analyzer.features) >= 10

    def test_patterns_findings_enhance_outcomes(self):
        """Test that pattern findings are added to feature outcomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create code with API endpoints
            api_code = dedent(
                '''
                """API service."""
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/products")
                def get_products():
                    """Get all products."""
                    return []

                class ProductService:
                    """Product service."""
                    def create_product(self):
                        """Create product."""
                        pass
                '''
            )
            (src_path / "api.py").write_text(api_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            analyzer.analyze()  # Analyze to populate features

            product_feature = next(feature for feature in analyzer.features if "product" in feature.key.lower())
            assert "Provides CRUD operations: CREATE product" in product_feature.outcomes

    def test_patterns_work_without_external_tool(self):
        """Test that analysis works correctly without an external scanner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Simple service."""
                class SimpleService:
                    """Simple service."""
                    def method(self):
                        """Method."""
                        pass
                '''
            )
            (src_path / "service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            # Should work even without an external scanner
            assert isinstance(plan_bundle, PlanBundle)
            assert len(analyzer.features) >= 1

            assert any(plugin["name"] == "AST Analysis" and plugin["used"] for plugin in analyzer.get_plugin_status())
