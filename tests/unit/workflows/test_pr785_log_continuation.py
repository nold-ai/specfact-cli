import contextlib
import hashlib
import http.client
import importlib.util
import inspect
import io
import json
import os
import re
import socket
import subprocess
import time
import urllib.error
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from typing import Any, NamedTuple
from unittest.mock import create_autospec

import pytest


SOURCE = Path(__file__).resolve().parents[3] / "scripts/pr785_runtime_prerequisite.py"
REAL_HTTPS = http.client.HTTPSConnection
REAL_REQUEST_SIGNATURE = inspect.signature(REAL_HTTPS.request)
REAL_SOCKET = socket.socket
LIMIT = 4 * 1024 * 1024
TOKEN = "SYNTHETIC-PR785-BEARER-NEVER-SERIALIZE"
LOCATION = "https://fixture.blob.core.windows.net/logs?sig=SYNTHETIC-LOCATION-ONE"
SECOND = "https://fixture.actions.githubusercontent.com/logs?sig=SYNTHETIC-LOCATION-TWO"
THIRD = "https://last.blob.core.windows.net/logs?sig=SYNTHETIC-LOCATION-THREE"
MARKER = (
    "PR785_CURRENT_JOB_OBSERVER run=12345 attempt=2 job=67890 "
    "event=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa "
    "workflow=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb phase=before-log-fetch"
)
DATE = "Sat, 24 Oct 2026 00:00:00 GMT"
JOBS_PATH = "/repos/nold-ai/specfact-cli/actions/runs/12345/attempts/2/jobs?per_page=100"
LOGS_PATH = "/repos/nold-ai/specfact-cli/actions/jobs/67890/logs"
STEPS = [
    {
        "name": "Set up job",
        "number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": "2026-10-24T00:00:00Z",
        "completed_at": "2026-10-24T00:00:01Z",
    },
    {
        "name": "Checkout immutable observer",
        "number": 2,
        "status": "in_progress",
        "conclusion": None,
        "started_at": "2026-10-24T00:00:01Z",
        "completed_at": None,
    },
    {
        "name": "Observe current job boundary",
        "number": 3,
        "status": "pending",
        "conclusion": None,
        "started_at": None,
        "completed_at": None,
    },
    {
        "name": "Future step marker",
        "number": 4,
        "status": "pending",
        "conclusion": None,
        "started_at": None,
        "completed_at": None,
    },
    {
        "name": "Upload prerequisite observations",
        "number": 5,
        "status": "pending",
        "conclusion": None,
        "started_at": None,
        "completed_at": None,
    },
    {
        "name": "Post Checkout immutable observer",
        "number": 10,
        "status": "pending",
        "conclusion": None,
        "started_at": None,
        "completed_at": None,
    },
]
JOBS = json.dumps(
    {
        "total_count": 1,
        "jobs": [
            {
                "id": 67890,
                "name": "PR785 runtime platform prerequisites",
                "run_id": 12345,
                "run_attempt": 2,
                "head_sha": "a" * 40,
                "status": "in_progress",
                "conclusion": None,
                "steps": STEPS,
            }
        ],
    }
).encode()
ENVIRONMENT = {
    "GITHUB_RUN_ID": "12345",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_SHA": "a" * 40,
    "GITHUB_WORKFLOW_SHA": "b" * 40,
    "GITHUB_REPOSITORY": "nold-ai/specfact-cli",
    "GITHUB_EVENT_NAME": "workflow_dispatch",
    "GITHUB_JOB": "platform-prerequisites",
    "GITHUB_WORKFLOW_REF": (
        "nold-ai/specfact-cli/.github/workflows/specfact.yml@refs/heads/codex/pr785-runtime-prerequisites"
    ),
    "GH_TOKEN": TOKEN,
    "HTTP_PROXY": "http://proxy.invalid:9",
    "HTTPS_PROXY": "http://proxy.invalid:9",
    "http_proxy": "http://proxy.invalid:9",
    "https_proxy": "http://proxy.invalid:9",
    "NO_PROXY": "",
    "no_proxy": "",
}


class WireResponse(NamedTuple):
    status: int
    body: bytes
    locations: tuple[str, ...] = ()
    failure: str | None = None
    date: str | None = DATE


class Result(NamedTuple):
    requests: list[dict[str, Any]]
    files: dict[str, bytes]
    stdout: str
    stderr: str
    exit_code: int | None


