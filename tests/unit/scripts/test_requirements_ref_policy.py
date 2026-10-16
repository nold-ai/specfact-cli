"""Native branch validation agrees with Git without loading candidate dependencies."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "scripts"
REFS = [
    "feature/a+b",
    "feature/a@b",
    "feature/a(b)",
    "feature/a]b",
    "feature/a{b",
    "feature/a$b",
    "feature/é",
    "@",
    "dependency-root",
    "foo/-bar",
    "HEAD",
    "-bad",
    "x/.bar",
    "x.lock/a",
    "x/@{a",
    "a b",
    "a..b",
    "a//b",
    "/bad",
    "bad/",
    "bad.",
    "bad~",
    "bad^",
    "bad:",
    "bad?",
    "bad*",
    "bad[",
    "bad\\",
    "bad\n",
    "bad\x7f",
    "",
]
PROBE = """
import json,sys
sys.path.insert(0,sys.argv[1])
from requirements_stack_context import _ref
try:
    print(json.dumps(_ref(json.loads(sys.stdin.read()))))
except ValueError:
    raise SystemExit(1)
"""


@pytest.mark.parametrize("ref", REFS)
def test_native_ref_validation_matches_literal_git_branch_rules(ref: str) -> None:
    git = subprocess.run(["git", "check-ref-format", "--branch", ref], capture_output=True, check=False)
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", PROBE, str(SCRIPT_DIR)],
        input=json.dumps(ref),
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert (result.returncode == 0) is (git.returncode == 0), ref
    if result.returncode == 0:
        assert json.loads(result.stdout) == ref
