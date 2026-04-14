"""Branch-aware module verify wrapper used by pre-commit (marketplace-06 policy)."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FLAG_SCRIPT = REPO_ROOT / "scripts" / "git-branch-module-signature-flag.sh"
VERIFY_WRAPPER = REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh"

TOKEN_VERIFY_SCRIPT = "verify-modules-signature.py"
TOKEN_REQUIRE_SIGNATURE = "--require-signature"
TOKEN_ENFORCE_VERSION_BUMP = "--enforce-version-bump"
TOKEN_PAYLOAD_FROM_FS = "--payload-from-filesystem"


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


def _repo_with_verify_scripts(
    tmp_path: Path,
    *,
    flag_script_body: str | None = None,
    stage_module_paths: bool = True,
) -> tuple[Path, Path]:
    """Minimal git repo with verify/flag scripts; optionally stage paths under modules/."""
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    (repo / "modules").mkdir()
    (repo / "modules" / "pkg.yaml").write_text("x: 1\n", encoding="utf-8")

    (scripts / "pre-commit-verify-modules.sh").symlink_to(VERIFY_WRAPPER.resolve())
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
        subprocess.run(["git", "add", "modules/pkg.yaml"], cwd=repo, check=True, capture_output=True, text=True)
    else:
        (repo / "README.md").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
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
    assert TOKEN_VERIFY_SCRIPT not in log
    assert log.strip() == "", "fake hatch must not run when module tree paths are not staged"


def test_verify_wrapper_runs_hatch_with_require_on_main(tmp_path: Path) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path)
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
    assert TOKEN_VERIFY_SCRIPT in log
    assert TOKEN_ENFORCE_VERSION_BUMP in log
    assert TOKEN_PAYLOAD_FROM_FS in log
    assert TOKEN_REQUIRE_SIGNATURE in log


def test_verify_wrapper_runs_hatch_checksum_only_off_main(tmp_path: Path) -> None:
    repo, log_path = _repo_with_verify_scripts(tmp_path)
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
    assert TOKEN_VERIFY_SCRIPT in log
    assert TOKEN_ENFORCE_VERSION_BUMP in log
    assert TOKEN_PAYLOAD_FROM_FS in log
    assert TOKEN_REQUIRE_SIGNATURE not in log


def test_verify_wrapper_rejects_invalid_sig_policy(tmp_path: Path) -> None:
    bad_flag = "#!/usr/bin/env bash\nset -euo pipefail\necho bogus\n"
    repo, _log_path = _repo_with_verify_scripts(tmp_path, flag_script_body=bad_flag)
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
