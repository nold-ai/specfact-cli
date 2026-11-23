"""Verify import aliases respect Python lexical scope in core SAST."""

import subprocess
import sys
from pathlib import Path

from tests.unit.scripts.test_core_sast_gate import SCRIPT, SOURCE_PATH, _run_gate, _tracked_source


def test_import_aliases_follow_lexical_scope(tmp_path: Path) -> None:
    _tracked_source(
        tmp_path,
        "import random as helper\n"
        "def unrelated(data):\n"
        "    import hashlib as helper\n"
        "    return helper.md5(data)\n"
        "class Sampler:\n"
        "    import hashlib as helper\n"
        "    digest = helper.md5(b'fixture')\n"
        "    def sample(self, value=helper.md5(b'default')):\n"
        "        return helper.random()\n"
        "def draw():\n"
        "    return helper.random()\n",
    )
    result, report = _run_gate(tmp_path)

    assert result.returncode == 1, result.stderr
    assert [(row["rule_id"], row["line"]) for row in report["new_findings"]] == [
        ("insecure-random", 9),
        ("insecure-random", 11),
        ("weak-cryptographic-hash", 4),
        ("weak-cryptographic-hash", 7),
        ("weak-cryptographic-hash", 8),
    ]


def test_text_codec_failure_retains_incomplete_report(tmp_path: Path) -> None:
    _tracked_source(tmp_path, "# coding: base64_codec\nvalue = 1\n")
    result, report = _run_gate(tmp_path)

    assert result.returncode == 2, result.stderr
    assert report["status"] == "incomplete"
    assert report["eligible_paths"] == [SOURCE_PATH]
    assert report["scanned_paths"] == []
    assert report["diagnostics"] == [{"path": SOURCE_PATH, "message": "invalid Python"}]


def test_standalone_scan_uses_default_output_path(tmp_path: Path) -> None:
    _tracked_source(tmp_path, "value = 1\n")
    baseline = tmp_path / "baseline.json"
    baseline.write_text('{"version": 1, "accepted_findings": []}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", ".", "--baseline", str(baseline)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "python-sast.json").is_file()


def test_global_import_without_flow_resolution_reports_incomplete(tmp_path: Path) -> None:
    _tracked_source(
        tmp_path,
        "class Setup:\n    global uniform\n    from random import random as uniform\nsample = uniform()\n",
    )
    result, report = _run_gate(tmp_path)

    assert result.returncode == 2, result.stderr
    assert report["status"] == "incomplete"
    assert report["diagnostics"] == [{"path": SOURCE_PATH, "message": "global import alias requires flow analysis"}]
