"""Verify the fallback across a process boundary with frozen parent assertions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FALLBACK_PROBE = """
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import scripts.runtime_discovery_smoke as smoke
workspace = Path(sys.argv[2])
def failed_builder(_self, _venv_dir):
    raise subprocess.CalledProcessError(1, "ensurepip")
calls = []
smoke.venv.EnvBuilder.create = failed_builder
smoke.shutil.which = lambda _name: "/controlled/virtualenv"
smoke._run = lambda command, **_kwargs: calls.append(command)
launcher = smoke._create_pip_editable_launcher(workspace)
print(json.dumps({"calls": calls, "launcher": launcher}))
"""


def test_pip_editable_fallback_uses_isolated_seed_cache(tmp_path: Path) -> None:
    """Freeze parent assertions while exercising fallback isolation in a bounded child."""
    observed = subprocess.run(
        [sys.executable, "-P", "-c", FALLBACK_PROBE, str(REPO_ROOT), str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    result = json.loads(observed.stdout)
    assert result["calls"][0] == [
        "/controlled/virtualenv",
        "--app-data",
        str(tmp_path / "virtualenv-app-data"),
        "--no-periodic-update",
        str(tmp_path / "pip-editable-venv"),
    ]
    assert result["calls"][1][1:] == ["-m", "pip", "install", "-e", str(REPO_ROOT)]
    assert result["launcher"] == [
        str(tmp_path / "pip-editable-venv" / ("Scripts/specfact.exe" if os.name == "nt" else "bin/specfact"))
    ]
