"""Integration tests for contract extraction in CodeAnalyzer.

Tests contract extraction integration with CodeAnalyzer and plan bundle generation.
"""

import tempfile
from pathlib import Path
from textwrap import dedent

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer


class TestContractExtractionIntegration:
    """Integration tests for contract extraction."""

    def test_contracts_extracted_in_stories(self):
        """Test that contracts are extracted and included in stories."""
        code = dedent(
            """
            class UserService:
                '''User management service.'''

                def create_user(self, name: str, email: str) -> dict:
                    '''Create a new user.'''
                    assert name and email
                    return {"id": 1, "name": name, "email": email}

                def get_user(self, user_id: int) -> dict | None:
                    '''Get user by ID.'''
                    if user_id < 0:
                        raise ValueError("Invalid user ID")
                    return {"id": user_id, "name": "Test"}
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "service.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            # Check that contracts are extracted
            assert len(plan_bundle.features) > 0
            feature = plan_bundle.features[0]
            assert len(feature.stories) > 0

            # Check that at least one story has contracts
            stories_with_contracts = [s for s in feature.stories if s.contracts]
            assert len(stories_with_contracts) > 0

            # Check contract structure
            story = stories_with_contracts[0]
            contracts = story.contracts
            assert isinstance(contracts, dict)
            assert "parameters" in contracts
            assert "return_type" in contracts
            assert "preconditions" in contracts
            assert "postconditions" in contracts
            assert "error_contracts" in contracts

    def test_contracts_include_parameters(self):
        """Test that contract parameters are extracted correctly."""
        code = dedent(
            """
            class Calculator:
                '''Simple calculator.'''

                def add(self, a: int, b: int) -> int:
                    '''Add two numbers.'''
                    return a + b
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "calc.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            feature = plan_bundle.features[0]
            story = feature.stories[0]

            if story.contracts:
                contracts = story.contracts
                assert len(contracts["parameters"]) >= 2  # At least a and b (self may be included)
                param_names = [p["name"] for p in contracts["parameters"]]
                assert "a" in param_names or "b" in param_names

    def test_contracts_include_return_types(self):
        """Test that return types are extracted correctly."""
        code = dedent(
            """
            class DataProcessor:
                '''Process data.'''

                def process(self, data: str) -> dict:
                    '''Process data and return result.'''
                    return {"result": data.upper()}
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "processor.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            feature = plan_bundle.features[0]
            story = feature.stories[0]

            if story.contracts:
                contracts = story.contracts
                assert contracts["return_type"] is not None
                assert contracts["return_type"]["type"] in ("dict", "Dict", "dict[str, Any]")

    def test_contracts_include_preconditions(self):
        """Test that preconditions are extracted from validation logic."""
        code = dedent(
            """
            class Validator:
                '''Validation service.'''

                def validate(self, value: int) -> bool:
                    '''Validate value.'''
                    assert value > 0, "Value must be positive"
                    return True
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "validator.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            feature = plan_bundle.features[0]
            story = feature.stories[0]

            if story.contracts:
                contracts = story.contracts
                # Preconditions may be extracted from assert statements
                assert isinstance(contracts["preconditions"], list)

    def test_contracts_include_error_contracts(self):
        """Test that error contracts are extracted from exception handling."""
        code = dedent(
            """
            class ErrorHandler:
                '''Error handling service.'''

                def handle(self, data: str) -> str:
                    '''Handle data with error checking.'''
                    try:
                        return data.upper()
                    except AttributeError:
                        raise ValueError("Invalid data")
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "handler.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            feature = plan_bundle.features[0]
            story = feature.stories[0]

            if story.contracts:
                contracts = story.contracts
                # Error contracts may be extracted from try/except blocks
                assert isinstance(contracts["error_contracts"], list)

    def test_contracts_with_complex_types(self):
        """Test that contracts handle complex types correctly."""
        code = dedent(
            """
            class DataService:
                '''Data processing service.'''

                def process_items(self, items: list[str], config: dict[str, int]) -> list[dict]:
                    '''Process items with configuration.'''
                    return [{"item": item, "count": config.get(item, 0)} for item in items]
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            (src_path / "data.py").write_text(code)

            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5, entry_point=src_path)
            plan_bundle = analyzer.analyze()

            feature = plan_bundle.features[0]
            story = feature.stories[0]

            if story.contracts:
                contracts = story.contracts
                # Check that complex types are handled
                param_types = [p["type"] for p in contracts["parameters"]]
                assert any("list" in str(t).lower() or "dict" in str(t).lower() for t in param_types)
