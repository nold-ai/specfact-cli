from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "run_changed_lint.py"


def _load_script_module() -> Any:
    spec = importlib.util.spec_from_file_location("run_changed_lint", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_targets_filters_missing_duplicates_and_non_python(tmp_path: Path) -> None:
    module = _load_script_module()
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "docs").mkdir(parents=True)
    py_file = repo_root / "src" / "app.py"
    py_file.write_text("print('ok')\n", encoding="utf-8")
    md_file = repo_root / "docs" / "readme.md"
    md_file.write_text("# doc\n", encoding="utf-8")

    module.REPO_ROOT = repo_root

    targets = module._normalize_targets(["src/app.py", "src/app.py", "docs/readme.md", "missing.py"])

    assert targets == ["src/app.py"]


def test_main_runs_changed_scope_tools_in_expected_order(monkeypatch) -> None:
    module = _load_script_module()
    commands: list[list[str]] = []

    monkeypatch.setattr(
        module, "_normalize_targets", lambda _argv: ["src/app.py", "scripts/helper.py", "tests/test_app.py"]
    )
    monkeypatch.setattr(module, "_run", lambda cmd: commands.append(cmd) or 0)

    exit_code = module.main(["src/app.py", "scripts/helper.py", "tests/test_app.py"])

    assert exit_code == 0
    assert commands == [
        ["ruff", "format", "--check", "src/app.py", "scripts/helper.py", "tests/test_app.py"],
        [
            "basedpyright",
            "--level",
            "error",
            "--pythonpath",
            module.sys.executable,
            "src/app.py",
            "scripts/helper.py",
            "tests/test_app.py",
        ],
        ["ruff", "check", "src/app.py", "scripts/helper.py", "tests/test_app.py"],
        ["pylint", "src/app.py", "tests/test_app.py"],
        ["python", "scripts/verify_safe_project_writes.py"],
    ]
