"""Verify import aliases respect Python lexical scope in core SAST."""

from pathlib import Path

from tests.unit.scripts.test_core_sast_gate import _run_gate, _tracked_source


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
