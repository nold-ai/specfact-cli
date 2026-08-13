"""Integration: the provenance gate's resolved inputs, checked against what pytest really loads.

Every rule in the gate is a hand-derived model of pytest's behaviour — which files it reads to
decide collection, which directories it puts on ``sys.path``, which modules a declaration pulls
in. A model has no error bar. Each divergence found so far was found by a reviewer reading the
rule, which makes review the only oracle, and review does not run on every change.

These tests supply the missing oracle. For a set of repository layouts, pytest is run for real
and every repository-local file it imports *or reads* is recorded; the gate must bind all of
them. A rule that stops matching how pytest actually resolves something fails here rather than
surviving until someone reads it.

Reads are observed as well as imports because the two exercise different rule families. An
import is visible in ``sys.modules``; a fixture reading ``tests/data/case.json`` is not, and the
path-resolution rules — join notations, ``__file__``-relative bases, links — live entirely in
that second family. Observing only imports would leave them checked by review alone, which is
the condition this file exists to end.

The direction is deliberate: this asserts the gate binds at least what pytest touched. It is a
guard against binding too little. The companion measurement in
``test_requirements_proof_provenance_repository.py`` guards the other direction.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"
OBSERVER_DIRECTORY = Path(__file__).resolve().parent
SELECTED_TEST = "tests/test_proof.py"
SELECTOR = f"{SELECTED_TEST}::test_selected"


class Layout(NamedTuple):
    """One repository shape, described by the files it contains and any links it needs."""

    name: str
    files: dict[str, str]
    links: dict[str, str] = {}


class Observation(NamedTuple):
    """What one real pytest run touched inside the observed repository."""

    imported: frozenset[str]
    read: frozenset[str]

    @property
    def touched(self) -> frozenset[str]:
        """Return every repository file the run depended on, however it reached it."""
        return self.imported | self.read


# Each layout puts the helper somewhere pytest can reach and the gate must therefore resolve.
# They differ in the mechanism, not in the outcome: `tests/helper.py` is loaded in every one.
LAYOUTS = [
    Layout(
        "bare import through the prepended test directory",
        {
            "tests/conftest.py": "import helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "package-qualified import from a package test directory",
        {
            "tests/__init__.py": "",
            "tests/conftest.py": "import tests.helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "conftest chain from the repository root",
        {
            "conftest.py": "import support\n",
            "support.py": "VALUE = False\n",
            "tests/conftest.py": "import helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "declared plugin importing its own helper",
        {
            "conftest.py": 'pytest_plugins = ["tests.localplugin"]\n',
            "tests/__init__.py": "",
            "tests/localplugin.py": "from tests import helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "plugin reached through a configured pythonpath root",
        {
            "pyproject.toml": '[tool.pytest.ini_options]\npythonpath = ["extra"]\n',
            "conftest.py": 'pytest_plugins = ["rooted"]\n',
            "extra/rooted.py": "import rooted_helper\n",
            "extra/rooted_helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "import inside a fixture body",
        {
            "tests/conftest.py": "import pytest\n\n\n@pytest.fixture\ndef support():\n    import helper\n\n    return helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    Layout(
        "package initializer importing at load time",
        {
            "tests/__init__.py": "from tests import helper\n",
            "tests/helper.py": "VALUE = False\n",
        },
    ),
    # From here the run reads data rather than importing it. None of these appear in
    # ``sys.modules``, so they exercise the path-resolution rules and nothing else does.
    Layout(
        "data read through a repository-relative literal",
        {
            "tests/conftest.py": 'from pathlib import Path\n\nCASE = Path("tests/data/case.json").read_text()\n',
            "tests/data/case.json": '{"expected": false}\n',
        },
    ),
    Layout(
        "data read relative to the reading module",
        {
            "tests/conftest.py": (
                'from pathlib import Path\n\nCASE = (Path(__file__).parent / "data" / "case.json").read_text()\n'
            ),
            "tests/data/case.json": '{"expected": false}\n',
        },
    ),
    Layout(
        "data read through a functional join",
        {
            "tests/conftest.py": (
                "import os\n\nwith open(os.path.join(os.path.dirname(__file__), "
                '"data", "case.json")) as handle:\n    CASE = handle.read()\n'
            ),
            "tests/data/case.json": '{"expected": false}\n',
        },
    ),
    Layout(
        "data read inside a fixture body",
        {
            "tests/conftest.py": (
                "from pathlib import Path\n\nimport pytest\n\n\n@pytest.fixture\ndef case():\n"
                '    return (Path(__file__).parent / "data" / "case.json").read_text()\n'
            ),
            "tests/data/case.json": '{"expected": false}\n',
            "tests/test_proof.py": "def test_selected(case) -> None:\n    assert False\n",
        },
    ),
    Layout(
        "data read through a linked file",
        {
            "tests/conftest.py": 'from pathlib import Path\n\nCASE = Path("tests/data/case.json").read_text()\n',
            "tests/data/real.json": '{"expected": false}\n',
        },
        {"tests/data/case.json": "real.json"},
    ),
    Layout(
        "data read through a linked directory",
        {
            "tests/conftest.py": 'from pathlib import Path\n\nCASE = Path("tests/linked/case.json").read_text()\n',
            "tests/real_data/case.json": '{"expected": false}\n',
        },
        {"tests/linked": "real_data"},
    ),
]


def _load_provenance_module() -> Any:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance", PROVENANCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements proof provenance validator must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=str(repository), check=False, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout


def _build_repository(repository: Path, layout: Layout) -> str:
    """Write a layout, add the selected failing test, and commit the result."""
    for relative, content in layout.files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for relative, target in layout.links.items():
        link = repository / relative
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
    selected = repository / SELECTED_TEST
    if SELECTED_TEST not in layout.files:
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_text("def test_selected() -> None:\n    assert False\n", encoding="utf-8")
    _git(repository, "init")
    _git(repository, "config", "user.email", "requirements@example.test")
    _git(repository, "config", "user.name", "Requirements proof")
    _git(repository, "add", ".")
    _git(repository, "commit", "--no-gpg-sign", "-m", "test: layout under observation")
    return _git(repository, "rev-parse", "HEAD").strip()


def _observed_repository_files(repository: Path, observation_path: Path) -> Observation:
    """Run pytest for real and return the repository-local files it imported and read."""
    environment = {
        **os.environ,
        "PYTHONPATH": str(OBSERVER_DIRECTORY),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "OBSERVE_ROOT": str(repository),
        "OBSERVE_OUT": str(observation_path),
        "PYTEST_ADDOPTS": "",
    }
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "observer_plugin", "-p", "no:cacheprovider", "-q", "--", SELECTOR],
        cwd=str(repository),
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
        env=environment,
    )
    if not observation_path.exists():
        raise AssertionError(f"pytest did not reach session finish:\n{result.stdout}\n{result.stderr}")
    recorded = cast(dict[str, list[str]], json.loads(observation_path.read_text(encoding="utf-8")))
    observation = Observation(frozenset(recorded["imported"]), frozenset(recorded["read"]))
    # The run must have collected the selected test, or it observed nothing meaningful.
    assert SELECTED_TEST in observation.imported, (
        f"pytest did not import the selected test:\n{result.stdout}\n{result.stderr}"
    )
    return observation


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda layout: layout.name)
def test_the_gate_binds_every_file_pytest_actually_used(tmp_path: Path, layout: Layout) -> None:
    """Whatever pytest loaded or read decided the outcome, so a proof that omits it is not bound."""
    module = _load_provenance_module()
    repository = tmp_path / "repository"
    repository.mkdir()
    source_ref = _build_repository(repository, layout)

    observed = _observed_repository_files(repository, tmp_path / "observed.json")
    bound = module._proof_inputs(
        repository, source_ref, (SELECTED_TEST,), {SELECTED_TEST: frozenset({"test_selected"})}
    )

    unbound = sorted(observed.touched - bound)
    assert not unbound, (
        f"pytest used these files while the gate bound none of them, so a change to any of "
        f"them after the red source would not invalidate the proof: {unbound}"
    )
