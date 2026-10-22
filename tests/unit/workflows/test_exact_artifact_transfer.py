from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import stat
import sys
import types
import zipfile
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from typing import Any, NamedTuple
from unittest.mock import patch
from urllib.request import Request

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
STEP_NAMES = (
    "Restore Requirements evidence for Code Review",
    "Restore fresh Requirements execution artifact",
    "Restore producer Requirements evidence for final verdict",
)


def transfer_steps() -> list[dict[str, Any]]:
    workflow = yaml.safe_load((ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    return [next(s for j in workflow["jobs"].values() for s in j["steps"] if s.get("name") == n) for n in STEP_NAMES]


def archive_bytes(entries: list[tuple[str | zipfile.ZipInfo, bytes]] | None = None) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries or [
            ("requirements-evidence.json", b'{"native":"failed"}'),
            ("proof.xml", b"<testsuite/>"),
        ]:
            archive.writestr(name, content)
    return output.getvalue()


class Response(io.BytesIO):
    def __init__(self, body: bytes = b"", status: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


class TransferHarness(NamedTuple):
    run: Callable[..., Path]
    destination: Path
    runner: Path
    requests: list[Request]
    module: types.ModuleType


@pytest.fixture
def transfer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TransferHarness:
    root = tmp_path.resolve()
    workspace, runner = root / "workspace", root / "runner"
    workspace.mkdir()
    runner.mkdir()
    destination = workspace / "artifacts/requirements-evidence"
    env = {
        "GH_TOKEN": "test-secret-never-forward",
        "GITHUB_WORKSPACE": str(workspace),
        "RUNNER_TEMP": str(runner),
        "GITHUB_REPOSITORY_ID": "1085706003",
        "ARTIFACT_REPOSITORY": "nold-ai/specfact-cli",
        "ARTIFACT_ID": "12341352657",
        "ARTIFACT_NAME": "requirements-evidence",
        "ARTIFACT_RUN_ID": "39589983181",
        "ARTIFACT_HEAD_SHA": "d88310de977bfc5d080e7e03c75256434ed937ea",
        "ARTIFACT_EXPECTED_SHA256": "",
        "ARTIFACT_DESTINATION": str(destination),
    }
    body = transfer_steps()[0]["run"].split("<<'PYTHON'\n", 1)[1].rsplit("\nPYTHON", 1)[0]
    program = root / "workflow_artifact_transfer.py"
    program.write_text(body)
    spec = importlib.util.spec_from_file_location("workflow_artifact_transfer", program)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    spec.loader.exec_module(module)
    requests: list[Request] = []

    def run(
        payload: bytes | None = None,
        metadata_update: dict[str, Any] | None = None,
        raw_metadata: bytes | None = None,
        responses: list[Response | Exception] | None = None,
        changes: dict[str, str] | None = None,
    ) -> Path:
        payload = archive_bytes() if payload is None else payload
        selected = dict(env, **(changes or {}))
        metadata: dict[str, Any] = {
            "id": int(selected["ARTIFACT_ID"]),
            "name": selected["ARTIFACT_NAME"],
            "expired": False,
            "size_in_bytes": len(payload),
            "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "workflow_run": {"id": 39589983181, "repository_id": 1085706003, "head_sha": env["ARTIFACT_HEAD_SHA"]},
        }
        metadata.update(metadata_update or {})
        queue: list[Response | Exception] = [Response(raw_metadata or json.dumps(metadata).encode())]
        queue += (
            responses
            if responses is not None
            else [
                Response(status=302, headers={"Location": "https://storage.example/artifact?sig=secret"}),
                Response(payload),
            ]
        )

        def open_response(_opener: Any, request: Request, timeout: float) -> Response:
            requests.append(request)
            assert timeout > 0
            assert queue, "Unexpected request, possibly a listing or retry"
            result = queue.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch.dict(os.environ, selected, clear=True), patch("urllib.request.OpenerDirector.open", open_response):
            module.main()
        return Path(selected["ARTIFACT_DESTINATION"])

    return TransferHarness(run, destination, runner, requests, module)


def test_three_transfers_share_program_and_fixed_subjects() -> None:
    steps = transfer_steps()
    assert len({step["run"] for step in steps}) == 1
    assert all("/usr/bin/python3 -I -S" in step["run"] for step in steps)
    assert [s["env"]["ARTIFACT_NAME"] for s in steps] == [
        "requirements-evidence",
        "requirements-evidence-execution",
        "requirements-evidence",
    ]
    assert steps[1]["env"]["ARTIFACT_EXPECTED_SHA256"] == "${{ needs.requirements-evidence.outputs.artifact-digest }}"


@pytest.mark.parametrize("artifact_id", ["12341352657", "12341630570"])
def test_exact_id_restores_inert_files_without_listing_or_token_forwarding(
    transfer: TransferHarness, artifact_id: str
) -> None:
    run, destination, _, requests, _ = transfer
    destination.mkdir(parents=True)
    (destination / "unrelated-context.json").write_bytes(b"keep")
    run(changes={"ARTIFACT_ID": artifact_id})
    assert (destination / "requirements-evidence.json").read_bytes() == b'{"native":"failed"}'
    assert (destination / "unrelated-context.json").read_bytes() == b"keep"
    assert all(
        stat.S_IMODE(p.stat().st_mode) == 0o600 for p in destination.iterdir() if p.name != "unrelated-context.json"
    )
    assert [r.full_url for r in requests[:2]] == [
        f"https://api.github.com/repos/nold-ai/specfact-cli/actions/artifacts/{artifact_id}",
        f"https://api.github.com/repos/nold-ai/specfact-cli/actions/artifacts/{artifact_id}/zip",
    ]
    assert all(r.get_header("Authorization") for r in requests[:2])
    assert requests[2].get_header("Authorization") is None


def test_execution_layout_requires_independent_digest(transfer: TransferHarness) -> None:
    run, _, runner, _, _ = transfer
    payload = archive_bytes(
        [
            ("requirements-evidence.json", b"{}"),
            ("requirements-proof.xml", b"<testsuite/>"),
            ("requirements-evidence-plan.json", b"{}"),
        ]
    )
    changes = {
        "ARTIFACT_NAME": "requirements-evidence-execution",
        "ARTIFACT_DESTINATION": str(runner / "requirements-execution"),
    }
    with pytest.raises(ValueError):
        run(payload, changes=changes)
    changes["ARTIFACT_EXPECTED_SHA256"] = hashlib.sha256(payload).hexdigest()
    destination = run(payload, changes=changes)
    assert sorted(p.name for p in destination.iterdir()) == [
        "requirements-evidence-plan.json",
        "requirements-evidence.json",
        "requirements-proof.xml",
    ]


@pytest.mark.parametrize(
    "update",
    [
        {"id": 1},
        {"id": True},
        {"name": "wrong"},
        {"expired": True},
        {"expired": 0},
        {"digest": ""},
        {"digest": "md5:" + "a" * 32},
        {"digest": "sha256:" + "0" * 64},
        {"size_in_bytes": 0},
        {"size_in_bytes": True},
        {"size_in_bytes": 16777217},
        {"size_in_bytes": 1},
        {
            "workflow_run": {
                "id": 1,
                "repository_id": 1085706003,
                "head_sha": "d88310de977bfc5d080e7e03c75256434ed937ea",
            }
        },
        {
            "workflow_run": {
                "id": 39589983181,
                "repository_id": 1,
                "head_sha": "d88310de977bfc5d080e7e03c75256434ed937ea",
            }
        },
        {"workflow_run": {"id": 39589983181, "repository_id": 1085706003, "head_sha": "0" * 40}},
    ],
)
def test_artifact_association_mismatch_never_publishes(transfer: TransferHarness, update: dict[str, Any]) -> None:
    run, destination, _, _, _ = transfer
    with pytest.raises((ValueError, OSError)):
        run(metadata_update=update)
    assert not destination.exists()


@pytest.mark.parametrize(
    "raw", [b'{"id":1,"id":2}', b"{", b"[]", b"x" * 1048577], ids=["duplicate", "truncated", "wrong-shape", "oversized"]
)
def test_invalid_rest_json_fails_closed(transfer: TransferHarness, raw: bytes) -> None:
    run, destination, _, _, _ = transfer
    with pytest.raises(ValueError):
        run(raw_metadata=raw)
    assert not destination.exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://storage.example/a",
        "https://user:pass@storage.example/a",
        "file:///tmp/a",
        "https://storage.example:443/a#fragment",
    ],
)
def test_unsafe_redirect_never_receives_credentials(transfer: TransferHarness, url: str) -> None:
    run, destination, _, requests, _ = transfer
    with pytest.raises(ValueError):
        run(responses=[Response(status=302, headers={"Location": url})])
    assert len(requests) == 2
    assert not destination.exists()


@pytest.mark.parametrize(
    "responses",
    [
        [Response(status=404)],
        [Response(status=403)],
        [Response(status=410)],
        [Response(status=302)],
        [Response(b"truncated")],
        [Response(status=302, headers={"Location": "https://storage.example/a"}) for _ in range(6)],
        [TimeoutError("timeout")],
        [Response(b"", headers={"Content-Length": "999999999"})],
    ],
)
def test_transport_failure_never_publishes(transfer: TransferHarness, responses: list[Response | Exception]) -> None:
    run, destination, _, _, _ = transfer
    with pytest.raises((ValueError, OSError)):
        run(responses=responses)
    assert not destination.exists()


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "C:drive", "a\\b", "nested/a", ".", "..", "folder/", "bad\nname"]
)
def test_unsafe_archive_paths_are_inert(transfer: TransferHarness, name: str) -> None:
    run, destination, _, _, _ = transfer
    with pytest.raises(ValueError):
        run(archive_bytes([("good.json", b"ok"), (name, b"bad")]))
    assert not destination.exists()