def _blocked(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("Unexpected real network, process, or delay operation")


class WireStream(io.BytesIO):
    fail_body = False
    reading_body = False

    def read(self, size: int | None = -1) -> bytes:
        if self.reading_body:
            assert size is not None and 0 <= size <= LIMIT + 1, "Response read exceeded the bounded evidence limit"
        if self.fail_body:
            raise OSError("Synthetic body failure " + LOCATION + TOKEN)
        return super().read(size)


class WireSocket:
    def __init__(self, wire: bytes) -> None:
        self.stream = WireStream(wire)

    def makefile(self, mode: str) -> WireStream:
        assert mode == "rb"
        return self.stream


class FlushedOutput(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.flushed = ""

    def flush(self) -> None:
        self.flushed = self.getvalue()
        super().flush()


def _wire_response(fixture: WireResponse) -> http.client.HTTPResponse:
    if fixture.failure == "timeout":
        raise TimeoutError("Synthetic timeout " + LOCATION + TOKEN)
    if fixture.failure == "urlerror":
        raise urllib.error.URLError("Synthetic URL error " + LOCATION + TOKEN)
    headers = [
        f"Content-Length: {len(fixture.body)}",
        "Connection: close",
        "X-GitHub-Request-Id: SYNTHETIC-REQUEST-ID",
    ]
    if fixture.date is not None:
        headers.append("Date: " + fixture.date)
    headers.extend("Location: " + value for value in fixture.locations)
    wire = (f"HTTP/1.1 {fixture.status} Synthetic\r\n" + "\r\n".join(headers) + "\r\n\r\n").encode()
    wire_socket = WireSocket(wire + fixture.body)
    socket_double = create_autospec(REAL_SOCKET, instance=True, spec_set=True)
    socket_double.makefile.side_effect = wire_socket.makefile
    response = http.client.HTTPResponse(socket_double, method="GET")
    response.begin()
    wire_socket.stream.reading_body = True
    wire_socket.stream.fail_body = fixture.failure == "body"
    return response


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fixtures: list[WireResponse]) -> Result:
    directory = tmp_path / ("case-" + str(len(list(tmp_path.iterdir()))))
    directory.mkdir(mode=0o700)
    pending = list(fixtures)
    requests: list[dict[str, Any]] = []
    responses: list[http.client.HTTPResponse] = []
    out, err = FlushedOutput(), io.StringIO()

    class RecordingHTTPSConnection(REAL_HTTPS):
        def __init__(self, host: str, timeout: int, **kwargs: Any) -> None:
            assert timeout == 30
            self.host = host
            self.sock = None

        def set_debuglevel(self, level: int) -> None:
            assert level == 0

        def request(self, method: str, url: str, *args: object, **kwargs: object) -> None:
            bound = REAL_REQUEST_SIGNATURE.bind(self, method, url, *args, **kwargs)
            bound.apply_defaults()
            assert pending, "Observer made an unexpected extra request"
            body = bound.arguments["body"]
            encode_chunked = bound.arguments["encode_chunked"]
            assert method == "GET" and body is None and not encode_chunked
            headers = bound.arguments["headers"]
            requests.append(
                {
                    "host": self.host,
                    "path": url,
                    "headers": {key.lower(): value for key, value in headers.items()},
                    "flushed_before_request": out.flushed,
                }
            )

        def getresponse(self) -> http.client.HTTPResponse:
            fixture = pending.pop(0)
            response = _wire_response(fixture)
            responses.append(response)
            return response

        def close(self) -> None:
            self.sock = None

    exit_code = None
    with monkeypatch.context() as patch:
        patch.chdir(directory)
        patch.setattr(os, "environ", dict(ENVIRONMENT))
        patch.setattr(http.client, "HTTPSConnection", RecordingHTTPSConnection)
        patch.setattr(socket, "socket", _blocked)
        patch.setattr(socket, "create_connection", _blocked)
        patch.setattr(socket, "getaddrinfo", _blocked)
        patch.setattr(time, "sleep", _blocked)
        patch.setattr(subprocess, "Popen", _blocked)
        patch.setattr(os, "system", _blocked)
        spec = importlib.util.spec_from_file_location("pr785_observer_under_test", SOURCE)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                module._main()
            except SystemExit as error:
                assert type(error.code) is int
                exit_code = error.code
        assert all(response.closed for response in responses), "Every received response must close"
    output = directory / "platform-prerequisite-observations"
    files = {path.name: path.read_bytes() for path in output.iterdir()}
    secrets = (TOKEN, LOCATION, SECOND, THIRD, *(value for fixture in fixtures for value in fixture.locations if value))
    for secret in secrets:
        assert secret not in out.getvalue() + err.getvalue(), "Transport secret leaked in diagnostic output"
        assert all(secret not in name and secret.encode() not in data for name, data in files.items()), (
            "Transport secret leaked in retained output"
        )
    return Result(requests, files, out.getvalue(), err.getvalue(), exit_code)


def _records(result: Result) -> list[dict[str, Any]]:
    return json.loads(result.files["responses.json"])


def _utc(value: str) -> datetime:
    assert re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|\+00:00)", value)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _retained(result: Result, name: str, fixture: WireResponse) -> dict[str, Any]:
    record = next(record for record in _records(result) if record["name"] == name)
    assert result.files[name + ".raw"] == fixture.body
    expected_metadata = {
        "http_status": fixture.status,
        "bytes": len(fixture.body),
        "sha256": hashlib.sha256(fixture.body).hexdigest(),
        "date": fixture.date,
        "request_id": "SYNTHETIC-REQUEST-ID",
        "redirect_present": bool(fixture.locations),
    }
    assert {key: record[key] for key in expected_metadata} == expected_metadata
    if len(fixture.locations) == 1 and fixture.locations[0]:
        assert record["redirect_sha256"] == hashlib.sha256(fixture.locations[0].encode()).hexdigest()
    assert _utc(record["request_started_at_utc"]) <= _utc(record["body_finished_at_utc"])
    return record


