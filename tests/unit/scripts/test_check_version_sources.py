"""Tests for scripts/check_version_sources.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _copy_version_script(tmp_path: Path) -> Path:
    script_src = Path(__file__).resolve().parents[3] / "scripts" / "check_version_sources.py"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    script = scripts_dir / "check_version_sources.py"
    script.write_text(script_src.read_text(encoding="utf-8"), encoding="utf-8")
    return script


def _write_canonical_version_files(tmp_path: Path, version: str) -> None:
    (tmp_path / "pyproject.toml").write_text(f'version = "{version}"\n', encoding="utf-8")
    (tmp_path / "setup.py").write_text(f'version="{version}"', encoding="utf-8")
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "__init__.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    (tmp_path / "src" / "specfact_cli").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "specfact_cli" / "__init__.py").write_text(
        f'__version__ = "{version}"\n',
        encoding="utf-8",
    )


def _init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True, text=True
    )


def _run_git(tmp_path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)


def _commit_all(tmp_path: Path, message: str) -> None:
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", message)


def _run_version_check(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=script.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_version_sources_passes_on_repo() -> None:
    """Current checkout must keep canonical version files aligned."""
    repo_root = Path(__file__).resolve().parents[3]
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if staged.stdout.strip():
        pytest.skip("Skip when the index has staged changes (local pre-commit uses a clean index).")
    script = repo_root / "scripts" / "check_version_sources.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_detects_mismatch(tmp_path: Path) -> None:
    """Mismatched __version__ in one file must fail the check."""
    script = _copy_version_script(tmp_path)

    (tmp_path / "pyproject.toml").write_text('version = "9.9.9"\n', encoding="utf-8")
    (tmp_path / "setup.py").write_text('version="9.9.9"', encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    (tmp_path / "src" / "specfact_cli").mkdir(parents=True)
    (tmp_path / "src" / "specfact_cli" / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "mismatch" in completed.stderr.lower()


def test_check_version_sources_fails_when_packaged_artifact_changes_without_staged_version_bundle(
    tmp_path: Path,
) -> None:
    """Staged packaged-artifact changes must carry the four version files and CHANGELOG."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/specfact_cli/runtime.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "missing staged version file" in completed.stderr


def test_check_version_sources_ignores_bundled_registry_snapshot_only(tmp_path: Path) -> None:
    """Staged changes under resources/bundled-module-registry/ must not require a version bump."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial.\n", encoding="utf-8")
    reg = tmp_path / "resources" / "bundled-module-registry" / "index.json"
    reg.parent.mkdir(parents=True)
    reg.write_text('{"modules": []}\n', encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    reg.write_text('{"modules": [{"id": "x", "latest_version": "1.0.0"}]}\n', encoding="utf-8")
    subprocess.run(
        ["git", "add", "resources/bundled-module-registry/index.json"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_passes_when_packaged_artifact_changes_with_version_bundle_and_changelog(
    tmp_path: Path,
) -> None:
    """Staged packaged-artifact changes should pass once the package version and changelog are updated together."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path, "initial")

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    _write_canonical_version_files(tmp_path, "1.2.4")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.4] - 2026-04-16\n\n- Runtime update.\n", encoding="utf-8")
    _run_git(tmp_path, "add", ".")

    completed = _run_version_check(script)
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_reuses_branch_release_for_dependency_follow_up(tmp_path: Path) -> None:
    """A follow-up metadata commit may reuse the branch's unreleased version bump."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial.\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path, "initial")
    _run_git(tmp_path, "update-ref", "refs/remotes/origin/dev", "HEAD")

    _write_canonical_version_files(tmp_path, "1.2.4")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.4] - 2026-04-16\n\n- Patch release.\n", encoding="utf-8")
    _commit_all(tmp_path, "release bundle")

    setup_path = tmp_path / "setup.py"
    setup_path.write_text(
        setup_path.read_text(encoding="utf-8") + '\ninstall_requires=["gitpython>=3.1.61"]\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "setup.py"], cwd=tmp_path, check=True, capture_output=True, text=True)

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_rejects_invalid_explicit_base_ref(tmp_path: Path) -> None:
    """An explicit CI comparison ref must fail closed when it cannot be resolved."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    completed = subprocess.run(
        [sys.executable, str(script), "--changed-vs", "refs/remotes/origin/missing"],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "cannot list changed files" in completed.stderr


def test_check_version_sources_rejects_staged_downgrade_after_branch_release(tmp_path: Path) -> None:
    """Branch-level release reuse must not permit a later staged version downgrade."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/dev", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    _write_canonical_version_files(tmp_path, "1.2.5")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.5] - 2026-04-16\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "release bundle"], cwd=tmp_path, check=True, capture_output=True, text=True)

    _write_canonical_version_files(tmp_path, "1.2.4")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.4] - 2026-04-16\n", encoding="utf-8")
    _run_git(tmp_path, "add", ".")

    completed = _run_version_check(script)

    assert completed.returncode == 1
    assert "incrementing the package version" in completed.stderr


def test_check_version_sources_rejects_staged_changelog_deletion_during_follow_up(tmp_path: Path) -> None:
    """A staged changelog deletion must not reuse the committed release entry."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [1.2.3] - 2026-04-16\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path, "initial")
    _run_git(tmp_path, "update-ref", "refs/remotes/origin/dev", "HEAD")

    _write_canonical_version_files(tmp_path, "1.2.4")
    changelog.write_text("## [1.2.4] - 2026-04-16\n", encoding="utf-8")
    _commit_all(tmp_path, "release bundle")

    setup_path = tmp_path / "setup.py"
    setup_path.write_text(setup_path.read_text(encoding="utf-8") + "\n# dependency follow-up\n", encoding="utf-8")
    changelog.unlink()
    _run_git(tmp_path, "add", "setup.py", "CHANGELOG.md")

    completed = _run_version_check(script)

    assert completed.returncode == 1
    assert "must contain a release header" in completed.stderr


def test_check_version_sources_changed_vs_detects_ci_packaged_artifact_change_without_version_bundle(
    tmp_path: Path,
) -> None:
    """CI mode must use changed files vs base ref when the index is empty."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/specfact_cli/runtime.py"], cwd=tmp_path, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "commit", "-m", "runtime only"], cwd=tmp_path, check=True, capture_output=True, text=True)

    completed = subprocess.run(
        [sys.executable, str(script), "--changed-vs", "HEAD~1"],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "missing staged version file" in completed.stderr


def test_check_version_sources_changed_vs_allows_pyproject_tooling_edit_without_release_bundle(
    tmp_path: Path,
) -> None:
    """CI mode must not require a release bundle for pyproject tooling-only edits."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(pyproject.read_text(encoding="utf-8") + 'semgrep-sast = "semgrep scan"\n', encoding="utf-8")
    subprocess.run(["git", "add", "pyproject.toml"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "tooling pyproject edit"], cwd=tmp_path, check=True, capture_output=True, text=True
    )

    completed = subprocess.run(
        [sys.executable, str(script), "--changed-vs", "HEAD~1"],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_compares_version_bump_against_changed_vs_base(
    tmp_path: Path,
) -> None:
    """CI mode must compare the version bump against the supplied base ref, not current HEAD."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path, "initial")

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    _write_canonical_version_files(tmp_path, "1.2.4")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.4] - 2026-04-16\n\n- Runtime update.\n", encoding="utf-8")
    _commit_all(tmp_path, "release bundle")

    completed = _run_version_check(script, "--changed-vs", "HEAD~1")
    assert completed.returncode == 0, completed.stderr
