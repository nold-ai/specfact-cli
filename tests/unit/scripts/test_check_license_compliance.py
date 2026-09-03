"""Unit tests for ``scripts/check_license_compliance.py`` (license gate)."""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _repo_root_for_scripts() -> Path:
    """Resolve specfact-cli root by walking upward (avoids brittle parent-depth indexing)."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        script = candidate / "scripts" / "check_license_compliance.py"
        if script.is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise AssertionError("Could not locate repository root containing scripts/check_license_compliance.py")


def _load_module():
    """Load check_license_compliance.py as a Python module."""
    root = _repo_root_for_scripts()
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

_MIXED_LICENSE_PIP_LICENSES = json.dumps(
    [
        {
            "Name": "docutils",
            "Version": "0.23",
            "License": "BSD License; GNU General Public License (GPL); Public Domain",
        }
    ]
)


class TestCleanEnvironmentPasses:
    """Scenario: Installed environment is GPL-clean — gate passes."""

    def test_scan_installed_env_passes_with_no_gpl(self, mod) -> None:
        """scan_installed_environment returns exit code 0 when no GPL packages found."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_CLEAN_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 0, "Clean env must exit 0"

    def test_scan_installed_env_prints_summary(self, mod, capsys) -> None:
        """Gate prints a summary of packages checked on clean pass."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_CLEAN_PIP_LICENSES,
        ):
            mod.scan_installed_environment(allowlist={})
        captured = capsys.readouterr()
        assert "checked" in captured.out or "scan" in captured.out.lower()

    def test_scan_installed_env_targets_an_additional_python(self, mod, tmp_path: Path) -> None:
        """The root pip-licenses tool can inspect a separately locked tool environment."""
        target_python = tmp_path / "review-tools" / "bin" / "python"
        with patch.object(mod, "_run_pip_licenses", return_value=_CLEAN_PIP_LICENSES) as run_pip_licenses:
            exit_code = mod.scan_installed_environment(allowlist={}, python_executable=target_python)
        assert exit_code == 0
        run_pip_licenses.assert_called_once_with(target_python)


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
        """Gate prints LICENSE VIOLATION including package name and license."""
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            mod.scan_installed_environment(allowlist={})
        captured = capsys.readouterr()
        assert "pylint" in captured.out
        assert "LICENSE VIOLATION" in captured.out
        assert "GPL" in captured.out

    def test_allowlist_wrong_license_does_not_suppress_gpl(self, mod) -> None:
        """Allowlist entry whose license field does not match pip output must not grant an exception."""
        allowlist = {
            "pylint": [{"package": "pylint", "license": "MIT", "scope": "dev-only", "reason": "wrong license row"}]
        }
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 1

    def test_mixed_license_metadata_requires_reviewed_classification(self, mod, capsys) -> None:
        """A GPL token in mixed metadata needs evidence, not a substring verdict."""
        with patch.object(mod, "_run_pip_licenses", return_value=_MIXED_LICENSE_PIP_LICENSES):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 1
        assert "LICENSE CLASSIFICATION REQUIRED" in capsys.readouterr().out

    def test_allowlist_version_mismatch_does_not_suppress_mixed_metadata(self, mod, capsys) -> None:
        """A mixed-license exception is valid only for the reviewed package version."""
        allowlist = {
            "docutils": [
                {
                    "package": "docutils",
                    "version": "0.22",
                    "license": "BSD License; GNU General Public License (GPL); Public Domain",
                    "scope": "dev-only",
                    "reason": "stale review",
                }
            ]
        }
        with patch.object(mod, "_run_pip_licenses", return_value=_MIXED_LICENSE_PIP_LICENSES):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 1
        assert "LICENSE CLASSIFICATION REQUIRED" in capsys.readouterr().out

    def test_empty_allowlist_version_does_not_suppress_mixed_metadata(self, mod, capsys) -> None:
        """Mixed-license exceptions must always identify the reviewed package version."""
        allowlist = {
            "docutils": [
                {
                    "package": "docutils",
                    "version": "",
                    "license": "BSD License; GNU General Public License (GPL); Public Domain",
                    "scope": "dev-only",
                    "reason": "unsafe wildcard",
                }
            ]
        }
        with patch.object(mod, "_run_pip_licenses", return_value=_MIXED_LICENSE_PIP_LICENSES):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 1
        assert "LICENSE CLASSIFICATION REQUIRED" in capsys.readouterr().out

    def test_mixed_metadata_with_lgpl_and_gpl_still_requires_review(self, mod) -> None:
        """An LGPL term cannot mask a separate GPL term in mixed metadata."""
        assert mod._is_mixed_gpl_metadata("LGPL-2.1-only; GPL-2.0-only; BSD License")

    def test_matching_version_allows_reviewed_mixed_metadata(self, mod, capsys) -> None:
        """A reviewed package/version pair is the only mixed-metadata acceptance path."""
        allowlist = {
            "docutils": [
                {
                    "package": "docutils",
                    "version": "0.23",
                    "license": "BSD License; GNU General Public License (GPL); Public Domain",
                    "scope": "dev-only",
                    "reason": "reviewed",
                }
            ]
        }
        with patch.object(mod, "_run_pip_licenses", return_value=_MIXED_LICENSE_PIP_LICENSES):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 0
        assert "EXCEPTION: docutils==0.23" in capsys.readouterr().out


class TestAllowlistAccepted:
    """Scenario: Allowlist entry accepted in both env and manifest scan."""

    def test_repository_allowlist_binds_the_locked_pylint_release(self, mod) -> None:
        """The isolated review tool exception is exact and carries its removal plan."""
        entries = mod._load_allowlist()["pylint"]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["version"] == "4.0.7"
        assert entry["license"] == "GPL-2.0-or-later"
        assert entry["scope"] == "code-review-only"
        assert "Phase 2" in entry["reason"]

    def test_allowlist_entry_suppresses_gpl_failure(self, mod) -> None:
        """GPL package in allowlist must not cause exit 1."""
        allowlist = {
            "pylint": [{"package": "pylint", "license": "GPL-2.0-or-later", "scope": "dev-only", "reason": "dev"}]
        }
        with patch.object(
            mod,
            "_run_pip_licenses",
            return_value=_GPL_PIP_LICENSES,
        ):
            exit_code = mod.scan_installed_environment(allowlist=allowlist)
        assert exit_code == 0, "Allowlisted GPL package must not fail the gate"

    def test_allowlist_entry_prints_exception_note(self, mod, capsys) -> None:
        """Allowlisted entry prints EXCEPTION note."""
        allowlist = {
            "pylint": [{"package": "pylint", "license": "GPL-2.0-or-later", "scope": "dev-only", "reason": "dev"}]
        }
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
            "pylint": [
                {
                    "package": "pylint",
                    "license": "GPL-2.0-or-later",
                    "scope": "dev-only",
                    "reason": "Dev only — GPL",
                }
            ]
        }
        # Provide the static license map so the gate resolves pylint's license offline
        static_license_map = {"pylint": "GPL-2.0-or-later"}
        exit_code = mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist=allowlist,
            static_license_map=static_license_map,
        )
        assert exit_code == 1, "dev-only allowlist must NOT protect GPL in module manifests"


class TestPipLicensesParseFailures:
    """Scenario: pip-licenses output must be valid JSON or the gate fails closed."""

    def test_unparseable_pip_licenses_json_fails(self, mod, capsys) -> None:
        """Invalid JSON from pip-licenses must exit 1, not pass silently."""
        with patch.object(mod, "_run_pip_licenses", return_value="not-json{"):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 1
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "ERROR" in combined
        assert "unparseable" in combined.lower()

    def test_empty_pip_licenses_output_fails(self, mod, capsys) -> None:
        """Empty stdout from pip-licenses must exit 1 (fail closed)."""
        with patch.object(mod, "_run_pip_licenses", return_value="  \n"):
            exit_code = mod.scan_installed_environment(allowlist={})
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "no usable output" in (captured.out + captured.err).lower()


class TestDefaultManifestDiscovery:
    """Scenario: default manifest scan uses modules/ (not packages/)."""

    def test_collect_paths_finds_modules_layout(self, mod, tmp_path: Path) -> None:
        """_collect_module_manifest_paths must find manifests under modules/."""
        (tmp_path / "modules" / "pkg-a").mkdir(parents=True)
        mf = tmp_path / "modules" / "pkg-a" / "module-package.yaml"
        mf.write_text("name: pkg-a\npip_dependencies: []\n", encoding="utf-8")
        found = mod._collect_module_manifest_paths(tmp_path, None)
        assert mf.resolve() in [p.resolve() for p in found]

    def test_scan_with_repo_root_finds_modules_without_packages_dir(
        self, mod, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """scan_module_manifests(None) resolves manifests from modules/ when repo root is patched."""
        (tmp_path / "modules" / "pkg-a").mkdir(parents=True)
        (tmp_path / "modules" / "pkg-a" / "module-package.yaml").write_text(
            "name: pkg-a\npip_dependencies:\n  - rich\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)
        exit_code = mod.scan_module_manifests(
            packages_dir=None,
            allowlist={},
            static_license_map={"rich": "MIT License"},
        )
        assert exit_code == 0

    def test_scan_default_fails_when_no_manifests_anywhere(
        self, mod, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """With no module-package.yaml under default roots, manifest scan must fail closed."""
        monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)
        exit_code = mod.scan_module_manifests(packages_dir=None, allowlist={}, static_license_map={})
        assert exit_code == 1


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


class TestNormalizeDependencyName:
    """Requirement strings must normalize via packaging.Requirement."""

    def test_normalize_extras_and_specifiers(self, mod) -> None:
        assert mod._normalize_dependency_name("Foo[extra]>=1.2") == "foo"
        assert mod._normalize_dependency_name("bar<2") == "bar"

    def test_invalid_requirement_raises(self, mod) -> None:
        with pytest.raises(ValueError, match="Invalid pip dependency"):
            mod._normalize_dependency_name("!!!<<<not-a-name")


class TestIsGplHeuristics:
    """GPL/AGPL detection must not false-positive on LGPL-family strings."""

    def test_lgpl_family_not_flagged_as_gpl(self, mod) -> None:
        assert mod._is_gpl("LGPL-2.1-only") is False
        assert mod._is_gpl("GNU Lesser General Public License v3 (LGPLv3)") is False

    def test_gpl_and_agpl_flagged(self, mod) -> None:
        assert mod._is_gpl("GPL-3.0-only") is True
        assert mod._is_gpl("AGPL-3.0") is True


class TestAllowlistLoader:
    """Allowlist YAML must exist and parse or the loader fails closed."""

    def test_missing_allowlist_raises(self, mod, tmp_path: Path) -> None:
        missing = tmp_path / "no_allowlist_here.yaml"
        with pytest.raises(RuntimeError, match="not found"):
            mod._load_allowlist(missing)

    @pytest.mark.parametrize("invalid_scope", ["[]", "{}"])
    def test_non_string_scope_uses_stable_invalid_scope_error(self, mod, tmp_path: Path, invalid_scope: str) -> None:
        """Malformed YAML shapes must not escape as unhandled set-membership errors."""
        allowlist_path = tmp_path / "license_allowlist.yaml"
        allowlist_path.write_text(
            "exceptions:\n"
            "  - package: pylint\n"
            "    license: GPL-2.0-or-later\n"
            "    reason: reviewed tool only\n"
            f"    scope: {invalid_scope}\n",
            encoding="utf-8",
        )

        with pytest.raises(RuntimeError, match="invalid 'scope' for package 'pylint'"):
            mod._load_allowlist(allowlist_path)


class TestManifestStaticLicenseMap:
    """Manifest deps must resolve to an SPDX string in the static map."""

    def test_pip_dep_missing_from_static_map_is_violation(self, mod, tmp_path: Path, capsys) -> None:
        pkg_dir = tmp_path / "packages" / "demo-mod"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "module-package.yaml").write_text(
            "name: demo-mod\npip_dependencies:\n  - rich\n",
            encoding="utf-8",
        )
        exit_code = mod.scan_module_manifests(
            packages_dir=tmp_path / "packages",
            allowlist={},
            static_license_map={},
        )
        assert exit_code == 1
        out = capsys.readouterr().out
        assert "MODULE MANIFEST VIOLATION" in out
        assert "rich" in out
        assert "module_pip_dependencies_licenses.yaml" in out
