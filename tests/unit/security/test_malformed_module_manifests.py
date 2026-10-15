"""Public fail-closed controls for alternate manifest parsing during project authority admission."""

from pathlib import Path

import pytest
import yaml

from specfact_cli.registry import CommandRegistry, module_packages as packages
from tests.unit.security.test_module_command_squatting import (
    _register_package,
    clean_registry as clean_registry,
)
from tests.unit.security.test_project_bundle_authority import (
    _assert_codebase_authority_available,
    _forged_project_package,
    preserve_fixture_cache_authenticity as preserve_fixture_cache_authenticity,
)


@pytest.mark.parametrize("grouped", [True, False])
def test_malformed_alternate_manifest_is_denied_without_startup_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, grouped: bool
) -> None:
    """Pair genuine project compatibility with public denial instead of an escaping YAML parser failure."""
    _assert_codebase_authority_available(monkeypatch, tmp_path / "authentic")
    package = _forged_project_package(tmp_path / "hostile", "specfact-codebase", "unchanged", monkeypatch)
    (package[0] / "metadata.yaml").write_text("broken: [\n", encoding="utf-8")
    escaped_parser_errors: list[yaml.YAMLError] = []
    try:
        _register_package(monkeypatch, package, grouped)
    except yaml.YAMLError as error:
        escaped_parser_errors.append(error)
    assert not escaped_parser_errors, "Malformed alternate manifest escaped admission and would abort startup"
    assert CommandRegistry.get_module_metadata("code") is None
    assert not packages._ACTIVE_MODULE_SRC_DIRS
