"""Prevent the isolated Code Review environment from restoring vulnerable pylint."""

import hashlib
from pathlib import Path


def test_code_review_pins_fixed_pylint_with_bound_artifact_hashes() -> None:
    """GHSA-22qq-2fwx-7p67 must be fixed in the actual installer inputs."""
    repository_root = Path(__file__).resolve().parents[3]
    requirements = repository_root / "requirements" / "code-review"
    input_bytes = (requirements / "requirements.in").read_bytes()
    assert "pylint==4.0.9" in input_bytes.decode("utf-8")
    locked = (requirements / "locked.txt").read_text(encoding="utf-8")
    assert f"# input-sha256: {hashlib.sha256(input_bytes).hexdigest()}" in locked.splitlines()
    pylint_record = next(record for record in locked.replace("\\\n", "").splitlines() if record.startswith("pylint=="))
    assert pylint_record.split()[0] == "pylint==4.0.9"
    assert {item.removeprefix("--hash=sha256:") for item in pylint_record.split()[1:]} == {
        "c4ba5bbaf1e70ecf05f08cd7d6091ea04824b79a2b2d9f5b10dc25fc34cb1124",
        "6f1305780229ae720e89b8aff2b3ff857cbb268fbab98c8b586960267667ad34",
    }
