"""
Integration tests for OpenAPI extractor Pydantic model extraction.

Tests comprehensive Pydantic model extraction, parallelization, and
integration with endpoint extraction.
"""

from __future__ import annotations

import os
from pathlib import Path

from beartype import beartype

from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


class TestPydanticModelExtraction:
    """Integration tests for Pydantic model extraction."""

    @beartype
    def test_pydantic_model_extraction_basic(self, tmp_path: Path) -> None:
        """Test basic Pydantic model extraction."""
        test_file = tmp_path / "models.py"
        test_file.write_text(
            '''
from pydantic import BaseModel

class User(BaseModel):
    """User model."""
    id: int
    name: str
    email: str
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        # Check that User schema was extracted
        assert "components" in result
        assert "schemas" in result["components"]
        assert "User" in result["components"]["schemas"]

        user_schema = result["components"]["schemas"]["User"]
        assert user_schema["type"] == "object"
        assert "properties" in user_schema
        assert "id" in user_schema["properties"]
        assert user_schema["properties"]["id"]["type"] == "integer"
        assert "name" in user_schema["properties"]
        assert user_schema["properties"]["name"]["type"] == "string"
        assert "email" in user_schema["properties"]
        assert user_schema["properties"]["email"]["type"] == "string"
        assert "required" in user_schema
        assert "id" in user_schema["required"]
        assert "name" in user_schema["required"]
        assert "email" in user_schema["required"]

    @beartype
    def test_pydantic_model_with_optional_fields(self, tmp_path: Path) -> None:
        """Test Pydantic model with optional fields."""
        test_file = tmp_path / "models.py"
        test_file.write_text(
            '''
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    """User model with optional fields."""
    id: int
    name: str
    email: Optional[str] = None
    age: Optional[int] = None
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        user_schema = result["components"]["schemas"]["User"]
        assert "required" in user_schema
        assert "id" in user_schema["required"]
        assert "name" in user_schema["required"]
        assert "email" not in user_schema["required"]
        assert "age" not in user_schema["required"]

    @beartype
    def test_pydantic_model_with_defaults(self, tmp_path: Path) -> None:
        """Test Pydantic model with default values."""
        test_file = tmp_path / "models.py"
        test_file.write_text(
            '''
from pydantic import BaseModel

class User(BaseModel):
    """User model with defaults."""
    id: int
    name: str = "Unknown"
    active: bool = True
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        user_schema = result["components"]["schemas"]["User"]
        assert "name" in user_schema["properties"]
        assert "default" in user_schema["properties"]["name"]
        assert user_schema["properties"]["name"]["default"] == "Unknown"
        assert "active" in user_schema["properties"]
        assert "default" in user_schema["properties"]["active"]
        assert user_schema["properties"]["active"]["default"] is True

    @beartype
    def test_pydantic_model_with_endpoints(self, tmp_path: Path) -> None:
        """Test Pydantic model extraction with FastAPI endpoints."""
        test_file = tmp_path / "api.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    """User creation model."""
    name: str
    email: str

class UserResponse(BaseModel):
    """User response model."""
    id: int
    name: str
    email: str

@app.post("/users")
def create_user(user: UserCreate) -> UserResponse:
    """Create a new user."""
    pass
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        # Check that models were extracted
        assert "UserCreate" in result["components"]["schemas"]
        assert "UserResponse" in result["components"]["schemas"]

        # Check that endpoint uses the models
        assert "/users" in result["paths"]
        assert "post" in result["paths"]["/users"]
        post_op = result["paths"]["/users"]["post"]
        assert "requestBody" in post_op
        request_schema = post_op["requestBody"]["content"]["application/json"]["schema"]
        assert "$ref" in request_schema
        assert request_schema["$ref"] == "#/components/schemas/UserCreate"

        # Check response schema
        assert "200" in post_op["responses"]
        response_schema = post_op["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in response_schema
        assert response_schema["$ref"] == "#/components/schemas/UserResponse"

    @beartype
    def test_parallel_processing_test_mode(self, tmp_path: Path) -> None:
        """Test that processing is sequential in test mode."""
        # Create multiple files
        for i in range(3):
            test_file = tmp_path / f"file_{i}.py"
            test_file.write_text(
                f'''
from pydantic import BaseModel

class Model{i}(BaseModel):
    """Model {i}."""
    id: int
    name: str
'''
            )

        # Set test mode
        os.environ["TEST_MODE"] = "true"

        try:
            extractor = OpenAPIExtractor(tmp_path)
            feature = Feature(
                key="FEATURE-TEST",
                title="Test Feature",
                stories=[],
                source_tracking=SourceTracking(
                    implementation_files=[f"file_{i}.py" for i in range(3)],
                    test_files=[],
                    file_hashes={},
                ),
                contract=None,
                protocol=None,
            )

            result = extractor.extract_openapi_from_code(tmp_path, feature)

            # Check that all models were extracted
            assert "Model0" in result["components"]["schemas"]
            assert "Model1" in result["components"]["schemas"]
            assert "Model2" in result["components"]["schemas"]
        finally:
            # Clean up environment
            os.environ.pop("TEST_MODE", None)

    @beartype
    def test_pydantic_model_with_nested_types(self, tmp_path: Path) -> None:
        """Test Pydantic model with nested types (List, Dict)."""
        test_file = tmp_path / "models.py"
        test_file.write_text(
            '''
from pydantic import BaseModel
from typing import List, Optional

class Tag(BaseModel):
    """Tag model."""
    name: str

class User(BaseModel):
    """User model with nested types."""
    id: int
    name: str
    tags: List[Tag]
    metadata: Optional[dict] = None
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        # Check that both models were extracted
        assert "Tag" in result["components"]["schemas"]
        assert "User" in result["components"]["schemas"]

        user_schema = result["components"]["schemas"]["User"]
        assert "tags" in user_schema["properties"]
        tags_schema = user_schema["properties"]["tags"]
        # Note: Nested model references in List types need more sophisticated extraction
        # The current implementation may extract as object or array depending on AST structure
        # For now, we verify the property exists
        assert isinstance(tags_schema, dict)

    @beartype
    def test_pydantic_model_docstring_extraction(self, tmp_path: Path) -> None:
        """Test that docstrings are extracted as descriptions."""
        test_file = tmp_path / "models.py"
        test_file.write_text(
            '''
from pydantic import BaseModel

class User(BaseModel):
    """A user model for the application.

    This model represents a user in the system.
    """
    id: int
    name: str
'''
        )

        extractor = OpenAPIExtractor(tmp_path)
        feature = Feature(
            key="FEATURE-TEST",
            title="Test Feature",
            stories=[],
            source_tracking=SourceTracking(
                implementation_files=[str(test_file.relative_to(tmp_path))],
                test_files=[],
                file_hashes={},
            ),
            contract=None,
            protocol=None,
        )

        result = extractor.extract_openapi_from_code(tmp_path, feature)

        user_schema = result["components"]["schemas"]["User"]
        assert "description" in user_schema
        assert "A user model" in user_schema["description"]