def _requests(result: Result, storage: list[tuple[str, str]]) -> None:
    assert [(request["host"], request["path"]) for request in result.requests] == [
        ("api.github.com", JOBS_PATH),
        ("api.github.com", LOGS_PATH),
        *storage,
    ], "The logs API redirect must produce exactly the bounded storage requests"
    for request in result.requests[:2]:
        assert request["headers"]["authorization"] == "Bearer " + TOKEN
        assert request["headers"]["accept"] == "application/vnd.github+json"
        assert request["headers"]["x-github-api-version"] == "2022-11-28"
    for request in result.requests[2:]:
        assert set(request["headers"]) <= {"user-agent", "host", "connection"}
        assert request["headers"]["user-agent"] == "specfact-pr785-read-only-prerequisite"
        assert TOKEN not in repr(request["headers"])


def _complete(result: Result, terminal: str, fixture: WireResponse, count: int) -> dict[str, Any]:
    assert result.exit_code is None
    summary = json.loads(result.files["observation-only.json"])
    expected_measurement = {
        "terminal_response": terminal,
        "http_status": fixture.status,
        "payload_retained": True,
        "marker_matches": count,
    }
    assert {
        "log_measurement": {key: summary["log_measurement"][key] for key in expected_measurement},
        "compatibility": summary["compatibility"],
        "observed_steps": summary["observed_steps"],
        "expected_future_step_names": summary["expected_future_step_names"],
    } == {
        "log_measurement": expected_measurement,
        "compatibility": "unjudged",
        "observed_steps": STEPS,
        "expected_future_step_names": ["Future step marker", "Upload prerequisite observations"],
    }
    assert summary["authority"] is False and summary["policy_execution"] is False
    assert (result.stdout, result.stderr) == (MARKER + "\n", "")
    emission = json.loads(result.files["marker-emission.json"])
    assert emission["marker"] == MARKER
    emitted = _utc(emission["emitted_at_utc"])
    assert result.requests[0]["flushed_before_request"] == ""
    assert all(request["flushed_before_request"] == MARKER + "\n" for request in result.requests[1:])
    records = _records(result)
    assert _utc(records[0]["body_finished_at_utc"]) <= emitted <= _utc(records[1]["request_started_at_utc"])
    for previous, following in pairwise(records):
        assert _utc(previous["body_finished_at_utc"]) <= _utc(following["request_started_at_utc"])
    _retained(result, terminal, fixture)
    return summary


def _refused(result: Result, reason: str) -> None:
    assert result.exit_code == 1
    assert "observation-only.json" not in result.files, "A partial observation must not fabricate a terminal summary"
    assert _records(result)[-1]["failure_reason"] == reason


