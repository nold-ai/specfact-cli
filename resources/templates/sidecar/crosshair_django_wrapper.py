#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
Django-aware CrossHair wrapper for source code analysis.

This wrapper initializes Django's app registry before running CrossHair,
enabling analysis of Django models and views that require the app registry to be ready.

Usage:
    python crosshair_django_wrapper.py <crosshair_args> <source_dirs>

Example:
    python crosshair_django_wrapper.py check --verbose /path/to/django/app
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _initialize_django(repo_path: Path | None = None) -> None:
    """
    Initialize Django's app registry before CrossHair analysis.

    Args:
        repo_path: Optional path to Django repository root.
                   If not provided, attempts to infer from current directory or environment.
    """
    # Check if Django is available
    try:
        import django
    except ImportError:
        print("Warning: Django not available, skipping Django initialization", file=sys.stderr)
        return

    # Set Django settings module if not already set
    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not django_settings:
        # Try to infer from repo structure
        if repo_path:
            # Common Django project structure: <project_name>/settings.py
            settings_candidates = [
                repo_path / "settings.py",
                repo_path / "config" / "settings.py",
                repo_path / "project" / "settings.py",
            ]
            for candidate in settings_candidates:
                if candidate.exists():
                    # Infer module path from file location
                    # e.g., /path/to/djangogoat/settings.py -> djangogoat.settings
                    relative = candidate.relative_to(repo_path.parent)
                    module_path = str(relative.with_suffix("")).replace(os.sep, ".")
                    os.environ.setdefault("DJANGO_SETTINGS_MODULE", module_path)
                    break

        # If still not set, try common patterns
        if not os.environ.get("DJANGO_SETTINGS_MODULE") and repo_path:
            # Check for manage.py to infer project name
            manage_py = repo_path / "manage.py"
            if manage_py.exists():
                # Read manage.py to find settings module
                try:
                    content = manage_py.read_text(encoding="utf-8")
                    # Look for DJANGO_SETTINGS_MODULE or os.environ.setdefault
                    import re

                    match = re.search(r"DJANGO_SETTINGS_MODULE\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if match:
                        os.environ.setdefault("DJANGO_SETTINGS_MODULE", match.group(1))
                    else:
                        # Fallback: assume project name matches directory name
                        project_name = repo_path.name
                        os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")
                except Exception:
                    # Fallback: assume project name matches directory name
                    project_name = repo_path.name
                    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")

    # Initialize Django
    try:
        django.setup()
        print(f"Django initialized with settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Django setup failed: {e}", file=sys.stderr)
        print("CrossHair will continue, but Django models may not be analyzable", file=sys.stderr)


def main() -> int:
    """Main entry point for Django-aware CrossHair wrapper."""
    # Parse arguments
    # Format: crosshair_django_wrapper.py <crosshair_args> <source_dirs>
    # We need to separate CrossHair arguments from source directories
    if len(sys.argv) < 2:
        print("Usage: crosshair_django_wrapper.py <crosshair_args> <source_dirs>", file=sys.stderr)
        return 1

    # Try to find repo path from environment or current directory
    repo_path: Path | None = None
    repo_path_str = os.environ.get("REPO_PATH")
    if repo_path_str:
        repo_path = Path(repo_path_str).resolve()
    else:
        # Try to infer from current working directory
        cwd = Path.cwd()
        # Look for manage.py or settings.py
        if (cwd / "manage.py").exists() or (cwd / "settings.py").exists():
            repo_path = cwd
        else:
            # Try parent directories
            for parent in cwd.parents:
                if (parent / "manage.py").exists() or (parent / "settings.py").exists():
                    repo_path = parent
                    break

    # Initialize Django before importing CrossHair
    _initialize_django(repo_path)

    # Now import and run CrossHair
    try:
        from crosshair.main import main as crosshair_main

        # CrossHair's main expects sys.argv to be set up correctly
        # We pass all arguments except our script name
        result = crosshair_main()
        # Ensure we always return an int (CrossHair may return None)
        if result is None:
            return 0
        return result if isinstance(result, int) else 1
    except ImportError:
        print("Error: CrossHair not available. Install with: pip install crosshair-tool", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running CrossHair: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
