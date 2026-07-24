"""Regression tests for the committed BasedPyright runner path."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_type_runner_uses_its_own_repository_path_not_caller_cwd(tmp_path: Path) -> None:
    """An untrusted current directory cannot shadow the committed Node runner."""
    repository = tmp_path / "repository"
    runner_script = repository / "tools" / "run_basedpyright.sh"
    runner_script.parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "tools" / "run_basedpyright.sh", runner_script)
    trusted_runner = repository / "tools" / "basedpyright" / "node_modules" / "basedpyright" / "index.js"
    trusted_runner.parent.mkdir(parents=True)
    trusted_runner.write_text("trusted", encoding="utf-8")
    untrusted = tmp_path / "untrusted"
    untrusted_runner = untrusted / "tools" / "basedpyright" / "node_modules" / "basedpyright" / "index.js"
    untrusted_runner.parent.mkdir(parents=True)
    untrusted_runner.write_text("untrusted", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_node = fake_bin / "node"
    fake_node.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$1\"\n", encoding="utf-8")
    fake_node.chmod(0o755)

    completed = subprocess.run(
        ["/bin/bash", str(runner_script)],
        cwd=untrusted,
        env={**os.environ, "PATH": f"{fake_bin}:/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(trusted_runner)
