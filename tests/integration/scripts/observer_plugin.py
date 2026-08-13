"""Record the repository-local files a pytest run actually imports and reads.

Loaded with ``-p`` from outside the repository under test, so the observation does not alter
the layout being observed.

Two things are recorded, because the gate binds two kinds of input. Imported modules are read
off ``sys.modules`` at session finish. Files opened for reading are captured by an audit hook,
which is the only way to see a fixture reading ``tests/data/case.json`` — that read leaves no
trace in ``sys.modules`` and is precisely where the path-resolution rules are exercised.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


_OPENED: set[str] = set()
_REPOSITORY_ROOT = os.path.realpath(os.environ["OBSERVE_ROOT"])
# Directories a run writes to or populates itself. They are not repository inputs, and a gate
# cannot bind them because they are not committed.
_IGNORED_SEGMENTS = frozenset({".git", "__pycache__", ".pytest_cache"})


def _repository_relative(path: str) -> str | None:
    """Return a path relative to the observed repository, or ``None`` when it lies outside."""
    try:
        relative = os.path.relpath(os.path.realpath(path), _REPOSITORY_ROOT)
    except (OSError, ValueError):
        return None
    if relative.startswith(os.pardir) or os.path.isabs(relative):
        return None
    posix = relative.replace(os.sep, "/")
    if any(segment in _IGNORED_SEGMENTS for segment in posix.split("/")):
        return None
    return posix


def _record_open(event: str, arguments: tuple[Any, ...]) -> None:
    """Record repository files opened for reading."""
    if event != "open" or not arguments:
        return
    path = arguments[0]
    if not isinstance(path, (str, bytes, os.PathLike)):
        return
    mode = arguments[1] if len(arguments) > 1 else "r"
    if isinstance(mode, str) and ("w" in mode or "a" in mode or "x" in mode):
        return
    relative = _repository_relative(os.fsdecode(path))
    if relative is not None:
        _OPENED.add(relative)


sys.addaudithook(_record_open)


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    """Write every repository-local file the run imported or read."""
    imported: set[str] = set()
    for module in list(sys.modules.values()):
        file_name = getattr(module, "__file__", None)
        if not file_name:
            continue
        relative = _repository_relative(file_name)
        if relative is not None:
            imported.add(relative)
    observation = {"imported": sorted(imported), "read": sorted(_OPENED)}
    with open(os.environ["OBSERVE_OUT"], "w", encoding="utf-8") as handle:
        json.dump(observation, handle)
