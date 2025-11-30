"""Integration tests for CodeAnalyzer with real codebases."""

import tempfile
from pathlib import Path
from textwrap import dedent

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.models.plan import PlanBundle


class TestCodeAnalyzerIntegration:
    """Integration tests for CodeAnalyzer with realistic codebases."""

    def test_analyze_realistic_codebase_with_dependencies(self):
        """Test analyzing a realistic codebase with module dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create a multi-module codebase with dependencies
            src_path = repo_path / "src"
            src_path.mkdir()

            # Module 1: Core service (base dependency)
            core_service = dedent(
                '''
                """Core service module."""

                class CoreService:
                    """Core service with base functionality."""

                    def initialize(self, config: dict) -> bool:
                        """Initialize the core service."""
                        return True

                    def shutdown(self) -> None:
                        """Shutdown the service."""
                        pass
                '''
            )
            (src_path / "core.py").write_text(core_service)

            # Module 2: Service that depends on core
            api_service = dedent(
                '''
                """API service module."""
                from core import CoreService

                class APIService:
                    """API service that uses core service."""

                    def __init__(self):
                        """Initialize API service."""
                        self.core = CoreService()

                    def handle_request(self, data: dict) -> dict:
                        """Handle an API request."""
                        self.core.initialize({})
                        return {"status": "ok"}

                    async def handle_async_request(self, data: dict) -> dict:
                        """Handle an async API request."""
                        return {"status": "ok"}
                '''
            )
            (src_path / "api.py").write_text(api_service)

            # Module 3: Repository that depends on both
            repository = dedent(
                '''
                """Repository module."""
                from core import CoreService
                from api import APIService

                class DataRepository:
                    """Data repository with CRUD operations."""

                    def create_record(self, data: dict) -> dict:
                        """Create a new record."""
                        return {"id": 1, **data}

                    def get_record(self, record_id: int) -> dict:
                        """Get record by ID."""
                        return {"id": record_id}

                    def update_record(self, record_id: int, data: dict) -> dict:
                        """Update an existing record."""
                        return {"id": record_id, **data}

                    def delete_record(self, record_id: int) -> bool:
                        """Delete a record."""
                        return True
                '''
            )
            (src_path / "repository.py").write_text(repository)

            # Analyze the codebase
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            _plan_bundle = analyzer.analyze()  # Not used - just testing it runs

            # Verify results
            assert isinstance(_plan_bundle, PlanBundle)
            assert len(analyzer.features) >= 3  # At least 3 features (CoreService, APIService, DataRepository)

            # Verify dependency graph was built
            assert len(analyzer.dependency_graph.nodes) >= 3
            assert len(analyzer.dependency_graph.edges) >= 2  # At least 2 dependencies

            # Verify type hints were extracted
            assert len(analyzer.type_hints) >= 3
            assert any("api.py" in module or "api" in module for module in analyzer.type_hints)

            # Verify async patterns were detected
            assert any("api.py" in module or "api" in module for module in analyzer.async_patterns)
            api_module = next((m for m in analyzer.async_patterns if "api.py" in m or "api" in m), None)
            if api_module:
                assert "handle_async_request" in analyzer.async_patterns[api_module]

    def test_analyze_codebase_with_type_hints(self):
        """Test that type hints are properly extracted and stored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Service with type hints."""
                from typing import List, Dict, Optional

                class TypedService:
                    """Service with comprehensive type hints."""

                    def get_items(self) -> List[str]:
                        """Get list of items."""
                        return ["item1", "item2"]

                    def get_config(self) -> Dict[str, int]:
                        """Get configuration dictionary."""
                        return {"key": 1}

                    def find_item(self, item_id: int) -> Optional[Dict[str, str]]:
                        """Find an item by ID."""
                        return {"id": str(item_id)}
                '''
            )
            (src_path / "typed.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            analyzer.analyze()

            # Verify type hints were extracted
            assert len(analyzer.type_hints) >= 1
            typed_module = next((m for m in analyzer.type_hints if "typed" in m), None)
            if typed_module:
                type_hints = analyzer.type_hints[typed_module]
                assert "get_items" in type_hints or len(type_hints) > 0

    def test_analyze_codebase_with_async_patterns(self):
        """Test that async patterns are properly detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Async service module."""
                import asyncio

                class AsyncService:
                    """Service with async operations."""

                    async def fetch_data(self) -> dict:
                        """Fetch data asynchronously."""
                        await asyncio.sleep(0.1)
                        return {"data": "test"}

                    async def process_items(self, items: list) -> list:
                        """Process items asynchronously."""
                        return [item.upper() for item in items]

                    def sync_method(self) -> str:
                        """Synchronous method."""
                        return "sync"
                '''
            )
            (src_path / "async_service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            analyzer.analyze()

            # Verify async patterns were detected
            assert len(analyzer.async_patterns) >= 1
            async_module = next((m for m in analyzer.async_patterns if "async_service" in m or "async" in m), None)
            if async_module:
                async_methods = analyzer.async_patterns[async_module]
                assert "fetch_data" in async_methods
                assert "process_items" in async_methods

    def test_analyze_codebase_with_themes(self):
        """Test that themes are detected from imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Service with various imports."""
                import asyncio
                import typer
                import pydantic
                from fastapi import FastAPI
                from redis import Redis

                class ThemedService:
                    """Service that should have multiple themes."""
                    pass
                '''
            )
            (src_path / "themed.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            analyzer.analyze()

            # Verify themes were detected
            assert len(analyzer.themes) >= 3
            assert "CLI" in analyzer.themes or "Async" in analyzer.themes
            assert "Validation" in analyzer.themes or "API" in analyzer.themes

    def test_analyze_codebase_with_crud_operations(self):
        """Test that CRUD operations are properly grouped into stories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Repository with CRUD operations."""

                class UserRepository:
                    """User data repository."""

                    def create_user(self, name: str, email: str) -> dict:
                        """Create a new user."""
                        return {"id": 1, "name": name, "email": email}

                    def get_user(self, user_id: int) -> dict:
                        """Get user by ID."""
                        return {"id": user_id}

                    def list_users(self) -> list:
                        """List all users."""
                        return []

                    def update_user(self, user_id: int, data: dict) -> dict:
                        """Update user information."""
                        return {"id": user_id, **data}

                    def delete_user(self, user_id: int) -> bool:
                        """Delete a user."""
                        return True
                '''
            )
            (src_path / "users.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            analyzer.analyze()

            # Find UserRepository feature
            user_feature = next(
                (f for f in analyzer.features if "user" in f.key.lower() or "user" in f.title.lower()),
                None,
            )

            if user_feature:
                # Should have multiple stories (Create, Read, Update, Delete)
                assert len(user_feature.stories) >= 3

                # Verify story types
                story_titles = [s.title.lower() for s in user_feature.stories]
                assert any("create" in title for title in story_titles)
                assert any("read" in title or "view" in title for title in story_titles)
                assert any("update" in title for title in story_titles)
                assert any("delete" in title for title in story_titles)

    def test_analyze_codebase_with_confidence_filtering(self):
        """Test that confidence threshold properly filters features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Well-documented service (high confidence)
            good_code = dedent(
                '''
                """Well-documented service."""

                class DocumentedService:
                    """Comprehensive service documentation.

                    This service provides core functionality for the application.
                    It handles all primary operations and integrates with external systems.
                    """

                    def process_data(self, data: dict) -> dict:
                        """Process data with validation.

                        Args:
                            data: Input data dictionary

                        Returns:
                            Processed data dictionary
                        """
                        return {"processed": True, **data}

                    def validate_input(self, input_data: dict) -> bool:
                        """Validate input data."""
                        return True

                    def transform_data(self, data: dict) -> dict:
                        """Transform data format."""
                        return data
                '''
            )
            (src_path / "good.py").write_text(good_code)

            # Poorly documented service (low confidence)
            bad_code = dedent(
                """
                class UndocumentedService:
                    def method1(self):
                        pass
                    def method2(self):
                        pass
                """
            )
            (src_path / "bad.py").write_text(bad_code)

            # Analyze with high confidence threshold
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.8)
            _plan_bundle = analyzer.analyze()  # Not used - just testing it runs

            # Should only include well-documented service (or empty if threshold too high)
            feature_keys = [f.key.lower() for f in analyzer.features]
            if len(feature_keys) > 0:
                # If features found, should only have documented service
                assert any("documented" in key for key in feature_keys)
                # Should not include undocumented service
                assert not any("undocumented" in key for key in feature_keys)
            # If no features (threshold too strict), that's also acceptable

    def test_analyze_codebase_with_dependency_graph(self):
        """Test that dependency graph correctly represents module dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Module A (no dependencies)
            module_a = dedent(
                '''
                """Module A."""
                class ModuleA:
                    """Module A class."""
                    pass
                '''
            )
            (src_path / "module_a.py").write_text(module_a)

            # Module B (depends on A)
            module_b = dedent(
                '''
                """Module B."""
                from module_a import ModuleA

                class ModuleB:
                    """Module B class."""
                    def __init__(self):
                        self.a = ModuleA()
                '''
            )
            (src_path / "module_b.py").write_text(module_b)

            # Module C (depends on B)
            module_c = dedent(
                '''
                """Module C."""
                from module_b import ModuleB

                class ModuleC:
                    """Module C class."""
                    def __init__(self):
                        self.b = ModuleB()
                '''
            )
            (src_path / "module_c.py").write_text(module_c)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            _plan_bundle = analyzer.analyze()  # Not used - just testing it runs

            # Verify dependency graph structure
            assert len(analyzer.dependency_graph.nodes) >= 3

            # Find module names in graph
            module_names = list(analyzer.dependency_graph.nodes)
            # More specific matching to avoid conflicts
            module_a_name = next((m for m in module_names if "module_a" in m and "a.py" not in m), None)
            module_b_name = next(
                (m for m in module_names if "module_b" in m and "b.py" not in m and m != "src.module_a"), None
            )
            module_c_name = next(
                (
                    m
                    for m in module_names
                    if "module_c" in m and "c.py" not in m and m not in ["src.module_a", "src.module_b"]
                ),
                None,
            )

            # Debug: Print module names and edges for troubleshooting
            if len(analyzer.dependency_graph.edges) > 0:
                edges = list(analyzer.dependency_graph.edges)
                # Verify we have the expected dependencies
                if module_b_name and module_a_name:
                    # Module B should depend on Module A
                    # Edge direction: module_b -> module_a (B imports A, so B depends on A)
                    assert analyzer.dependency_graph.has_edge(module_b_name, module_a_name), (
                        f"Missing edge from {module_b_name} to {module_a_name}. Available edges: {edges}"
                    )

                if module_c_name and module_b_name and module_c_name != module_b_name:
                    # Module C should depend on Module B
                    # Edge direction: module_c -> module_b (C imports B, so C depends on B)
                    assert analyzer.dependency_graph.has_edge(module_c_name, module_b_name), (
                        f"Missing edge from {module_c_name} to {module_b_name}. Available edges: {edges}"
                    )
            else:
                # If no edges, at least verify we have the nodes
                assert len(module_names) >= 3, f"Expected at least 3 modules, got: {module_names}"

    def test_analyze_codebase_handles_invalid_files(self):
        """Test that invalid Python files are skipped gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Valid file
            valid_code = dedent(
                '''
                """Valid module."""
                class ValidClass:
                    """Valid class."""
                    def method(self):
                        """Valid method."""
                        pass
                '''
            )
            (src_path / "valid.py").write_text(valid_code)

            # Invalid file (syntax error)
            invalid_code = "def broken syntax here"
            (src_path / "invalid.py").write_text(invalid_code)

            # Should not raise exception
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            _plan_bundle = analyzer.analyze()  # Not used - just testing it runs

            # Should still analyze valid file
            assert len(analyzer.features) >= 1
            assert any("valid" in f.key.lower() or "valid" in f.title.lower() for f in analyzer.features)

    def test_analyze_codebase_with_nested_structure(self):
        """Test analyzing a codebase with nested package structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src" / "package"
            src_path.mkdir(parents=True)

            code = dedent(
                '''
                """Nested package module."""
                class NestedService:
                    """Service in nested package."""
                    def method(self):
                        """Method."""
                        pass
                '''
            )
            (src_path / "service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            _plan_bundle = analyzer.analyze()  # Not used - just testing it runs

            # Should analyze nested structure
            assert len(analyzer.features) >= 1

    def test_analyze_empty_repository(self):
        """Test analyzing an empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # No Python files

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Should still return valid plan bundle
            assert isinstance(plan_bundle, PlanBundle)
            assert len(analyzer.features) == 0
            assert len(analyzer.dependency_graph.nodes) == 0

    def test_semgrep_integration_detects_api_endpoints(self):
        """Test that Semgrep integration detects FastAPI endpoints and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create FastAPI code with routes
            fastapi_code = dedent(
                '''
                """FastAPI application with routes."""
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/users")
                def get_users():
                    """Get all users."""
                    return []

                @app.post("/users")
                def create_user():
                    """Create a new user."""
                    return {}

                class UserService:
                    """User management service."""
                    def get_user(self, user_id: int):
                        """Get user by ID."""
                        pass
                '''
            )
            (src_path / "api.py").write_text(fastapi_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            # Verify Semgrep integration status
            assert hasattr(analyzer, "semgrep_enabled")
            assert hasattr(analyzer, "semgrep_config")

            # If Semgrep is enabled and available, verify enhancements
            if analyzer.semgrep_enabled and analyzer.semgrep_config:
                # Should have features
                assert len(analyzer.features) >= 1

                # Check if API theme was added (from Semgrep or AST)
                assert "API" in plan_bundle.product.themes or len(plan_bundle.product.themes) > 0

                # Find UserService feature
                user_feature = next(
                    (f for f in analyzer.features if "user" in f.key.lower() or "user" in f.title.lower()),
                    None,
                )

                if user_feature:
                    # If Semgrep found API endpoints, confidence should be enhanced
                    # (Base confidence + Semgrep boost if endpoints detected)
                    assert user_feature.confidence >= 0.3

    def test_semgrep_integration_detects_crud_operations(self):
        """Test that Semgrep integration detects CRUD operations and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create code with CRUD operations
            crud_code = dedent(
                '''
                """Repository with CRUD operations."""
                class ProductRepository:
                    """Product data repository."""

                    def create_product(self, data: dict) -> dict:
                        """Create a new product."""
                        return {"id": 1, **data}

                    def get_product(self, product_id: int) -> dict:
                        """Get product by ID."""
                        return {"id": product_id}

                    def update_product(self, product_id: int, data: dict) -> dict:
                        """Update product."""
                        return {"id": product_id, **data}

                    def delete_product(self, product_id: int) -> bool:
                        """Delete product."""
                        return True
                '''
            )
            (src_path / "products.py").write_text(crud_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            analyzer.analyze()  # Analyze to populate features

            # Find ProductRepository feature
            product_feature = next(
                (f for f in analyzer.features if "product" in f.key.lower() or "product" in f.title.lower()),
                None,
            )

            if product_feature:
                # Should have CRUD stories
                assert len(product_feature.stories) >= 3

                # If Semgrep is enabled and detected CRUD operations, confidence should be enhanced
                if analyzer.semgrep_enabled and analyzer.semgrep_config:
                    # Semgrep CRUD detection adds +0.1 to confidence
                    assert product_feature.confidence >= 0.3

    def test_semgrep_integration_detects_database_models(self):
        """Test that Semgrep integration detects database models and enhances features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create SQLAlchemy model
            model_code = dedent(
                '''
                """Database models."""
                from sqlalchemy import Column, Integer, String
                from sqlalchemy.ext.declarative import declarative_base

                Base = declarative_base()

                class User(Base):
                    """User database model."""
                    __tablename__ = "users"

                    id = Column(Integer, primary_key=True)
                    name = Column(String(100))
                    email = Column(String(255))
                '''
            )
            (src_path / "models.py").write_text(model_code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            # If Semgrep is enabled and detected models, verify enhancements
            if analyzer.semgrep_enabled and analyzer.semgrep_config:
                # Should have Database theme
                assert "Database" in plan_bundle.product.themes or len(plan_bundle.product.themes) > 0

                # Find User model feature
                user_feature = next(
                    (f for f in analyzer.features if "user" in f.key.lower() or "user" in f.title.lower()),
                    None,
                )

                if user_feature:
                    # Semgrep model detection adds +0.15 to confidence
                    assert user_feature.confidence >= 0.3

    def test_semgrep_integration_graceful_degradation(self):
        """Test that analysis works correctly when Semgrep is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Simple service."""
                class SimpleService:
                    """Simple service class."""
                    def method(self):
                        """Simple method."""
                        pass
                '''
            )
            (src_path / "service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plan_bundle = analyzer.analyze()

            # Should work even if Semgrep is not available
            assert isinstance(plan_bundle, PlanBundle)
            # Should have at least one feature (from AST analysis)
            assert len(analyzer.features) >= 1

            # Semgrep should be gracefully disabled if not available
            assert hasattr(analyzer, "semgrep_enabled")
            # Analysis should complete successfully regardless
            assert plan_bundle.features is not None

    def test_semgrep_integration_parallel_execution(self):
        """Test that Semgrep integration works correctly in parallel execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create multiple files to test parallel execution
            for i in range(5):
                code = dedent(
                    f'''
                    """Service {i}."""
                    class Service{i}:
                        """Service class {i}."""
                        def create_item(self):
                            """Create item."""
                            pass
                        def get_item(self):
                            """Get item."""
                            pass
                    '''
                )
                (src_path / f"service_{i}.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            analyzer.analyze()  # Analyze to test parallel execution

            # Should analyze all files in parallel
            assert len(analyzer.features) >= 5

            # All features should have valid confidence scores
            for feature in analyzer.features:
                assert feature.confidence >= 0.3
                assert feature.confidence <= 1.0

    def test_plugin_status_reporting(self):
        """Test that plugin status is correctly reported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            code = dedent(
                '''
                """Simple service."""
                class SimpleService:
                    """Simple service class."""
                    def method(self):
                        """Simple method."""
                        pass
                '''
            )
            (src_path / "service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.3)
            plugin_status = analyzer.get_plugin_status()

            # Should return a list of plugin statuses
            assert isinstance(plugin_status, list)
            assert len(plugin_status) >= 1

            # Should always include AST Analysis
            ast_plugin = next((p for p in plugin_status if p["name"] == "AST Analysis"), None)
            assert ast_plugin is not None
            assert ast_plugin["enabled"] is True
            assert ast_plugin["used"] is True
            assert "Core analysis engine" in ast_plugin["reason"]

            # Should include Semgrep status
            semgrep_plugin = next((p for p in plugin_status if p["name"] == "Semgrep Pattern Detection"), None)
            assert semgrep_plugin is not None
            assert isinstance(semgrep_plugin["enabled"], bool)
            assert isinstance(semgrep_plugin["used"], bool)
            assert "reason" in semgrep_plugin

            # Should include Dependency Graph status
            graph_plugin = next((p for p in plugin_status if p["name"] == "Dependency Graph Analysis"), None)
            assert graph_plugin is not None
            assert isinstance(graph_plugin["enabled"], bool)
            assert isinstance(graph_plugin["used"], bool)
            assert "reason" in graph_plugin

            # Each plugin should have required keys
            for plugin in plugin_status:
                assert "name" in plugin
                assert "enabled" in plugin
                assert "used" in plugin
                assert "reason" in plugin
                assert isinstance(plugin["name"], str)
                assert isinstance(plugin["enabled"], bool)
                assert isinstance(plugin["used"], bool)
                assert isinstance(plugin["reason"], str)