def test_api_redirect_retains_both_responses_and_separates_bearer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redirect = WireResponse(302, b"Original API redirect body\n", (LOCATION,))
    terminal = WireResponse(200, (MARKER + "\n").encode())
    result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), redirect, terminal])
    _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")])
    _retained(result, "current-job-logs", redirect)
    record = _retained(result, "current-job-logs-storage-01", terminal)
    assert record["endpoint"] == "current-job-log-storage-hop-1"
    _complete(result, "current-job-logs-storage-01", terminal, 1)


def test_direct_terminal_payload_is_measured_without_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    terminal = WireResponse(200, ("2026-10-24T01:02:03.123Z " + MARKER + "\r\n").encode(), date=None)
    result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), terminal])
    _requests(result, [])
    _complete(result, "current-job-logs", terminal, 1)


def test_three_storage_hops_revalidate_both_allowed_host_families(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for status in (301, 302, 303, 307, 308):
        redirects = [
            WireResponse(status, b"first", (LOCATION,)),
            WireResponse(302, b"second", (SECOND,)),
            WireResponse(307, b"third", (THIRD,)),
        ]
        terminal = WireResponse(200, MARKER.encode())
        result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), *redirects, terminal])
        _requests(
            result,
            [
                ("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE"),
                ("fixture.actions.githubusercontent.com", "/logs?sig=SYNTHETIC-LOCATION-TWO"),
                ("last.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-THREE"),
            ],
        )
        names = ("current-job-logs", "current-job-logs-storage-01", "current-job-logs-storage-02")
        for name, fixture in zip(names, redirects, strict=True):
            _retained(result, name, fixture)
        _complete(result, "current-job-logs-storage-03", terminal, 1)


def test_fourth_redirect_is_retained_without_a_fifth_logs_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redirects = [WireResponse(302, str(index).encode(), (LOCATION,)) for index in range(4)]
    result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), *redirects])
    _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")] * 3)
    for name, fixture in zip(
        (
            "current-job-logs",
            "current-job-logs-storage-01",
            "current-job-logs-storage-02",
            "current-job-logs-storage-03",
        ),
        redirects,
        strict=True,
    ):
        _retained(result, name, fixture)
    _refused(result, "redirect-limit-exceeded")


def test_rejected_locations_never_receive_a_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    locations: list[tuple[str, ...]] = [
        (),
        ("",),
        (LOCATION, SECOND),
        ("http://fixture.blob.core.windows.net/logs",),
        ("/relative",),
        ("https:///missing-host",),
        ("https://[broken",),
        ("https://user:password@fixture.blob.core.windows.net/logs",),
        ("https://fixture.blob.core.windows.net:443/logs",),
        ("https://fixture.blob.core.windows.net/logs#fragment",),
        ("https://blob.core.windows.net/logs",),
        ("https://actions.githubusercontent.com/logs",),
        ("https://fixture.blob.core.windows.net.evil.invalid/logs",),
        ("https://evilblob.core.windows.net/logs",),
        ("https://evilactions.githubusercontent.com/logs",),
        ("https://127.0.0.1/logs",),
        ("https://fixture.blob.core.windows.net./logs",),
        ("https://evil.invalid/logs",),
        ("https://api.github.com/logs",),
        ("https://fixture.blob.core.windows.net/a b",),
    ]
    locations.extend((LOCATION + control,) for control in ("\x00", "\x01", "\x1f", "\x7f", "\t", "\r\n\tfold"))
    for values in locations:
        redirect = WireResponse(302, b"Rejected destination body", values)
        result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), redirect])
        assert len(result.requests) == 2, "Rejected destination must not receive a request"
        _retained(result, "current-job-logs", redirect)
        _refused(result, "redirect-location-invalid")


def test_storage_redirect_to_api_or_http_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for location in ("https://api.github.com/private", "http://fixture.blob.core.windows.net/private"):
        redirect = WireResponse(302, b"Storage redirect", (location,))
        result = _run(
            tmp_path,
            monkeypatch,
            [
                WireResponse(200, JOBS),
                WireResponse(302, b"API", (LOCATION,)),
                redirect,
            ],
        )
        _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")])
        _retained(result, "current-job-logs-storage-01", redirect)
        _refused(result, "redirect-location-invalid")


