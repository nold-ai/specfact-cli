"""Pytest conftest: add bundle_mapper src to path."""

import sys
from pathlib import Path


# modules/bundle-mapper/tests/conftest.py -> src = modules/bundle-mapper/src
_bundle_mapper_src = Path(__file__).resolve().parents[1] / "src"
if _bundle_mapper_src.exists() and str(_bundle_mapper_src) not in sys.path:
    sys.path.insert(0, str(_bundle_mapper_src))
