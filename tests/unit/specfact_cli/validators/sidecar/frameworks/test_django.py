"""
Unit tests for Django framework extractor.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.validators.sidecar.frameworks.django import DjangoExtractor


def test_django_extractor_detect(tmp_path: Path) -> None:
    """Test Django extractor detection."""
    # Create manage.py
    manage_py = tmp_path / "manage.py"
    manage_py.write_text("import django\n")

    extractor = DjangoExtractor()
    assert extractor.detect(tmp_path) is True


def test_django_extractor_detect_not_django(tmp_path: Path) -> None:
    """Test Django extractor detection when Django is not present."""
    # Create regular Python file
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    extractor = DjangoExtractor()
    assert extractor.detect(tmp_path) is False


def test_django_extractor_extract_routes_no_urls(tmp_path: Path) -> None:
    """Test Django extractor with no urls.py file."""
    extractor = DjangoExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert routes == []


def test_django_extractor_extract_schemas(tmp_path: Path) -> None:
    """Test Django extractor schema extraction."""
    from specfact_cli.validators.sidecar.frameworks.base import RouteInfo

    extractor = DjangoExtractor()
    routes: list[RouteInfo] = []
    schemas = extractor.extract_schemas(tmp_path, routes)
    assert isinstance(schemas, dict)