def test_jobs_redirect_stops_before_marker_or_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    redirect = WireResponse(302, b"Jobs redirect", (LOCATION,))
    result = _run(tmp_path, monkeypatch, [redirect])
    assert [(request["host"], request["path"]) for request in result.requests] == [("api.github.com", JOBS_PATH)]
    assert result.exit_code == 1 and result.stdout == "" and result.stderr == ""
    assert "marker-emission.json" not in result.files and "observation-only.json" not in result.files
    _retained(result, "jobs", redirect)


def test_non_200_terminal_remains_an_unjudged_received_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for status in (403, 404, 500):
        terminal = WireResponse(status, MARKER.encode())
        result = _run(
            tmp_path,
            monkeypatch,
            [
                WireResponse(200, JOBS),
                WireResponse(302, b"API", (LOCATION,)),
                terminal,
            ],
        )
        _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")])
        summary = _complete(result, "current-job-logs-storage-01", terminal, 1)
        assert summary["log_measurement"]["http_status"] != 200


def test_marker_matching_uses_exact_bytes_and_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = MARKER.encode()
    cases = [
        (b"", 0),
        (marker, 1),
        (marker + b"\r\n", 1),
        (marker + b"\n" + marker, 2),
        (b"2026-10-24T01:02:03Z " + marker, 1),
        (b"2026-10-24T01:02:03.123Z " + marker, 1),
        (b"prefix " + marker, 0),
        (marker + b" trailing", 0),
        (b"\xff" + marker, 0),
        (b"2026-10-24T01:02:03Z  " + marker, 0),
        (b"2026-10-24T01:02:03+00:00 " + marker, 0),
        (b"2026-10-24T01:02:03.Z " + marker, 0),
        (b"2026-10-24T01:02:03Z\t" + marker, 0),
        ("２０２６-10-24T01:02:03Z ".encode() + marker, 0),
    ]
    cases.extend(
        (marker.replace(old, new), 0)
        for old, new in (
            (b"run=12345", b"run=12344"),
            (b"attempt=2", b"attempt=1"),
            (b"job=67890", b"job=67891"),
            (b"event=" + b"a" * 40, b"event=" + b"c" * 40),
            (b"workflow=" + b"b" * 40, b"workflow=" + b"c" * 40),
        )
    )
    for raw, count in cases:
        terminal = WireResponse(200, raw)
        result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), terminal])
        _requests(result, [])
        _complete(result, "current-job-logs", terminal, count)


def test_size_limit_preserves_complete_and_refuses_incomplete_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redirect = WireResponse(302, b"API redirect remains", (LOCATION,))
    for size in (LIMIT, LIMIT + 1):
        terminal = WireResponse(200, b"x" * size)
        result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), redirect, terminal])
        _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")])
        _retained(result, "current-job-logs", redirect)
        if size == LIMIT:
            _complete(result, "current-job-logs-storage-01", terminal, 0)
        else:
            _refused(result, "response-too-large")
            assert "current-job-logs-storage-01.raw" not in result.files
            assert _records(result)[-1]["response_retained"] is False
            assert _records(result)[-1]["http_status"] == 200


def test_transport_failures_are_sanitized_and_keep_earlier_responses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redirect = WireResponse(302, b"API redirect remains", (LOCATION,))
    for failure in ("timeout", "urlerror", "body"):
        result = _run(
            tmp_path, monkeypatch, [WireResponse(200, JOBS), redirect, WireResponse(200, b"unread", failure=failure)]
        )
        _requests(result, [("fixture.blob.core.windows.net", "/logs?sig=SYNTHETIC-LOCATION-ONE")])
        _retained(result, "current-job-logs", redirect)
        _refused(result, "body-read-failed" if failure == "body" else "transport-unavailable")
        assert "current-job-logs-storage-01.raw" not in result.files
        record = _records(result)[-1]
        assert record["response_retained"] is False
        assert record["http_status"] == (200 if failure == "body" else None)
        assert "Synthetic" not in json.dumps(record)


def test_lagging_steps_and_post_step_numbers_remain_unmodified(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    terminal = WireResponse(200, b"No current marker in this synthetic sample")
    result = _run(tmp_path, monkeypatch, [WireResponse(200, JOBS), terminal])
    _requests(result, [])
    summary = _complete(result, "current-job-logs", terminal, 0)
    assert summary["observed_steps"][0]["status"] == "completed"
    assert summary["observed_steps"][1]["status"] == "in_progress"
    assert summary["observed_steps"][2]["status"] == "pending"
    assert summary["observed_steps"][-1]["number"] == 10
    _retained(result, "jobs", WireResponse(200, JOBS))
