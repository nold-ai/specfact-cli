from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.runtime_discovery_smoke as smoke
from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources


def _make_modules_repo(tmp_path: Path) -> Path:
    modules_repo = tmp_path / "specfact-cli-modules"
    package_src = modules_repo / "packages" / "specfact-codebase" / "src"
    package_src.mkdir(parents=True)
    return modules_repo


def test_bootstrap_local_bundle_sources_honors_specfact_modules_repo_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
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


def test_child_bundle_bootstrap_only_imports_staged_git_bytes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    raw = tmp_path / "unreviewed-checkout"
    staged = tmp_path / "staging"
    for repo, marker in ((raw, "unreviewed"), (staged, "reviewed")):
        source = repo / "packages" / "probe" / "src" / "smoke_source_probe.py"
        source.parent.mkdir(parents=True)
        source.write_text(f"MARKER = {marker!r}\n")
    monkeypatch.setenv("SPECFACT_CLI_MODULES_REPO", str(raw))
    monkeypatch.setenv("SPECFACT_MODULES_ROOTS", str(raw / "packages"))
    env = smoke._build_launcher_env("direct", tmp_path / "home-direct", tmp_path / "index.json", raw)
    probe = (
        "from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources; "
        "bootstrap_local_bundle_sources(__file__); "
        "import smoke_source_probe; print(smoke_source_probe.MARKER)"
    ).replace("__file__", repr(str(smoke.SRC_ROOT / "specfact_cli/commands/repro.py")))
    result = subprocess.run(
        [sys.executable, "-c", probe], env=env, capture_output=True, text=True, check=False, timeout=20
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "reviewed"
    assert "SPECFACT_MODULES_ROOTS" not in env