@pytest.mark.parametrize("kind", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFDIR, stat.S_IFSOCK])
def test_nonregular_members_never_publish(transfer: TransferHarness, kind: int) -> None:
    run, destination, _, _, _ = transfer
    member = zipfile.ZipInfo("evil")
    member.create_system = 3
    member.external_attr = (kind | 0o777) << 16
    with pytest.raises(ValueError):
        run(archive_bytes([("good.json", b"ok"), (member, b"outside")]))
    assert not destination.exists()


@pytest.mark.parametrize("names", [["same", "same"], ["Same", "same"]])
def test_archive_name_collisions_never_publish(transfer: TransferHarness, names: list[str]) -> None:
    run, destination, _, _, _ = transfer
    expected_warning = pytest.warns(UserWarning, match="Duplicate name") if names[0] == names[1] else nullcontext()
    with expected_warning:
        payload = archive_bytes([(n, b"data") for n in names])
    with pytest.raises(ValueError):
        run(payload)
    assert not destination.exists()


def test_corrupt_member_does_not_publish_earlier_valid_member(transfer: TransferHarness) -> None:
    run, destination, _, _, _ = transfer
    payload = archive_bytes([("first.json", b"first"), ("second.json", b"second")])
    broken = bytearray(payload)
    index = broken.index(b"PK\x01\x02")
    broken[index + 16] ^= 1
    with pytest.raises(zipfile.BadZipFile):
        run(bytes(broken))
    assert not destination.exists() or not list(destination.iterdir())


