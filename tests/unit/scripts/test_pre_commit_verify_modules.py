"""Branch-aware module verify wrapper used by pre-commit (marketplace-06 policy)."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_GIT = shutil.which("git")
FLAG_SCRIPT = REPO_ROOT / "scripts" / "git-branch-module-signature-flag.sh"
VERIFY_WRAPPER = REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh"
LEGACY_VERIFY_WRAPPER = REPO_ROOT / "scripts" / "pre-commit-verify-modules-signature.sh"

# Pre-commit invokes Hatch env scripts (see pyproject.toml) that wrap
# scripts/run_verify_modules_policy.sh → verify-modules-signature.py with policy arrays.
TOKEN_HATCH_LINE_STRICT = "run verify-modules-signature"
TOKEN_HATCH_LINE_PR = "run verify-modules-signature-pr"
TOKEN_SIGN_MODULES = "sign-modules.py"


def _hatch_log_lines(log: str) -> list[str]:
    return [ln.strip() for ln in log.strip().splitlines() if ln.strip()]


def _run_flag(*, cwd: Path) -> str:
    result = subprocess.run(
        ["bash", str(FLAG_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=8,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _git_init_with_commit(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)


def _write_fake_hatch(bin_dir: Path, log_path: Path) -> Path:
    hatch = bin_dir / "hatch"
    hatch.write_text(
        f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "{log_path}"\nexit 0\n',
        encoding="utf-8",
    )
    hatch.chmod(hatch.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hatch


def _write_fake_git_fail_diff_cached(bin_dir: Path, real_git: str) -> Path:
    git_bin = bin_dir / "git"
    git_bin.write_text(
        f"""#!/bin/sh
if [ "$1" = "diff" ] && [ "$2" = "--cached" ]; then
  exit 2
fi
exec "{real_git}" "$@"
""",
        encoding="utf-8",
    )
    git_bin.chmod(git_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return git_bin


def _repo_with_verify_scripts(
    tmp_path: Path,
    *,
    flag_script_body: str | None = None,
    stage_module_paths: bool = True,
    module_tree: str = "top",
) -> tuple[Path, Path]:
    """Minimal git repo with verify/flag scripts; optionally stage under modules/ or bundled tree."""
    assert module_tree in {"top", "bundled"}
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)

    (scripts / "pre-commit-verify-modules.sh").symlink_to(VERIFY_WRAPPER.resolve())
    (scripts / "pre-commit-verify-modules-signature.sh").symlink_to(LEGACY_VERIFY_WRAPPER.resolve())
    (scripts / "module-verify-policy.sh").symlink_to((REPO_ROOT / "scripts" / "module-verify-policy.sh").resolve())
    flag_target = scripts / "git-branch-module-signature-flag.sh"
    if flag_script_body is None:
        flag_target.symlink_to(FLAG_SCRIPT.resolve())
    else:
        flag_target.write_text(flag_script_body, encoding="utf-8")
        flag_target.chmod(flag_target.stat().st_mode | stat.S_IXUSR)

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    if stage_module_paths:
        if module_tree == "top":
            mod_dir = repo / "modules" / "testmod"
            mod_dir.mkdir(parents=True)
            stage_path = "modules/testmod/module-package.yaml"
        else:
            mod_dir = repo / "src" / "specfact_cli" / "modules" / "testmod"
            mod_dir.mkdir(parents=True)
            stage_path = "src/specfact_cli/modules/testmod/module-package.yaml"
        (mod_dir / "module-package.yaml").write_text("id: testmod\nversion: 0.0.1\n", encoding="utf-8")
        subprocess.run(["git", "add", stage_path], cwd=repo, check=True, capture_output=True, text=True)
    else:
        docs = repo / "docs"
        docs.mkdir(parents=True)
        (docs / "notes.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "docs/notes.txt"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    log_path = tmp_path / "hatch_invocations.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_hatch(bin_dir, log_path)
    log_path.touch()
    return repo, log_path


def test_verify_wrapper_skips_when_no_module_paths_staged(tmp_path: Path) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path, stage_module_paths=False)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True, text=True)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    log = log_path.read_text(encoding="utf-8")
    assert TOKEN_HATCH_LINE_STRICT not in log
    assert TOKEN_HATCH_LINE_PR not in log
    assert log.strip() == "", "fake hatch must not run when module tree paths are not staged"


def test_pre_commit_verify_modules_legacy_entrypoint(tmp_path: Path) -> None:
    """Legacy shim must exec the canonical ``pre-commit-verify-modules.sh`` beside it."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    log_path = tmp_path / "canon_invoked.txt"
    canon = scripts_dir / "pre-commit-verify-modules.sh"
    canon.write_text(
        f'#!/usr/bin/env bash\necho invoked > "{log_path}"\nexit 0\n',
        encoding="utf-8",
    )
    canon.chmod(canon.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    legacy = scripts_dir / "pre-commit-verify-modules-signature.sh"
    legacy.write_text(LEGACY_VERIFY_WRAPPER.read_text(encoding="utf-8"), encoding="utf-8")
    legacy.chmod(legacy.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    result = subprocess.run(
        ["bash", str(legacy)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert log_path.is_file()
    assert log_path.read_text(encoding="utf-8").strip() == "invoked"


@pytest.mark.parametrize("module_tree", ("top", "bundled"))
def test_legacy_verify_script_matches_canonical_invocation(tmp_path: Path, module_tree: str) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path, module_tree=module_tree)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True, text=True)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}"}
    canon = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    log_canon = log_path.read_text(encoding="utf-8")
    log_path.write_text("", encoding="utf-8")
    legacy = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules-signature.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    log_legacy = log_path.read_text(encoding="utf-8")
    assert canon.returncode == legacy.returncode == 0, (canon.stderr, legacy.stderr)
    assert log_canon == log_legacy
    assert TOKEN_HATCH_LINE_STRICT in _hatch_log_lines(log_legacy)


@pytest.mark.parametrize("module_tree", ("top", "bundled"))
def test_verify_wrapper_propagates_git_diff_cached_failure(tmp_path: Path, module_tree: str) -> None:
    assert REAL_GIT is not None
    repo, log_path = _repo_with_verify_scripts(tmp_path, stage_module_paths=True, module_tree=module_tree)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True, text=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_hatch(bin_dir, log_path)
    _write_fake_git_fail_diff_cached(bin_dir, REAL_GIT)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0, (result.stdout, result.stderr)
    log = log_path.read_text(encoding="utf-8")
    assert TOKEN_HATCH_LINE_STRICT not in log
    assert TOKEN_HATCH_LINE_PR not in log
    assert "git diff --cached failed" in result.stderr


@pytest.mark.parametrize("module_tree", ("top", "bundled"))
def test_verify_wrapper_runs_hatch_with_require_on_main(tmp_path: Path, module_tree: str) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path, module_tree=module_tree)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True, text=True)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    log = log_path.read_text(encoding="utf-8")
    lines = _hatch_log_lines(log)
    assert TOKEN_HATCH_LINE_STRICT in lines
    assert TOKEN_HATCH_LINE_PR not in lines


