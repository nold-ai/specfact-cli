"""
Tests for OpenAPI extractor enhancements.

Tests Flask route extraction, FastAPI router support, path parameter extraction,
and test example integration.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


class TestOpenAPIExtractorEnhancements:
    """Tests for enhanced OpenAPI extraction capabilities."""

    @beartype
    def test_flask_route_extraction(self, tmp_path: Path) -> None:
        """Test Flask route extraction with methods."""
        # Create test file with Flask routes
        test_file = tmp_path / "flask_app.py"
        test_file.write_text(
            '''
from flask import Flask
app = Flask(__name__)

@app.route("/users", methods=["GET"])
def get_users():
    """Get all users."""
    pass

@app.route("/users/<int:user_id>", methods=["GET", "DELETE"])
def user_operations(user_id):
    """User operations."""
    pass

@app.route("/users", methods=["POST"])
def create_user():
    """Create user."""
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

        # Check that routes were extracted
        assert "/users" in result["paths"]
        assert "get" in result["paths"]["/users"]
        assert "post" in result["paths"]["/users"]

        # Check path parameters for /users/{user_id}
        assert "/users/{user_id}" in result["paths"]
        assert "get" in result["paths"]["/users/{user_id}"]
        assert "delete" in result["paths"]["/users/{user_id}"]

        # Check path parameters
        get_op = result["paths"]["/users/{user_id}"]["get"]
        assert "parameters" in get_op
        assert len(get_op["parameters"]) == 1
        assert get_op["parameters"][0]["name"] == "user_id"
        assert get_op["parameters"][0]["in"] == "path"
        assert get_op["parameters"][0]["schema"]["type"] == "integer"

    @beartype
    def test_fastapi_router_support(self, tmp_path: Path) -> None:
        """Test FastAPI router with prefix and tags."""
        # Create test file with FastAPI router
        test_file = tmp_path / "fastapi_router.py"
        test_file.write_text(
            '''
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["users"])

@router.get("/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID."""
    pass