@pytest.mark.parametrize("existing", ["file", "symlink", "parent-symlink"])
def test_existing_evidence_and_symlink_parents_are_preserved(
    transfer: TransferHarness, existing: str, tmp_path: Path
) -> None:
    run, destination, _, _, _ = transfer
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"unchanged")
    if existing == "parent-symlink":
        destination.parent.symlink_to(outside, target_is_directory=True)
    else:
        destination.mkdir(parents=True)
        target = destination / "requirements-evidence.json"
        target.symlink_to(outside / "missing") if existing == "symlink" else target.write_bytes(b"old")
    with pytest.raises((ValueError, OSError)):
        run()
    assert sentinel.read_bytes() == b"unchanged"
    if existing == "file":
        assert (destination / "requirements-evidence.json").read_bytes() == b"old"


def test_member_count_and_expansion_are_bounded(transfer: TransferHarness) -> None:
    run, destination, _, _, _ = transfer
    with pytest.raises(ValueError):
        run(archive_bytes([(f"report-{n}.json", b"x") for n in range(129)]))
    with pytest.raises(ValueError):
        run(archive_bytes([("large.json", b"x" * (16 * 1024 * 1024 + 1))]))
    assert not destination.exists()


def test_raw_nul_and_encrypted_members_are_rejected(transfer: TransferHarness) -> None:
    run, destination, _, _, _ = transfer
    payload = archive_bytes([("unsafe_name", b"inert")])
    with pytest.raises(ValueError):
        run(payload.replace(b"unsafe_name", b"unsafe\x00name"))
    encrypted = bytearray(payload)
    encrypted[6] |= 1
    encrypted[encrypted.index(b"PK\x01\x02") + 8] |= 1
    with pytest.raises(ValueError):
        run(bytes(encrypted))
    assert not destination.exists()


