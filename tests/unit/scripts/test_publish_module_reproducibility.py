"""Reproducibility coverage for immutable bundled-module releases."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "publish-module.py"


class PublishModule(Protocol):
    """Typed surface used by the reproducibility regression."""

    def _create_tarball(self, module_dir: Path, output_path: Path, name: str, version: str) -> Path:
        raise NotImplementedError


def _load_script_module() -> PublishModule:
    spec = importlib.util.spec_from_file_location("publish_module_reproducibility", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load publish-module.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(PublishModule, module)


def test_tarball_is_reproducible_across_git_invisible_attributes(tmp_path: Path) -> None:
    """Retrying an immutable release must reproduce the exact archive bytes."""
    module = _load_script_module()
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module-package.yaml").write_text(
        "name: nold-ai/example\nversion: 1.2.3\ncommands: [example]\n",
        encoding="utf-8",
    )
    source_path = module_dir / "example.py"
    source_path.write_text("VALUE = True\n", encoding="utf-8")
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    module._create_tarball(module_dir, first, "nold-ai/example", "1.2.3")
    source_path.chmod(0o600)
    source_path.touch()
    module._create_tarball(module_dir, second, "nold-ai/example", "1.2.3")

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()


def test_tarball_rejects_symlinks_instead_of_silently_omitting_them(tmp_path: Path) -> None:
    """A verified module cannot publish a bundle with missing symlinked files."""
    module = _load_script_module()
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "target.py").write_text("VALUE = True\n", encoding="utf-8")
    (module_dir / "alias.py").symlink_to("target.py")

    with pytest.raises(ValueError, match="symlink"):  # pyright: ignore[reportUnknownMemberType]
        module._create_tarball(module_dir, tmp_path / "module.tar.gz", "nold-ai/example", "1.2.3")
