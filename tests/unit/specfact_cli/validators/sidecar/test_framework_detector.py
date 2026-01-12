"""
Unit tests for framework detection logic.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.validators.sidecar.framework_detector import (
    detect_django_settings_module,
    detect_framework,
)
from specfact_cli.validators.sidecar.models import FrameworkType


def test_detect_framework_django(tmp_path: Path) -> None:
    """Test Django framework detection."""
    # Create manage.py file
    manage_py = tmp_path / "manage.py"
    manage_py.write_text("import django\n")

    result = detect_framework(tmp_path)
    assert result == FrameworkType.DJANGO


def test_detect_framework_fastapi(tmp_path: Path) -> None:
    """Test FastAPI framework detection."""
    # Create main.py with FastAPI
    main_py = tmp_path / "main.py"
    main_py.write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    result = detect_framework(tmp_path)
    assert result == FrameworkType.FASTAPI


def test_detect_framework_pure_python(tmp_path: Path) -> None:
    """Test pure Python detection (no framework)."""
    # Create regular Python file
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    result = detect_framework(tmp_path)
    assert result == FrameworkType.PURE_PYTHON


def test_detect_framework_flask(tmp_path: Path) -> None:
    """Test Flask detection (should return FLASK)."""
    # Create Flask app file
    app_py = tmp_path / "app.py"
    app_py.write_text("from flask import Flask\napp = Flask(__name__)\n")

    result = detect_framework(tmp_path)
    assert result == FrameworkType.FLASK


def test_detect_framework_flask_before_django_urls(tmp_path: Path) -> None:
    """Test Flask detection takes priority over Django urls.py files."""
    # Create Flask app
    app_py = tmp_path / "app.py"
    app_py.write_text("from flask import Flask\napp = Flask(__name__)\n")

    # Create urls.py file (which would trigger Django detection)
    urls_py = tmp_path / "urls.py"
    urls_py.write_text("# This should not trigger Django detection if Flask is present\n")

    result = detect_framework(tmp_path)
    # Flask should be detected and return FLASK, not DJANGO
    assert result == FrameworkType.FLASK


def test_detect_django_settings_module(tmp_path: Path) -> None:
    """Test Django settings module detection."""
    # Create manage.py with settings module in assignment format
    manage_py = tmp_path / "manage.py"
    manage_py.write_text('DJANGO_SETTINGS_MODULE = "myproject.settings"\n')

    result = detect_django_settings_module(tmp_path)
    assert result == "myproject.settings"


def test_detect_django_settings_module_not_found(tmp_path: Path) -> None:
    """Test Django settings module detection when not found."""
    # Create regular file (not manage.py)
    main_py = tmp_path / "main.py"
    main_py.write_text("print('hello')\n")

    result = detect_django_settings_module(tmp_path)
    assert result is None
