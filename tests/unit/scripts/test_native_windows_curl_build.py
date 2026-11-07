from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def builder() -> ModuleType:
    path = ROOT / ".github/actions/setup-frozen-python/windows_curl.py"
    assert path.is_file(), "The private frozen Windows producer must exist"
    spec = importlib.util.spec_from_file_location("_native_windows_curl_build", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("kind", ["missing", "directory", "conflict"])
def test_crt_selection_rejects_unavailable_or_ambiguous_content(builder: ModuleType, tmp_path: Path, kind: str) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    if kind == "directory":
        (cache / "kernel32.lib").mkdir()
    elif kind == "conflict":
        for name, data in [("first", b"one"), ("second", b"two")]:
            parent = cache / name
            parent.mkdir()
            (parent / "kernel32.lib").write_bytes(data)
    with pytest.raises(ValueError, match="link inputs"):
        builder._cache_file(cache, "kernel32.lib")


def test_crt_selection_accepts_identical_compiler_copies(builder: ModuleType, tmp_path: Path) -> None:
    for name in ["first", "second"]:
        parent = tmp_path / name
        parent.mkdir()
        (parent / "kernel32.lib").write_bytes(b"identical input")
    selected = Path(builder._cache_file(tmp_path, "kernel32.lib"))
    assert selected.read_bytes() == b"identical input"


@pytest.mark.parametrize("name", ["relative", "bad;path", "bad\npath"])
def test_invalid_build_paths_fail_before_external_tools(builder: ModuleType, tmp_path: Path, name: str) -> None:
    build = Path(name) if name == "relative" else tmp_path / name
    with pytest.raises(ValueError, match="build path"):
        builder.build_windows_curl(source=tmp_path, zig=tmp_path, cmake=tmp_path, ninja=tmp_path, build=build)
    assert not build.exists()


def test_existing_build_directory_is_not_repaired(builder: ModuleType, tmp_path: Path) -> None:
    sentinel = tmp_path / "existing-input"
    sentinel.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        builder.build_windows_curl(source=tmp_path, zig=tmp_path, cmake=tmp_path, ninja=tmp_path, build=tmp_path)
    assert sentinel.read_bytes() == b"preserve"
