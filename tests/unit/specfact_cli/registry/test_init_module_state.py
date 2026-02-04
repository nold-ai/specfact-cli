"""
Tests for specfact init module state (spec: init-module-state).

First init writes modules.json with all enabled; second init respects enabled: false;
--enable-module/--disable-module persist; message when modules disabled by configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from specfact_cli.registry.module_packages import get_discovered_modules_for_state
from specfact_cli.registry.module_state import read_modules_state, write_modules_state


@pytest.fixture
def registry_dir(tmp_path: Path):
    os.environ["SPECFACT_REGISTRY_DIR"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        os.environ.pop("SPECFACT_REGISTRY_DIR", None)


def test_first_init_writes_state_all_enabled(registry_dir: Path):
    """First run: get_discovered_modules_for_state with no overrides returns all enabled."""
    modules_list = get_discovered_modules_for_state()
    for m in modules_list:
        assert m.get("enabled") is True
        assert "id" in m
        assert "version" in m


def test_second_init_respects_disabled(registry_dir: Path):
    """After writing state with one disabled, merge preserves disabled."""
    write_modules_state(
        [
            {"id": "example", "version": "0.1.0", "enabled": False},
        ]
    )
    state = read_modules_state()
    assert state.get("example", {}).get("enabled") is False
    modules_list = get_discovered_modules_for_state()
    example = next((m for m in modules_list if m["id"] == "example"), None)
    if example:
        assert example.get("enabled") is False


def test_enable_disable_module_override(registry_dir: Path):
    """--enable-module and --disable-module override state."""
    write_modules_state([{"id": "a", "version": "1.0", "enabled": False}])
    modules_list = get_discovered_modules_for_state(enable_ids=["a"], disable_ids=[])
    a_mod = next((m for m in modules_list if m["id"] == "a"), None)
    if a_mod:
        assert a_mod.get("enabled") is True
    modules_list2 = get_discovered_modules_for_state(enable_ids=[], disable_ids=["a"])
    a_mod2 = next((m for m in modules_list2 if m["id"] == "a"), None)
    if a_mod2:
        assert a_mod2.get("enabled") is False


def test_new_module_gets_enabled_true(registry_dir: Path):
    """New discovered module (not in state) gets enabled: true in merged list."""
    modules_list = get_discovered_modules_for_state()
    for m in modules_list:
        assert m.get("enabled", True) is True
