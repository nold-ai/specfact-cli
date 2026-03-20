"""Helpers for lazy-loading compatibility shims that point to bundle packages."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from icontract import ensure, require

from ..modules._bundle_import import bootstrap_local_bundle_sources


@require(lambda anchor_file: anchor_file.strip() != "", "anchor_file must not be empty")
@require(lambda target_module: target_module.strip() != "", "target_module must not be empty")
@ensure(lambda result: result is not None, "Must return app object")
def load_bundle_app(anchor_file: str, target_module: str) -> Any:
    """Load and return the lazily imported `app` object from a bundle command module."""
    bootstrap_local_bundle_sources(anchor_file)
    return import_module(target_module).app
