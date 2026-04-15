"""Tests for scripts/check_license_compliance.py (Task 1.6).

All tests here are FAILING until scripts/check_license_compliance.py is created.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module():
    """Load check_license_compliance.py as a Python module."""
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "check_license_compliance.py"
    assert path.exists(), f"scripts/check_license_compliance.py not found at {path}"
    spec = importlib.util.spec_from_file_location("_check_license_compliance", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    """Load the license compliance module."""
    return _load_module()


_CLEAN_PIP_LICENSES = json.dumps(
    [
        {"Name": "requests", "Version": "2.31.0", "License": "Apache Software License"},
        {"Name": "rich", "Version": "13.5.2", "License": "MIT License"},
        {"Name": "typer", "Version": "0.9.0", "License": "MIT License"},
    ]
)

_GPL_PIP_LICENSES = json.dumps(
    [
        {"Name": "pylint", "Version": "3.0.0", "License": "GPL-2.0-or-later"},
        {"Name": "requests", "Version": "2.31.0", "License": "Apache Software License"},
    ]
)


class TestCleanEnvironmentPasses:
    """Scenario: Installed environment is GPL-clean — gate passes."""

    def test_scan_installed_env_passes_with_no_gpl(self, mod, tmp_path: Path) -> None:
        """scan_installed_environment returns exit code 0 when no GPL packages found."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_CLEAN_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 0, "Clean env must exit 0"

    def test_scan_installed_env_prints_summary(self, mod, tmp_path: Path, capsys) -> None:
        """Gate prints a summary of packages checked on clean pass."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_CLEAN_PIP_LICENSES,
        ):
            mod.scan_installed_environment(allowlist={})
        captured = capsys.readouterr()
        assert "checked" in captured.out or "scan" in captured.out.lower()


class TestGplViolationDetected:
    """Scenario: Module manifest pip_dependency is GPL — gate fails."""

    def test_scan_installed_env_fails_on_gpl_package(self, mod) -> None:
        """scan_installed_environment returns exit code 1 when GPL package found."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 1, "GPL violation must exit 1"

    def test_scan_installed_env_prints_violation_message(self, mod, capsys) -> None:
        """Gate prints VIOLATION message including package name and license."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            mod.scan_installed_environment(allowlist={})
        captured = capsys.readouterr()
        assert "pylint" in captured.out
        assert "GPL" in captured.out or "violation" in captured.out.lower()


class TestAllowlistAccepted:
    """Scenario: Allowlist entry accepted in both env and manifest scan."""

    def test_allowlist_entry_suppresses_gpl_failure(self, mod) -> None:
        """GPL package in allowlist must not cause exit 1."""
        allowlist = {"pylint": {"license": "GPL-2.0-or-later", "scope": "dev-only"}}
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 0, "Allowlisted GPL package must not fail the gate"

    def test_allowlist_entry_prints_exception_note(self, mod, capsys) -> None:
        """Allowlisted entry prints EXCEPTION note."""
        allowlist = {"pylint": {"license": "GPL-2.0-or-later", "scope": "dev-only"}}
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            mod.scan_installed_environment(allowlist=allowlist)
        captured = capsys.readouterr()
        assert "EXCEPTION" in captured.out or "exception" in captured.out.lower()

    def test_dev_only_allowlist_rejected_in_manifest_scan(self, mod, tmp_path: Path) -> None:
        """A 'dev-only' allowlist entry must fail when the package appears in a module manifest."""
        # Create a fake module-package.yaml with pylint
        pkg_dir = tmp_path / "packages" / "specfact-code-review"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "module-package.yaml").write_text(
            "name: specfact-code-review\npip_dependencies:\n  - pylint\n",
            encoding="utf-8",
        )
        allowlist = {
            "pylint": {
                "license": "GPL-2.0-or-later",
                "scope": "dev-only",
                "reason": "Dev only — GPL",
            }
        }
        # Provide the static license map so the gate resolves pylint's license offline
        static_license_map = {"pylint": "GPL-2.0-or-later"}
        exit_code = mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist=allowlist,
            static_license_map=static_license_map,
        )
        assert exit_code == 1, "dev-only allowlist must NOT protect GPL in module manifests"


class TestUnknownLicenseWarnsNotFails:
    """Scenario: Unknown license triggers warning not failure."""

    def test_unknown_license_exits_0_with_warning(self, mod, capsys) -> None:
        """Unknown license in installed env must warn but not fail the gate."""
        unknown_pkg = json.dumps([{"Name": "mysterious-pkg", "Version": "1.0.0", "License": "UNKNOWN"}])
        with patch.object(mod, "_run_pip_licenses", return_value=unknown_pkg):
            exit_code = mod.scan_installed_environment(allowlist={})
        captured = capsys.readouterr()
        assert exit_code == 0, "Unknown license must not fail the gate"
        assert "WARNING" in captured.out or "warning" in captured.out.lower()


class TestModuleManifestScan:
    """Scenario: Module manifest pip_dependency validated against license allowlist."""

    def test_clean_manifests_exit_0(self, mod, tmp_path: Path) -> None:
        """Module manifests with no GPL deps must exit 0."""
        pkg_dir = tmp_path / "packages" / "specfact-project"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "module-package.yaml").write_text(
            "name: specfact-project\npip_dependencies:\n  - gitpython\n  - rich\n",
            encoding="utf-8",
        )
        license_map = {"gitpython": "BSD License", "rich": "MIT License"}
        exit_code = mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist={},
            static_license_map=license_map,
        )
        assert exit_code == 0

    def test_gpl_in_manifest_exits_1(self, mod, tmp_path: Path) -> None:
        """Module manifest with GPL dep exits 1 and prints MODULE MANIFEST VIOLATION."""
        pkg_dir = tmp_path / "packages" / "specfact-code-review"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "module-package.yaml").write_text(
            "name: specfact-code-review\npip_dependencies:\n  - pylint\n",
            encoding="utf-8",
        )
        license_map = {"pylint": "GPL-2.0-or-later"}
        exit_code = mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist={},
            static_license_map=license_map,
        )
        assert exit_code == 1

    def test_gpl_in_manifest_prints_module_manifest_violation(self, mod, tmp_path: Path, capsys) -> None:
        """Gate prints MODULE MANIFEST VIOLATION message when GPL dep found in manifest."""
        pkg_dir = tmp_path / "packages" / "specfact-code-review"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "module-package.yaml").write_text(
            "name: specfact-code-review\npip_dependencies:\n  - pylint\n",
            encoding="utf-8",
        )
        license_map = {"pylint": "GPL-2.0-or-later"}
        mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist={},
            static_license_map=license_map,
        )
        captured = capsys.readouterr()
        assert "MODULE MANIFEST VIOLATION" in captured.out
        assert "pylint" in captured.out
