"""Check release source artifacts through the actual offline PEP 517 build."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_source_distribution_rebuild_preserves_bundle_mapper(tmp_path: Path) -> None:
    """The sdist can produce a wheel containing the original bundled manifest."""
    uv = shutil.which("uv")
    assert uv is not None
    build = subprocess.run(
        [uv, "build", "--offline", "--no-build-isolation", "--python", sys.executable, "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    wheel = next(tmp_path.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        manifest = archive.read("specfact_cli/modules/bundle-mapper/module-package.yaml")
    assert manifest == (REPO_ROOT / "modules/bundle-mapper/module-package.yaml").read_bytes()
