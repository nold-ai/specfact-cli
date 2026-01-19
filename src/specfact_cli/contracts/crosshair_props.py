"""CrossHair property-based tests for pure helpers.

CrossHair property test
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda value: isinstance(value, str) and value.strip() != "", "Value must be non-empty string")
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "Result must be non-empty string")
def normalize_provider_contract(value: str) -> str:
    """CrossHair property test for provider normalization."""
    return value.strip().lower().replace("_", "-").replace(" ", "-")


@beartype
@require(lambda value: isinstance(value, int), "Value must be int")
@ensure(lambda result: isinstance(result, int), "Result must be int")
def clamp_timeout_contract(value: int) -> int:
    """CrossHair property test for timeout clamping."""
    return max(1, min(value, 300))
