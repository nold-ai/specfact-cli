import json
import re
import shutil
import subprocess
import sys
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
sys.path.extend(sys.argv[1:-1])
import git
from git.objects.submodule.base import Submodule
workspace = Path(sys.argv[-1])
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


def _frozen_gitpython_requirement(tmp_path: Path) -> tuple[Path, str]:
    locked = (REPO_ROOT / "requirements/ci/locked.txt").read_text(encoding="utf-8")
    requirements: dict[str, tuple[str, str]] = {}
    for package in ("gitdb", "gitpython", "smmap"):
        declarations = re.findall(rf"(?m)^{package}(?=[\s=<>!~;\[@]|$)", locked)
        assert len(declarations) == 1, f"Expected one {package} delivery requirement"
        entries = re.findall(
            rf"(?m)^{package}==([^\s]+) \\\n((?:[ \t]+--hash=sha256:[0-9a-f]{{64}}(?: \\)?\n)+)", locked
        )
        assert len(entries) == 1, f"Expected one hash-pinned {package} delivery requirement"
        requirements[package] = entries[0]
    requirement = tmp_path / "gitpython.txt"
    requirement.write_text(
        "".join(f"{package}=={version} \\\n{hashes}" for package, (version, hashes) in requirements.items()),
        encoding="utf-8",
    )
    return requirement, requirements["gitpython"][0]


def test_submodule_update_rejects_outside_checkout_before_clone(tmp_path: Path) -> None:
    requirement, version = _frozen_gitpython_requirement(tmp_path)
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
    probe_arguments = [str(target), str(tmp_path)]
    observed = subprocess.run(
        [sys.executable, "-I", "-S", "-c", SUBMODULE_PROBE, *probe_arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert observed.returncode == 0, observed.stderr
    result = json.loads(observed.stdout)
    assert result["version"] == version
    assert result["rejected"] is True
    assert result["clone_calls"] == 0
    assert result["outside_exists"] is False
