"""Verify the standalone async scanner on the release source."""

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def test_promoted_async_scanner_reports_only_the_unawaited_coroutine(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        dedent("""\
        async def worker():
            pass

        async def shadowed():
            worker = lambda: None
            worker()

        async def unawaited():
            worker()
        """),
        encoding="utf-8",
    )
    source_root = Path(__file__).resolve().parents[3] / "src"
    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli.analyzers.async_checks", "--root", str(tmp_path), "app.py"],
        cwd=source_root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr
    report = json.loads(result.stdout)
    assert report["targets_scanned"] == 1
    assert [item["line"] for item in report["findings"] if item["rule_id"] == "missing-await-on-coroutine"] == [9]
