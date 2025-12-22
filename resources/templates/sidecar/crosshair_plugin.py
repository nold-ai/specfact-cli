"""
CrossHair plugin template for registering contracts without source edits.

Use with: python -m crosshair check --extra_plugin crosshair_plugin.py <targets>
"""

import importlib
from collections.abc import Callable
from typing import Any, cast

from crosshair.register_contract import register_contract


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def _post_is_not_none(result: object) -> bool:
    return result is not None


def plugin() -> None:
    """
    Register contracts dynamically for target functions.

    Replace the target import and constraints below.
    """
    target_module = "your_package.your_module"
    target_function = "your_function"

    module = importlib.import_module(target_module)
    func = cast(Callable[..., Any], getattr(module, target_function))

    register_contract(func, pre=_is_non_empty_str, post=_post_is_not_none)
