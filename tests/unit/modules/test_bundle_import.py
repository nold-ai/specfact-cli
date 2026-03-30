from __future__ import annotations

import sys
from pathlib import Path

from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources


def _make_modules_repo(tmp_path: Path) -> Path:
    modules_repo = tmp_path / "specfact-cli-modules"
    package_src = modules_repo / "packages" / "specfact-codebase" / "src"
    package_src.mkdir(parents=True)
    return modules_repo


def test_bootstrap_local_bundle_sources_honors_specfact_modules_repo_env(monkeypatch: object, tmp_path: Path) -> None:
    modules_repo = _make_modules_repo(tmp_path)
    anchor = tmp_path / "workspace" / "src" / "specfact_cli" / "commands" / "repro.py"
    anchor.parent.mkdir(parents=True)
    anchor.write_text("# anchor\n", encoding="utf-8")

    expected_src = str((modules_repo / "packages" / "specfact-codebase" / "src").resolve())
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(modules_repo))
    monkeypatch.delenv("SPECFACT_CLI_MODULES_REPO", raising=False)
    original_path = sys.path.copy()
    if expected_src in sys.path:
        sys.path.remove(expected_src)

    try:
        bootstrap_local_bundle_sources(str(anchor))
        assert expected_src in sys.path
    finally:
        sys.path[:] = original_path
