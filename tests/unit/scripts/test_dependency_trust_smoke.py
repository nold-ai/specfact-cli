"""An auxiliary lock must not escape the existing executable-wheel prohibition."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import scripts.check_dependency_trust_exceptions as checker


def test_runtime_smoke_lock_rejects_unofficial_node_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "requirements.in"
    source.write_text("nodejs-wheel-binaries==24.19.0\n")
    locked = tmp_path / "locked.txt"
    locked.write_text(
        "# input-sha256: "
        + hashlib.sha256(source.read_bytes()).hexdigest()
        + "\nnodejs-wheel-binaries==24.19.0 \\\n    --hash=sha256:"
        + "a" * 64
        + "\n"
    )
    monkeypatch.setattr(checker, "DEFAULT_RUNTIME_SMOKE_INPUT", source)
    monkeypatch.setattr(checker, "DEFAULT_RUNTIME_SMOKE_LOCK", locked)
    errors = checker.validate_frozen_dependency_policy()
    assert "nodejs-wheel-binaries==24.19.0 is prohibited in the frozen lock" in errors
