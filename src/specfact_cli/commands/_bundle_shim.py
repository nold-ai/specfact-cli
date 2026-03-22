"""Helpers for lazy-loading compatibility shims that point to bundle packages."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from icontract import ensure, require

from ..modules._bundle_import import bootstrap_local_bundle_sources


def _bundle_anchor_nonempty(anchor_file: str) -> bool:
    return anchor_file.strip() != ""


def _bundle_target_module_nonempty(target_module: str) -> bool:
    return target_module.strip() != ""


@require(_bundle_anchor_nonempty, "anchor_file must not be empty")
@require(_bundle_target_module_nonempty, "target_module must not be empty")
@ensure(lambda result: result is not None, "Must return app object")
def load_bundle_app(anchor_file: str, target_module: str) -> Any:
    """Load and return the lazily imported `app` object from a bundle command module."""
    bootstrap_local_bundle_sources(anchor_file)
    return import_module(target_module).app
