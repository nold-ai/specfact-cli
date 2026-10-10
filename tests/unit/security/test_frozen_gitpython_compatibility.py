"""Submodule containment exercised through the hash-pinned delivery wheel."""

import json
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_WHEEL_INSTALL_FLAGS = (
    "--no-config",
    "pip",
    "install",
    "--only-binary=:all:",
    "--no-deps",
    "--require-hashes",
    "--index-url",
    "https://pypi.org/simple",
)
SUBMODULE_PROBE = """
import json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.extend(sys.argv[1:3])
import git
from git.objects.submodule.base import Submodule
workspace = Path(sys.argv[3])
parent = git.Repo.init(workspace / "parent")
submodule = Submodule(parent, Submodule.NULL_BIN_SHA, name="module",
                      path="../outside", url="unused")
rejected = False
with patch.object(Submodule, "_clone_repo", side_effect=AssertionError("clone boundary reached")) as clone:
    try:
        submodule.update(init=True)
    except ValueError:
        rejected = True
    clone_calls = clone.call_count
print(json.dumps({"version": git.__version__, "rejected": rejected,
                  "clone_calls": clone_calls, "outside_exists": (workspace / "outside").exists()}))
"""


def test_submodule_update_rejects_outside_checkout_before_clone(tmp_path: Path) -> None:
    """An outside checkout never reaches cloning or creates an outside directory."""
    locked = (REPO_ROOT / "requirements/ci/locked.txt").read_text(encoding="utf-8")
    entries = re.findall(r"(?m)^gitpython==([^\s]+) \\\n((?:[ \t]+--hash=sha256:[0-9a-f]{64}(?: \\)?\n)+)", locked)
    assert len(entries) == 1, "Expected one hash-pinned GitPython delivery requirement"
    version, hashes = entries[0]
    requirement = tmp_path / "gitpython.txt"
    requirement.write_text(f"gitpython=={version} \\\n{hashes}", encoding="utf-8")
    uv = shutil.which("uv")
    assert uv is not None, "The frozen delivery probe requires uv"
    target = tmp_path / "delivery-package"
    install_command = [uv, *FROZEN_WHEEL_INSTALL_FLAGS, "--target", str(target), "-r", str(requirement)]
    subprocess.run(
        install_command,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    probe_arguments = [str(target), sysconfig.get_paths()["purelib"], str(tmp_path)]
    observed = subprocess.run(
        [sys.executable, "-I", "-S", "-c", SUBMODULE_PROBE, *probe_arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    result = json.loads(observed.stdout)
    assert result["version"] == version
    assert result["rejected"] is True
    assert result["clone_calls"] == 0
    assert result["outside_exists"] is False
