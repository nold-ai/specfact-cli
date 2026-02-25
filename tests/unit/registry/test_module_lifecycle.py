from pathlib import Path

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry import module_lifecycle


def test_apply_module_state_update_persists_disabled_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        module_lifecycle,
        "discover_all_package_metadata",
        lambda: [(Path("/tmp/mock-module"), ModulePackageMetadata(name="mock-module", version="0.1.0"))],
    )
    monkeypatch.setattr(
        module_lifecycle,
        "read_modules_state",
        lambda: {"mock-module": {"version": "0.1.0", "enabled": True}},
    )
    monkeypatch.setattr(module_lifecycle, "run_discovery_and_write_cache", lambda _version: None)
    monkeypatch.setattr(module_lifecycle, "get_modules_with_state", list)

    captured: dict[str, list[dict[str, object]]] = {"modules": []}

    def _capture_write(modules: list[dict[str, object]]) -> None:
        captured["modules"] = modules

    monkeypatch.setattr(module_lifecycle, "write_modules_state", _capture_write)

    module_lifecycle.apply_module_state_update(enable_ids=[], disable_ids=["mock-module"], force=False)

    assert captured["modules"] == [{"id": "mock-module", "version": "0.1.0", "enabled": False}]
