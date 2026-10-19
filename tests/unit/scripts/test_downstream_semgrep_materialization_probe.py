from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts import downstream_semgrep as boundary
from tools.downstream_semgrep import test_artifact_materialization as probe


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    path = tmp_path / "semgrep-1.179.0+specfact.1-py3-none-any.whl"
    path.write_bytes(b"synthetic test wheel\x00\xff" * 100)
    return path


def test_probe_reads_candidate_without_modifying_it(candidate: Path) -> None:
    original = candidate.read_bytes()
    evidence: dict[str, object] = {}
    probe._run_probe(candidate, evidence)
    assert candidate.read_bytes() == original
    assert evidence["contexts_verified"] == 5
    assert evidence["transport_mutations"] == ["same_inode_overwrite", "replacement", "deletion"]


def test_probe_rejects_wrong_materialized_bytes(candidate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = boundary.AdmittedWheel.materialize

    @contextmanager
    def corrupted(self: boundary.AdmittedWheel) -> Iterator[Path]:
        with original(self) as path:
            path.write_bytes(b"different bytes")
            yield path

    monkeypatch.setattr(boundary.AdmittedWheel, "materialize", corrupted)
    with pytest.raises(AssertionError, match="bytes"):
        probe._run_probe(candidate, {})


def test_probe_rejects_leaked_materialization(candidate: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = tmp_path / "leaked"
    directory.mkdir(mode=0o700)
    materialized = directory / candidate.name
    materialized.write_bytes(candidate.read_bytes())

    @contextmanager
    def leaking(self: boundary.AdmittedWheel) -> Iterator[Path]:
        yield materialized

    monkeypatch.setattr(boundary.AdmittedWheel, "materialize", leaking)
    with pytest.raises(AssertionError, match="cleanup"):
        probe._run_probe(candidate, {})


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode negative control")
def test_probe_rejects_exposed_directory(candidate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = boundary.AdmittedWheel.materialize

    @contextmanager
    def exposed(self: boundary.AdmittedWheel) -> Iterator[Path]:
        with original(self) as path:
            path.parent.chmod(0o777)
            yield path

    monkeypatch.setattr(boundary.AdmittedWheel, "materialize", exposed)
    with pytest.raises(AssertionError, match="group or other"):
        probe._run_probe(candidate, {})


def test_probe_rejects_nonzero_child(candidate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe, "_CHILD_READ", "raise SystemExit(23)")
    with pytest.raises(AssertionError, match=r"child.*23"):
        probe._run_probe(candidate, {})


@pytest.mark.parametrize("child", ["print('0' * 64)", "import sys; sys.stdout.buffer.write(b'\\xff')"])
def test_probe_rejects_invalid_child_digest(candidate: Path, monkeypatch: pytest.MonkeyPatch, child: str) -> None:
    monkeypatch.setattr(probe, "_CHILD_READ", child)
    with pytest.raises((AssertionError, UnicodeDecodeError)):
        probe._run_probe(candidate, {})


def test_probe_reports_nonzero_failure_as_json(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(Path(probe.__file__)), str(tmp_path / "missing.whl")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode != 0
    result = json.loads(completed.stdout)
    assert result["status"] == "failed"
    assert result["candidate_only"] is True
    assert result["production_admission"] == "not_requested"
    assert result["fixture"] == "synthetic-private-authority-test-only"


@pytest.mark.parametrize("defect", ["null_dacl", "absent_dacl", "untrusted_allow", "unreadable_sddl", "missing_file"])
def test_windows_observation_rejects_untrusted_or_incomplete_acl(
    candidate: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    current = "S-1-5-21-100-200-300-1001"
    descriptors: list[dict[str, object]] = [
        {
            "path": str(path),
            "owner": current,
            "sddl": "O:SYG:SYD:(A;;FA;;;SY)",
            "dacl_present": True,
            "null_dacl": False,
            "rules": [{"type": "Allow", "sid": current, "rights": 2032127}],
        }
        for path in (candidate.parent, candidate)
    ]
    patches: dict[str, tuple[int, dict[str, object]]] = {
        "null_dacl": (0, {"null_dacl": True}),
        "absent_dacl": (0, {"dacl_present": False}),
        "untrusted_allow": (1, {"rules": [{"type": "Allow", "sid": "S-1-1-0", "rights": 1}]}),
        "unreadable_sddl": (0, {"sddl": ""}),
    }
    if defect == "missing_file":
        descriptors.pop()
    else:
        index, patch = patches[defect]
        descriptors[index].update(patch)
    completed = subprocess.CompletedProcess(
        args=["synthetic Get-Acl response"],
        returncode=0,
        stdout=json.dumps({"current_user": current, "descriptors": descriptors}),
        stderr="",
    )
    monkeypatch.setattr(probe.subprocess, "run", lambda *args, **kwargs: completed)
    with pytest.raises(AssertionError, match="Windows"):
        probe._windows_privacy(candidate, {})


def test_cleanup_error_fails_executable(
    candidate: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    original = boundary.AdmittedWheel.materialize

    @contextmanager
    def failed_cleanup(self: boundary.AdmittedWheel) -> Iterator[Path]:
        with original(self) as path:
            yield path
        raise OSError("synthetic cleanup error")

    monkeypatch.setattr(boundary.AdmittedWheel, "materialize", failed_cleanup)
    monkeypatch.setattr(sys, "argv", ["probe", str(candidate)])
    assert probe._main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "failed"
    assert result["error_type"] == "OSError"


@pytest.fixture
def windows_acl(candidate: Path) -> tuple[str, list[dict[str, object]]]:
    current = "S-1-5-21-100-200-300-1001"
    descriptors: list[dict[str, object]] = [
        {
            "path": str(path),
            "owner": current,
            "sddl": f"O:{current}G:SYD:(A;;FA;;;{current})(A;;FA;;;SY)(A;;FA;;;BA)",
            "dacl_present": True,
            "null_dacl": False,
            "rules": [
                {"type": "Allow", "sid": sid, "rights": 2032127} for sid in (current, "S-1-5-18", "S-1-5-32-544")
            ],
        }
        for path in (candidate.parent, candidate)
    ]
    return current, descriptors


@pytest.mark.parametrize("descriptor_index", [0, 1], ids=["directory", "file"])
@pytest.mark.parametrize(
    "acl_case",
    [
        pytest.param((None, None, None), id="current-user-owner"),
        pytest.param(("S-1-5-18", None, None), id="system-owner"),
        pytest.param(("S-1-5-32-544", None, None), id="administrators-owner"),
        pytest.param(("S-1-5-21-100-200-300-1002", None, "owner is untrusted"), id="untrusted-owner"),
        pytest.param(("S-1-3-4", None, "owner is untrusted"), id="owner-rights-is-not-an-owner"),
        pytest.param((None, "S-1-1-0", "grants access to an untrusted SID"), id="everyone-allow"),
        pytest.param((None, "S-1-5-32-545", "grants access to an untrusted SID"), id="users-allow"),
        pytest.param((None, "S-1-5-11", "grants access to an untrusted SID"), id="authenticated-users-allow"),
        pytest.param((None, "S-1-3-0", "grants access to an untrusted SID"), id="creator-owner-allow"),
        pytest.param((None, "S-1-3-1", "grants access to an untrusted SID"), id="creator-group-allow"),
        pytest.param((None, "S-1-3-99", "grants access to an untrusted SID"), id="unknown-special-sid-allow"),
    ],
)
def test_windows_owner_rights_resolves_only_to_trusted_descriptor_owner(
    candidate: Path,
    monkeypatch: pytest.MonkeyPatch,
    descriptor_index: int,
    acl_case: tuple[str | None, str | None, str | None],
    windows_acl: tuple[str, list[dict[str, object]]],
) -> None:
    owner, extra_sid, expected_error = acl_case
    current, descriptors = windows_acl
    owner = current if owner is None else owner
    allowed = ["S-1-3-4", "S-1-5-18", "S-1-5-32-544"]
    if extra_sid is not None:
        allowed.append(extra_sid)
    descriptors[descriptor_index].update(
        owner=owner,
        sddl=f"O:{owner}G:SYD:" + "".join(f"(A;;FA;;;{sid})" for sid in allowed),
        rules=[{"type": "Allow", "sid": sid, "rights": 2032127} for sid in allowed],
    )
    response = {"current_user": current, "descriptors": descriptors}
    completed = subprocess.CompletedProcess(
        args=["synthetic Get-Acl response"], returncode=0, stdout=json.dumps(response), stderr=""
    )
    monkeypatch.setattr(probe.subprocess, "run", lambda *args, **kwargs: completed)
    observation: dict[str, object] = {}
    if expected_error is not None:
        with pytest.raises(AssertionError, match=expected_error):
            probe._windows_privacy(candidate, observation)
        return
    probe._windows_privacy(candidate, observation)
    assert observation["native_acl"] == response
    assert observation["stdout"] == completed.stdout
