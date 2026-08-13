"""Record the repository-local files a pytest run actually imported.

Loaded with ``-p`` from outside the repository under test, so the observation does not alter
the layout being observed.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    """Write every module file loaded from inside the observed repository."""
    repository_root = os.path.realpath(os.environ["OBSERVE_ROOT"])
    observed: set[str] = set()
    for module in list(sys.modules.values()):
        file_name = getattr(module, "__file__", None)
        if not file_name:
            continue
        relative = os.path.relpath(os.path.realpath(file_name), repository_root)
        if not relative.startswith(os.pardir) and not os.path.isabs(relative):
            observed.add(relative.replace(os.sep, "/"))
    with open(os.environ["OBSERVE_OUT"], "w", encoding="utf-8") as handle:
        json.dump(sorted(observed), handle)