def test_digest_mismatch_precedes_zip_interpretation(transfer: TransferHarness) -> None:
    run, destination, _, _, module = transfer
    payload = archive_bytes()
    with (
        patch.object(module.zipfile, "ZipFile", side_effect=AssertionError("Unverified ZIP interpreted")),
        pytest.raises(ValueError),
    ):
        run(payload, metadata_update={"digest": "sha256:" + "0" * 64})
    assert not destination.exists()


def test_independent_digest_mismatch_fails_before_download(transfer: TransferHarness) -> None:
    run, destination, _, requests, _ = transfer
    with pytest.raises(ValueError):
        run(changes={"ARTIFACT_EXPECTED_SHA256": "f" * 64})
    assert len(requests) == 1
    assert not destination.exists()


def test_redirect_chain_never_recovers_authorization(transfer: TransferHarness) -> None:
    run, _, _, requests, _ = transfer
    payload = archive_bytes()
    run(
        payload,
        responses=[
            Response(status=302, headers={"Location": "https://storage.example/a"}),
            Response(status=307, headers={"Location": "https://api.github.com/redirected"}),
            Response(payload),
        ],
    )
    assert all(r.get_header("Authorization") is None for r in requests[2:])


def test_publication_collision_preserves_concurrent_file(transfer: TransferHarness) -> None:
    run, destination, _, _, module = transfer
    link = module.os.link

    def collide(source: str, target: str, **kwargs: Any) -> None:
        assert (destination / "requirements-evidence.json").exists() is False
        (destination / target).write_bytes(b"concurrent evidence")
        link(source, target, **kwargs)

    with patch.object(module.os, "link", collide), pytest.raises(FileExistsError):
        run()
    assert (destination / "requirements-evidence.json").read_bytes() == b"concurrent evidence"
    assert not (destination / "proof.xml").exists()
    assert not list(destination.glob(".artifact-stage-*"))


def test_fresh_destinations_are_exclusive(transfer: TransferHarness) -> None:
    run, _, runner, _, _ = transfer
    destination = runner / "requirements-producer"
    destination.mkdir()
    with pytest.raises(ValueError):
        run(changes={"ARTIFACT_DESTINATION": str(destination)})
    assert not list(destination.iterdir())


def test_destination_escape_is_rejected_before_network(transfer: TransferHarness) -> None:
    run, _, runner, requests, _ = transfer
    with pytest.raises(ValueError):
        run(changes={"ARTIFACT_DESTINATION": str(runner / "elsewhere")})
    assert requests == []


def test_absolute_transfer_deadline_is_enforced(transfer: TransferHarness) -> None:
    run, destination, _, _, module = transfer
    times = iter([0, 0, 91])
    with patch.object(module.time, "monotonic", lambda: next(times)), pytest.raises(TimeoutError):
        run()
    assert not destination.exists()


def test_declared_total_expansion_limit_is_enforced(transfer: TransferHarness) -> None:
    run, destination, _, _, module = transfer
    with patch.object(module, "MAX_EXPANDED", 5), pytest.raises(ValueError):
        run(archive_bytes([("first", b"123"), ("second", b"456")]))
    assert not destination.exists()
