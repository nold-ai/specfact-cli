"""Compatibility coverage for the canonical-selector pytest plugin."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_selector_plugin_uses_only_public_pytest_report_contract() -> None:
    source = (REPO_ROOT / "scripts/requirements_proof_pytest_plugin.py").read_text(encoding="utf-8")

    assert "from _pytest" not in source
    assert 'record_property("specfact.selector", request.node.nodeid)' in source
    assert 'record_property("specfact.runner", "pytest")' in source
    assert 'record_property("specfact.python", platform.python_version())' in source
    assert 'record_property("specfact.pytest", pytest.__version__)' in source
