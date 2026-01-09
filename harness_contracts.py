"""Generated sidecar harness for CrossHair validation."""
from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure, require

try:
    from common import adapters as sidecar_adapters
except ImportError:
    sidecar_adapters = None


@beartype
@require(lambda *args, **kwargs: True, 'Precondition placeholder')
@ensure(lambda result: True, 'Postcondition placeholder')
def harness_test_operation(*args: Any, **kwargs: Any) -> Any:
    """Harness for GET /test."""
    if sidecar_adapters:
        return sidecar_adapters.call_endpoint('GET', '/test', *args, **kwargs)
    return None
