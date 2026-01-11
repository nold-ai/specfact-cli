"""
Unit tests for Flask framework extractor.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.validators.sidecar.frameworks.base import RouteInfo
from specfact_cli.validators.sidecar.frameworks.flask import FlaskExtractor


def test_flask_extractor_detect(tmp_path: Path) -> None:
    """Test Flask extractor detection."""
    # Create app.py with Flask
    app_py = tmp_path / "app.py"
    app_py.write_text("from flask import Flask\napp = Flask(__name__)\n")

    extractor = FlaskExtractor()
    assert extractor.detect(tmp_path) is True


def test_flask_extractor_detect_import_flask(tmp_path: Path) -> None:
    """Test Flask extractor detection with import flask pattern."""
    # Create app.py with import flask
    app_py = tmp_path / "app.py"
    app_py.write_text("import flask\napp = flask.Flask(__name__)\n")

    extractor = FlaskExtractor()
    assert extractor.detect(tmp_path) is True


def test_flask_extractor_detect_not_flask(tmp_path: Path) -> None:
    """Test Flask extractor detection when Flask is not present."""
    # Create regular Python file
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    extractor = FlaskExtractor()
    assert extractor.detect(tmp_path) is False


def test_flask_extractor_extract_routes_simple(tmp_path: Path) -> None:
    """Test Flask extractor route extraction from simple @app.route decorator."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World'

@app.route('/users', methods=['GET'])
def get_users():
    return []
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert len(routes) >= 2
    assert any(route.path == "/" and route.method == "GET" for route in routes)
    assert any(route.path == "/users" and route.method == "GET" for route in routes)


def test_flask_extractor_extract_routes_with_path_params(tmp_path: Path) -> None:
    """Test Flask extractor route extraction with path parameters."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/user/<int:id>')
def get_user(id):
    return {'id': id}

@app.route('/post/<slug>')
def get_post(slug):
    return {'slug': slug}
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert len(routes) >= 2

    # Check path parameter conversion
    user_route = next((r for r in routes if "/user" in r.path), None)
    assert user_route is not None
    assert user_route.path == "/user/{id}"
    assert len(user_route.path_params) == 1
    assert user_route.path_params[0]["name"] == "id"
    assert user_route.path_params[0]["schema"]["type"] == "integer"

    post_route = next((r for r in routes if "/post" in r.path), None)
    assert post_route is not None
    assert post_route.path == "/post/{slug}"
    assert len(post_route.path_params) == 1
    assert post_route.path_params[0]["name"] == "slug"
    assert post_route.path_params[0]["schema"]["type"] == "string"


def test_flask_extractor_extract_routes_blueprint(tmp_path: Path) -> None:
    """Test Flask extractor route extraction from Blueprint."""
    # Create Blueprint file
    bp_py = tmp_path / "routes.py"
    bp_py.write_text(
        """from flask import Blueprint

bp = Blueprint('api', __name__)

@bp.route('/api/users')
def get_users():
    return []
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    # Blueprint routes should be extracted
    assert len(routes) >= 1
    assert any(route.path == "/api/users" for route in routes)


def test_flask_extractor_extract_routes_multiple_methods(tmp_path: Path) -> None:
    """Test Flask extractor route extraction with multiple HTTP methods."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/users', methods=['GET', 'POST'])
def users():
    return []
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert len(routes) >= 1
    # Should extract at least one route (first method)
    assert any(route.path == "/users" for route in routes)


def test_flask_extractor_path_parameter_int(tmp_path: Path) -> None:
    """Test Flask path parameter conversion: <int:id> -> {id} with type integer."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/user/<int:id>')
def get_user(id):
    return {'id': id}
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    route = next((r for r in routes if "/user" in r.path), None)
    assert route is not None
    assert route.path == "/user/{id}"
    assert route.path_params[0]["schema"]["type"] == "integer"


def test_flask_extractor_path_parameter_float(tmp_path: Path) -> None:
    """Test Flask path parameter conversion: <float:value> -> {value} with type number."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/value/<float:value>')
def get_value(value):
    return {'value': value}
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    route = next((r for r in routes if "/value" in r.path), None)
    assert route is not None
    assert route.path == "/value/{value}"
    assert route.path_params[0]["schema"]["type"] == "number"


def test_flask_extractor_path_parameter_path(tmp_path: Path) -> None:
    """Test Flask path parameter conversion: <path:path> -> {path} with type string."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/files/<path:filepath>')
def get_file(filepath):
    return {'path': filepath}
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    route = next((r for r in routes if "/files" in r.path), None)
    assert route is not None
    assert route.path == "/files/{filepath}"
    assert route.path_params[0]["schema"]["type"] == "string"


def test_flask_extractor_path_parameter_slug(tmp_path: Path) -> None:
    """Test Flask path parameter conversion: <slug> -> {slug} with type string."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/post/<slug>')
def get_post(slug):
    return {'slug': slug}
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    route = next((r for r in routes if "/post" in r.path), None)
    assert route is not None
    assert route.path == "/post/{slug}"
    assert route.path_params[0]["schema"]["type"] == "string"


def test_flask_extractor_extract_schemas(tmp_path: Path) -> None:
    """Test Flask extractor schema extraction."""
    extractor = FlaskExtractor()
    routes: list[RouteInfo] = []
    schemas = extractor.extract_schemas(tmp_path, routes)
    assert isinstance(schemas, dict)
    assert len(schemas) == 0  # Currently returns empty dict


def test_flask_extractor_operation_id(tmp_path: Path) -> None:
    """Test Flask extractor sets operation_id from function name."""
    app_py = tmp_path / "app.py"
    app_py.write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/users')
def get_all_users():
    return []
"""
    )

    extractor = FlaskExtractor()
    routes = extractor.extract_routes(tmp_path)
    route = next((r for r in routes if "/users" in r.path), None)
    assert route is not None
    assert route.operation_id == "get_all_users"
    assert route.function == "get_all_users"
