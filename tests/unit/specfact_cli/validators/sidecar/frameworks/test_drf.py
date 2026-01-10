"""
Unit tests for DRF framework extractor.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.validators.sidecar.frameworks.drf import DRFExtractor


def test_drf_extractor_detect(tmp_path: Path) -> None:
    """Test DRF extractor detection."""
    # Create Python file with rest_framework import
    views_py = tmp_path / "views.py"
    views_py.write_text("from rest_framework import serializers\n")

    extractor = DRFExtractor()
    assert extractor.detect(tmp_path) is True


def test_drf_extractor_detect_not_drf(tmp_path: Path) -> None:
    """Test DRF extractor detection when DRF is not present."""
    # Create regular Python file
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    extractor = DRFExtractor()
    assert extractor.detect(tmp_path) is False


def test_drf_extractor_extract_routes(tmp_path: Path) -> None:
    """Test DRF extractor route extraction."""
    # Create manage.py for Django
    manage_py = tmp_path / "manage.py"
    manage_py.write_text("import django\n")

    extractor = DRFExtractor()
    routes = extractor.extract_routes(tmp_path)
    assert isinstance(routes, list)


def test_drf_extractor_extract_schemas(tmp_path: Path) -> None:
    """Test DRF extractor schema extraction."""
    from specfact_cli.validators.sidecar.frameworks.base import RouteInfo

    extractor = DRFExtractor()
    routes: list[RouteInfo] = []
    schemas = extractor.extract_schemas(tmp_path, routes)
    assert isinstance(schemas, dict)
