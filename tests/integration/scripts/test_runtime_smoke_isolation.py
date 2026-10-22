"""Smoke launchers must not install into the running test interpreter."""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHILD_PROBE = """
import json, pathlib, subprocess, sys
sys.path.append(sys.argv[1])
sys.path.insert(0, sys.argv[2])
from scripts.runtime_discovery_smoke import _launcher_command
workspace = pathlib.Path(sys.argv[3])
command = _launcher_command("direct", workspace)
result = subprocess.run([command[0], "-c", "import sys; print(sys.prefix)"], capture_output=True, text=True, check=True)
print(json.dumps({"prefix": result.stdout.strip(), "command": command}))
"""


def test_direct_smoke_uses_workspace_owned_interpreter(tmp_path: Path) -> None:
    """Check the real prefix without ever modifying a shared interpreter."""
    runtime_site = str(importlib.metadata.distribution("beartype").locate_file(""))
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", CHILD_PROBE, runtime_site, str(REPO_ROOT), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    prefix = Path(observed["prefix"]).resolve()
    assert prefix.is_relative_to(tmp_path.resolve())
    assert prefix != Path(sys.prefix).resolve()
    assert observed["command"][1:] == ["-m", "specfact_cli.cli"]
