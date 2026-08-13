"""Integration: the proof-input set the provenance gate resolves for this repository.

Every other test in the provenance suite states what the gate must bind. These state what it
must not, which is the axis those cannot cover: a rule that binds too much satisfies every
positive expectation while rejecting valid proofs, and it only shows up against a real tree
with real conftest chains, plugins, and path literals. That measurement used to be run by
hand before each change to the gate; running it here removes the manual step.

Failures name the offending paths, because the fix is always to narrow the rule that bound
them, not to widen the expectation.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple, Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"

# The product source a red-to-green change edits by definition. Binding any of it would reject
# the proof for the very fix it is meant to prove, so this is stated separately from the
# exception list below and must never gain an entry.
PRODUCT_SOURCE_PREFIX = "src/specfact_cli/"

# Files outside the test tree that the gate binds for a stated reason. Each is something pytest
# genuinely loads for the selected tests, so a change to it can change their outcome.
EXPECTED_OUTSIDE_TEST_TREE = {
    # Early-loaded on every proof run through the executor's -p option.
    "scripts/requirements_proof_pytest_plugin.py",
    # Imported directly by the tests that exercise them.
    "scripts/runtime_discovery_smoke.py",
    "tools/smart_test_coverage.py",
    "tools/validate_prompts.py",
}

# The resolved set grows with the test suite, so it is bounded per selector rather than
# absolutely. The ceiling is generous against the measured ratio; it catches a rule that starts
# pulling in whole directories, not ordinary growth.
MAX_INPUTS_PER_SELECTOR = 15


class ProvenanceModule(Protocol):
    """The internals this measurement drives directly."""

    def _proof_inputs(self, repo_root: Path, source_ref: str, selector_paths: tuple[str, ...]) -> set[str]: ...

    def _configuration_candidate_paths(self, directories: tuple[str, ...]) -> set[str]: ...

    def _configuration_directories(self, selector_paths: tuple[str, ...]) -> tuple[str, ...]: ...


class Measurement(NamedTuple):
    """The resolved proof inputs for every selectable test committed at HEAD."""

    selectors: tuple[str, ...]
    inputs: frozenset[str]
    committed: frozenset[str]
    configuration_candidates: frozenset[str]

    @property
    def existing_inputs(self) -> frozenset[str]:
        """Return only inputs that exist, since absent candidates bind no content."""
        return self.inputs & self.committed


def _load_provenance_module() -> ProvenanceModule:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance", PROVENANCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements proof provenance validator must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(ProvenanceModule, module)


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=str(REPO_ROOT), check=False, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout


@pytest.fixture(scope="module")
def measurement() -> Measurement:
    """Resolve the proof inputs once for every test in this file."""
    module = cast(Any, _load_provenance_module())
    source_ref = _git("rev-parse", "HEAD").strip()
    committed = frozenset(_git("ls-files").split())
    selectors = tuple(
        sorted(
            path
            for path in committed
            if path.startswith("tests/") and path.endswith(".py") and Path(path).name.startswith("test_")
        )
    )
    assert selectors, "the repository must contain selectable tests for this measurement to mean anything"
    directories = module._configuration_directories(selectors)
    return Measurement(
        selectors=selectors,
        inputs=frozenset(module._proof_inputs(REPO_ROOT, source_ref, selectors)),
        committed=committed,
        configuration_candidates=frozenset(module._configuration_candidate_paths(directories)),
    )


@pytest.mark.integration
@pytest.mark.slow
def test_no_product_source_file_is_a_proof_input(measurement: Measurement) -> None:
    """A change to product source is the fix, so binding it would reject every proof of one."""
    bound_product_source = sorted(path for path in measurement.inputs if path.startswith(PRODUCT_SOURCE_PREFIX))

    assert not bound_product_source, (
        f"the gate binds product source, so a red-to-green change would invalidate its own proof: "
        f"{bound_product_source}"
    )


@pytest.mark.integration
@pytest.mark.slow
def test_every_bound_file_outside_the_test_tree_is_a_recorded_exception(measurement: Measurement) -> None:
    """Anything the harness does not own is something a change may edit, so binding it is a defect."""
    escapes = sorted(
        path
        for path in measurement.existing_inputs
        if not path.startswith("tests/")
        and path not in measurement.configuration_candidates
        and path not in EXPECTED_OUTSIDE_TEST_TREE
    )

    assert not escapes, (
        f"the gate binds files outside the test tree with no recorded reason, which will reject valid "
        f"proofs whenever they change: {escapes}"
    )


@pytest.mark.integration
@pytest.mark.slow
def test_the_bound_set_stays_proportional_to_the_selectors(measurement: Measurement) -> None:
    """A rule that pulls in whole directories stays inside the test tree and escapes the check above."""
    inputs_per_selector = len(measurement.inputs) / len(measurement.selectors)

    assert inputs_per_selector <= MAX_INPUTS_PER_SELECTOR, (
        f"{len(measurement.inputs)} inputs for {len(measurement.selectors)} selectors "
        f"({inputs_per_selector:.1f} each) exceeds the ceiling of {MAX_INPUTS_PER_SELECTOR}"
    )


@pytest.mark.integration
@pytest.mark.slow
def test_the_selected_tests_themselves_are_bound(measurement: Measurement) -> None:
    """The measurement is only evidence of restraint while it still resolves what it must bind."""
    unbound_selectors = sorted(set(measurement.selectors) - measurement.inputs)

    assert not unbound_selectors, f"selected tests missing from their own proof inputs: {unbound_selectors[:5]}"
