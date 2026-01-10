"""
Unit tests for FastAPI framework extractor.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.validators.sidecar.frameworks.fastapi import FastAPIExtractor


def test_fastapi_extractor_detect(tmp_path: Path) -> None:
    """Test FastAPI extractor detection."""
    # Create main.py with FastAPI
    main_py = tmp_path / "main.py"
    main_py.write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    extractor = FastAPIExtractor()
    assert extractor.detect(tmp_path) is True


def test_fastapi_extractor_detect_not_fastapi(tmp_path: Path) -> None:
    """Test FastAPI extractor detection when FastAPI is not present."""
    # Create regular Python file
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    extractor = FastAPIExtractor()
    assert extractor.detect(tmp_path) is False


def test_fastapi_extractor_extract_routes(tmp_path: Path) -> None:
    """Test FastAPI extractor route extraction."""
    extractor = FastAPIExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert isinstance(routes, list)


def test_fastapi_extractor_extract_schemas(tmp_path: Path) -> None:
    """Test FastAPI extractor schema extraction."""
    from specfact_cli.validators.sidecar.frameworks.base import RouteInfo

    extractor = FastAPIExtractor()
    routes: list[RouteInfo] = []
    schemas = extractor.extract_schemas(tmp_path, routes)
    assert isinstance(schemas, dict)