@pytest.mark.parametrize("module_tree", ("top", "bundled"))
def test_verify_wrapper_runs_hatch_checksum_only_off_main(tmp_path: Path, module_tree: str) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path, module_tree=module_tree)
    subprocess.run(["git", "branch", "-M", "feature/x"], cwd=repo, check=True, capture_output=True, text=True)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    log = log_path.read_text(encoding="utf-8")
    lines = _hatch_log_lines(log)
    assert TOKEN_HATCH_LINE_PR in lines
    assert TOKEN_HATCH_LINE_STRICT not in lines
    assert TOKEN_SIGN_MODULES in log


@pytest.mark.parametrize("module_tree", ("top", "bundled"))
def test_verify_wrapper_rejects_invalid_sig_policy(tmp_path: Path, module_tree: str) -> None:
    bad_flag = "#!/usr/bin/env bash\nset -euo pipefail\necho bogus\n"
    repo, _log_path = _repo_with_verify_scripts(tmp_path, flag_script_body=bad_flag, module_tree=module_tree)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True, capture_output=True, text=True)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "pre-commit-verify-modules.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Invalid module signature policy" in result.stderr
    assert "bogus" in result.stderr
    assert "expected require or omit" in result.stderr


@pytest.mark.parametrize(
    ("branch", "expected"),
    (
        ("feature/foo", "omit"),
        ("dev", "omit"),
        ("main", "require"),
    ),
)
def test_git_branch_signature_flag(tmp_path: Path, branch: str, expected: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init_with_commit(repo)
    subprocess.run(["git", "branch", "-M", branch], cwd=repo, check=True, capture_output=True, text=True)
    assert _run_flag(cwd=repo) == expected


def test_pre_commit_verify_modules_staged_query_includes_deletions() -> None:
    """Deleted module paths must appear in staged listing so the hook does not skip."""
    body = VERIFY_WRAPPER.read_text(encoding="utf-8")
    assert "--diff-filter=ACMRD" in body


def test_pre_commit_verify_modules_uses_macos_default_bash_compatible_read_loop() -> None:
    """macOS ships Bash 3.2, so the hook must avoid Bash 4-only ``mapfile``."""
    body = VERIFY_WRAPPER.read_text(encoding="utf-8")
    assert "mapfile" not in body
    assert "while IFS= read -r staged_manifest" in body


def test_git_branch_signature_flag_detached_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init_with_commit(repo)
    subprocess.run(
        ["git", "checkout", "--detach", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert _run_flag(cwd=repo) == "omit"
