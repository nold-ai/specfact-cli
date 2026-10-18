from __future__ import annotations

import fnmatch
import hashlib
import os
import shlex
import subprocess
from pathlib import Path
from typing import cast

import yaml


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ".github/workflows/downstream-semgrep.yml"
BOUND_INPUTS = (
    "scripts/downstream_semgrep.py",
    "scripts/verify_downstream_semgrep.py",
    "ci/downstream-semgrep-recipe.json",
    "tools/downstream_semgrep/test_mcp_regressions.py",
    WORKFLOW,
    "uv.lock",
    "tools/semgrep/sast.yml",
    "tools/semgrep/sast-baseline.json",
    "scripts/semgrep_sast_gate.py",
)


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _workflow() -> dict[str, object]:
    path = ROOT / WORKFLOW
    assert path.is_file(), "Downstream candidate workflow is absent"
    return _object(yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader))


def _windows_checkout_command() -> list[str]:
    candidate = _object(_object(_workflow()["jobs"])["candidate"])
    steps = cast(list[dict[str, object]], candidate["steps"])
    checkout = next(
        index for index, step in enumerate(steps) if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    controls = [step for step in steps[:checkout] if "core.autocrlf" in str(step.get("run", ""))]
    assert len(controls) == 1, "Windows Git byte preservation must precede candidate checkout"
    control = controls[0]
    assert control.get("if") in ("runner.os == 'Windows'", "${{ runner.os == 'Windows' }}")
    assert control.get("shell") == "bash"
    argv = shlex.split(str(control["run"]))
    assert argv == ["git", "config", "--global", "core.autocrlf", "false"]
    return argv


def test_windows_checkout_preserves_committed_recipe_bytes(tmp_path: Path) -> None:
    argv = _windows_checkout_command()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_GLOBAL=str(tmp_path / "global.gitconfig"), GIT_CONFIG_NOSYSTEM="1")
    repository = tmp_path / "repository"
    repository.mkdir()

    def git(*arguments: str) -> bytes:
        return subprocess.run(
            ["git", *arguments], cwd=repository, env=environment, check=True, capture_output=True
        ).stdout

    git("init")
    git("config", "--global", "core.autocrlf", "false")
    recipe = repository / "recipe.json"
    recipe.write_bytes(b'{\n  "schema_version": 1,\n  "name": "downstream-recipe"\n}\n')
    git("add", "recipe.json")
    git("-c", "user.name=Checkout Test", "-c", "user.email=checkout@example.invalid", "commit", "-m", "LF recipe")
    committed = git("show", "HEAD:recipe.json")
    git("config", "--global", "core.autocrlf", "true")
    recipe.unlink()
    git("checkout-index", "--force", "--all")
    assert recipe.read_bytes() == committed.replace(b"\n", b"\r\n")
    assert hashlib.sha256(recipe.read_bytes()).digest() != hashlib.sha256(committed).digest()
    assert git("diff", "--exit-code") == b""
    subprocess.run(argv, cwd=repository, env=environment, check=True, capture_output=True)
    recipe.unlink()
    git("checkout-index", "--force", "--all")
    assert recipe.read_bytes() == committed
    assert hashlib.sha256(recipe.read_bytes()).hexdigest() == hashlib.sha256(committed).hexdigest()
    assert git("diff", "--exit-code") == b""


def test_candidate_pr_trigger_covers_bound_inputs_and_regression_tests() -> None:
    trigger = _object(_object(_workflow()["on"])["pull_request"])
    patterns = cast(list[str], trigger["paths"])
    assert all(not pattern.startswith("!") for pattern in patterns)
    tests = [str(path.relative_to(ROOT)) for path in (ROOT / "tests/unit/scripts").glob("test_downstream_semgrep*.py")]
    required = (
        *BOUND_INPUTS,
        *tests,
        "tests/unit/scripts/test_native_report_schema.py",
        "tests/unit/scripts/test_downstream_semgrep_future_regression.py",
    )
    missing = [path for path in required if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)]
    assert not missing, f"Candidate PR trigger omits bound inputs or regression tests: {missing}"
    assert "ci/downstream*" in patterns
    assert "tools/downstream_semgrep/**" in patterns