@router.post("/users")
def create_user():
    """Create user."""
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

        # Check that router prefix was applied
        assert "/api/v1/users" in result["paths"]
        assert "/api/v1/users/{user_id}" in result["paths"]

        # Check that router tags were applied
        get_op = result["paths"]["/api/v1/users/{user_id}"]["get"]
        assert "tags" in get_op
        assert get_op["tags"] == ["users"]

        # Check path parameters
        assert "parameters" in get_op
        assert len(get_op["parameters"]) == 1
        assert get_op["parameters"][0]["name"] == "user_id"
        assert get_op["parameters"][0]["in"] == "path"

    @beartype
    def test_path_parameter_extraction_fastapi(self, tmp_path: Path) -> None:
        """Test path parameter extraction for FastAPI format."""
        test_file = tmp_path / "fastapi_paths.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: str):
    """Get user post."""
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

        assert "/users/{user_id}/posts/{post_id}" in result["paths"]
        op = result["paths"]["/users/{user_id}/posts/{post_id}"]["get"]
        assert "parameters" in op
        assert len(op["parameters"]) == 2
        param_names = [p["name"] for p in op["parameters"]]
        assert "user_id" in param_names
        assert "post_id" in param_names

    @beartype
    def test_path_parameter_extraction_flask(self, tmp_path: Path) -> None:
        """Test path parameter extraction for Flask format."""
        test_file = tmp_path / "flask_paths.py"
        test_file.write_text(
            '''
from flask import Flask
app = Flask(__name__)

@app.route("/users/<int:user_id>/posts/<post_id>", methods=["GET"])
def get_user_post(user_id, post_id):
    """Get user post."""
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

        assert "/users/{user_id}/posts/{post_id}" in result["paths"]
        op = result["paths"]["/users/{user_id}/posts/{post_id}"]["get"]
        assert "parameters" in op
        assert len(op["parameters"]) == 2
        # Check types: user_id should be integer, post_id should be string
        for param in op["parameters"]:
            if param["name"] == "user_id":
                assert param["schema"]["type"] == "integer"
            elif param["name"] == "post_id":
                assert param["schema"]["type"] == "string"

    @beartype
    def test_extract_path_parameters_method(self, tmp_path: Path) -> None:
        """Test _extract_path_parameters method directly."""
        extractor = OpenAPIExtractor(tmp_path)

        # Test FastAPI format
        path, params = extractor._extract_path_parameters("/users/{user_id}")
        assert path == "/users/{user_id}"
        assert len(params) == 1
        assert params[0]["name"] == "user_id"
        assert params[0]["in"] == "path"
        assert params[0]["schema"]["type"] == "string"

        # Test Flask format
        path, params = extractor._extract_path_parameters("/users/<int:user_id>", flask_format=True)
        assert path == "/users/{user_id}"
        assert len(params) == 1
        assert params[0]["name"] == "user_id"
        assert params[0]["in"] == "path"
        assert params[0]["schema"]["type"] == "integer"

        # Test Flask format without type
        path, params = extractor._extract_path_parameters("/users/<user_id>", flask_format=True)
        assert path == "/users/{user_id}"
        assert len(params) == 1
        assert params[0]["schema"]["type"] == "string"

    @beartype
    def test_query_parameter_extraction(self, tmp_path: Path) -> None:
        """Test query parameter extraction from function parameters."""
        test_file = tmp_path / "query_params.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users(limit: int = 10, offset: int = 0, search: str = ""):
    """Get users with pagination and search."""
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

        assert "/users" in result["paths"]
        op = result["paths"]["/users"]["get"]
        assert "parameters" in op
        assert len(op["parameters"]) == 3

        param_names = [p["name"] for p in op["parameters"]]
        assert "limit" in param_names
        assert "offset" in param_names
        assert "search" in param_names

        # Check query parameter properties
        for param in op["parameters"]:
            assert param["in"] == "query"
            assert param["required"] is False
            assert "schema" in param

    @beartype
    def test_request_body_extraction(self, tmp_path: Path) -> None:
        """Test request body extraction from function parameters."""
        test_file = tmp_path / "request_body.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
from typing import Optional

app = FastAPI()

class UserCreate:
    name: str
    email: str
    age: Optional[int] = None

@app.post("/users")
def create_user(user: UserCreate):
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

        assert "/users" in result["paths"]
        op = result["paths"]["/users"]["post"]
        assert "requestBody" in op
        assert op["requestBody"]["required"] is True
        assert "content" in op["requestBody"]
        assert "application/json" in op["requestBody"]["content"]
        assert "schema" in op["requestBody"]["content"]["application/json"]

    @beartype
    def test_response_schema_extraction(self, tmp_path: Path) -> None:
        """Test response schema extraction from return type hints."""
        test_file = tmp_path / "response_schema.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
from typing import List

app = FastAPI()

class User:
    id: int
    name: str

@app.get("/users")
def get_users() -> List[User]:
    """Get all users."""
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

        assert "/users" in result["paths"]
        op = result["paths"]["/users"]["get"]
        assert "responses" in op
        assert "200" in op["responses"]
        assert "content" in op["responses"]["200"]
        assert "application/json" in op["responses"]["200"]["content"]
        assert "schema" in op["responses"]["200"]["content"]["application/json"]

    @beartype
    def test_type_hint_extraction_basic_types(self, tmp_path: Path) -> None:
        """Test type hint extraction for basic types."""
        extractor = OpenAPIExtractor(tmp_path)

        # Test basic types
        import ast

        str_type = ast.Name(id="str")
        schema = extractor._extract_type_hint_schema(str_type)
        assert schema == {"type": "string"}

        int_type = ast.Name(id="int")
        schema = extractor._extract_type_hint_schema(int_type)
        assert schema == {"type": "integer"}

        bool_type = ast.Name(id="bool")
        schema = extractor._extract_type_hint_schema(bool_type)
        assert schema == {"type": "boolean"}

    @beartype
    def test_type_hint_extraction_list_types(self, tmp_path: Path) -> None:
        """Test type hint extraction for List types."""
        extractor = OpenAPIExtractor(tmp_path)
        import ast

        # Test List[str]
        list_type = ast.Subscript(
            value=ast.Name(id="list"),
            slice=ast.Name(id="str"),
        )
        schema = extractor._extract_type_hint_schema(list_type)
        assert schema == {"type": "array", "items": {"type": "string"}}

        # Test List[int]
        list_int = ast.Subscript(
            value=ast.Name(id="list"),
            slice=ast.Name(id="int"),
        )
        schema = extractor._extract_type_hint_schema(list_int)
        assert schema == {"type": "array", "items": {"type": "integer"}}

    @beartype
    def test_type_hint_extraction_optional_types(self, tmp_path: Path) -> None:
        """Test type hint extraction for Optional types."""
        extractor = OpenAPIExtractor(tmp_path)
        import ast

        # Test Optional[str]
        optional_type = ast.Subscript(
            value=ast.Name(id="Optional"),
            slice=ast.Name(id="str"),
        )
        schema = extractor._extract_type_hint_schema(optional_type)
        assert schema == {"type": "string"}

    @beartype
    def test_combined_path_query_and_body(self, tmp_path: Path) -> None:
        """Test extraction of path parameters, query parameters, and request body together."""
        test_file = tmp_path / "combined.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
app = FastAPI()

@app.put("/users/{user_id}")
def update_user(user_id: int, name: str = "", email: str = ""):
    """Update user with path param, query params."""
    pass

@app.post("/users/{user_id}/posts")
def create_post(user_id: int, title: str, content: str):
    """Create post with path param and body."""
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

        # Test PUT endpoint with path and query params
        assert "/users/{user_id}" in result["paths"]
        put_op = result["paths"]["/users/{user_id}"]["put"]
        assert "parameters" in put_op
        param_names = [p["name"] for p in put_op["parameters"]]
        assert "user_id" in param_names  # Path param
        assert "name" in param_names  # Query param
        assert "email" in param_names  # Query param

        # Test POST endpoint with path param and body
        assert "/users/{user_id}/posts" in result["paths"]
        post_op = result["paths"]["/users/{user_id}/posts"]["post"]
        assert "parameters" in post_op
        assert "user_id" in [p["name"] for p in post_op["parameters"]]
        assert "requestBody" in post_op

    @beartype
    def test_status_code_extraction(self, tmp_path: Path) -> None:
        """Test status code extraction from decorator."""
        test_file = tmp_path / "status_code.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
app = FastAPI()

@app.post("/users", status_code=201)
def create_user():
    """Create user with custom status code."""
    pass

@app.get("/users/{user_id}", status_code=200)
def get_user(user_id: int):
    """Get user."""
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

        # Check POST endpoint has 201 status code
        assert "/users" in result["paths"]
        post_op = result["paths"]["/users"]["post"]
        assert "responses" in post_op
        assert "201" in post_op["responses"]
        assert "200" not in post_op["responses"]  # Should not have default 200

        # Check GET endpoint has 200 status code
        assert "/users/{user_id}" in result["paths"]
        get_op = result["paths"]["/users/{user_id}"]["get"]
        assert "200" in get_op["responses"]

    @beartype
    def test_security_scheme_extraction(self, tmp_path: Path) -> None:
        """Test security scheme extraction from dependencies."""
        test_file = tmp_path / "security.py"
        test_file.write_text(
            '''
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/users", dependencies=[Depends(lambda: None)])
def get_users():
    """Get users with security."""
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

        # Check security scheme is defined
        assert "components" in result
        assert "securitySchemes" in result["components"]
        assert "bearerAuth" in result["components"]["securitySchemes"]

        # Check operation has security requirement
        assert "/users" in result["paths"]
        op = result["paths"]["/users"]["get"]
        assert "security" in op
        assert len(op["security"]) > 0

    @beartype
    def test_multiple_response_codes(self, tmp_path: Path) -> None:
        """Test that multiple response codes are added for different methods."""
        test_file = tmp_path / "multiple_responses.py"
        test_file.write_text(
            '''
from fastapi import FastAPI
app = FastAPI()

@app.post("/users")
def create_user():
    """Create user."""
    pass

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get user."""
    pass

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete user."""
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

        # Check POST has error responses
        post_op = result["paths"]["/users"]["post"]
        assert "400" in post_op["responses"]
        assert "422" in post_op["responses"]
        assert "401" in post_op["responses"]
        assert "500" in post_op["responses"]

        # Check GET has 404
        get_op = result["paths"]["/users/{user_id}"]["get"]
        assert "404" in get_op["responses"]

        # Check DELETE has 404, 401, 403
        delete_op = result["paths"]["/users/{user_id}"]["delete"]
        assert "404" in delete_op["responses"]
        assert "401" in delete_op["responses"]
        assert "403" in delete_op["responses"]

    @beartype
    def test_add_test_examples(self, tmp_path: Path) -> None:
        """Test adding test examples to OpenAPI specification."""
        extractor = OpenAPIExtractor(tmp_path)

        # Create a basic OpenAPI spec
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "post": {
                        "operationId": "post_api_users",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                    }
                                }
                            },
                        },
                        "responses": {
                            "201": {
                                "description": "Created",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"id": {"type": "integer"}},
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

        # Create test examples
        test_examples = {
            "post_api_users": {
                "request": {"body": {"name": "John", "email": "john@example.com"}},
                "response": {"id": 1, "name": "John", "email": "john@example.com"},
                "status_code": 201,
            }
        }

        # Add examples
        updated_spec = extractor.add_test_examples(openapi_spec, test_examples)

        # Verify examples were added
        operation = updated_spec["paths"]["/api/users"]["post"]
        request_content = operation["requestBody"]["content"]["application/json"]
        assert "examples" in request_content
        assert "test-example" in request_content["examples"]
        assert request_content["examples"]["test-example"]["value"] == {"name": "John", "email": "john@example.com"}

        response_content = operation["responses"]["201"]["content"]["application/json"]
        assert "examples" in response_content
        assert "test-example" in response_content["examples"]
        assert response_content["examples"]["test-example"]["value"] == {
            "id": 1,
            "name": "John",
            "email": "john@example.com",
        }

    @beartype
    def test_add_test_examples_no_matching_operation(self, tmp_path: Path) -> None:
        """Test adding test examples when no matching operation exists."""
        extractor = OpenAPIExtractor(tmp_path)

        openapi_spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "get": {
                        "operationId": "get_api_users",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }

        test_examples = {
            "post_api_users": {  # Different operation ID
                "request": {"body": {"name": "John"}},
                "response": {"id": 1},
                "status_code": 201,
            }
        }

        # Should not raise error, just skip non-matching operations
        updated_spec = extractor.add_test_examples(openapi_spec, test_examples)
        assert updated_spec == openapi_spec  # No changes
