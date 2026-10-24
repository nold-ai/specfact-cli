"""Observe bounded current-job service responses. No policy/admission outcome."""

import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, NamedTuple, NoReturn


REPOSITORY = "nold-ai/specfact-cli"
JOB_NAME = "PR785 runtime platform prerequisites"
LIMIT = 4 * 1024 * 1024
USER_AGENT = "specfact-pr785-read-only-prerequisite"
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


_Record = dict[str, str | int | bool | None]
_FailureReason = Literal[
    "redirect-location-invalid",
    "redirect-limit-exceeded",
    "response-too-large",
    "transport-unavailable",
    "body-read-failed",
]


class _Context(NamedTuple):
    run: str
    attempt: str
    revision: str
    workflow_revision: str
    context: dict[str, str]


class _ObservationState(NamedTuple):
    output: Path
    opener: urllib.request.OpenerDirector
    observations: list[_Record]


class _Received(NamedTuple):
    status: int
    raw: bytes
    location: str | None
    location_count: int


def _context() -> _Context:
    run, attempt = os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"]
    revision = os.environ["GITHUB_SHA"]
    workflow_revision = os.environ["GITHUB_WORKFLOW_SHA"]
    context = {
        name: os.environ[name]
        for name in ("GITHUB_REPOSITORY", "GITHUB_EVENT_NAME", "GITHUB_JOB", "GITHUB_WORKFLOW_REF")
    }
    if context != {
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_JOB": "platform-prerequisites",
        "GITHUB_WORKFLOW_REF": REPOSITORY
        + "/.github/workflows/specfact.yml@refs/heads/codex/pr785-runtime-prerequisites",
    }:
        raise SystemExit(1)
    if not all(re.fullmatch(r"[1-9][0-9]{0,18}", value) for value in (run, attempt)):
        raise SystemExit(1)
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (revision, workflow_revision)):
        raise SystemExit(1)
    return _Context(run, attempt, revision, workflow_revision, context)


def _save_responses(state: _ObservationState) -> None:
    (state.output / "responses.json").write_text(json.dumps(state.observations, indent=2) + "\n")


def _fail(state: _ObservationState, reason: _FailureReason) -> NoReturn:
    state.observations[-1]["failure_reason"] = reason
    _save_responses(state)
    raise SystemExit(1) from None


def _exchange(
    state: _ObservationState,
    name: str,
    request: urllib.request.Request,
    endpoint_label: str,
) -> _Received:
    record: _Record = {
        "name": name,
        "endpoint": endpoint_label,
        "http_status": None,
        "response_retained": False,
        "request_started_at_utc": datetime.now(UTC).isoformat(),
    }
    state.observations.append(record)
    response: http.client.HTTPResponse | urllib.error.HTTPError
    try:
        try:
            response = state.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
    except (urllib.error.URLError, OSError, http.client.HTTPException):
        record["transport"] = "unavailable"
        _fail(state, "transport-unavailable")
    with response:
        status = response.code if isinstance(response, urllib.error.HTTPError) else response.status
        locations = response.headers.get_all("Location", [])
        location = locations[0] if locations else None
        record.update(
            {
                "http_status": status,
                "request_id": response.headers.get("X-GitHub-Request-Id"),
                "date": response.headers.get("Date"),
                "redirect_present": location is not None,
                "redirect_sha256": hashlib.sha256(location.encode()).hexdigest() if location else None,
            }
        )
        try:
            raw = response.read(LIMIT + 1)
        except (urllib.error.URLError, OSError, http.client.HTTPException):
            record["body_finished_at_utc"] = datetime.now(UTC).isoformat()
            _fail(state, "body-read-failed")
        record["body_finished_at_utc"] = datetime.now(UTC).isoformat()
        if len(raw) > LIMIT:
            _fail(state, "response-too-large")
        http_response = response.fp if isinstance(response, urllib.error.HTTPError) else response
        if not isinstance(http_response, http.client.HTTPResponse) or (
            http_response.length is not None and http_response.length > 0
        ):
            _fail(state, "body-read-failed")
    (state.output / (name + ".raw")).write_bytes(raw)
    record.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "response_retained": True})
    _save_responses(state)
    return _Received(status, raw, location, len(locations))


def _observe(state: _ObservationState, name: str, path: str) -> _Received:
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        },
    )
    return _exchange(state, name, request, path)


def _storage_location(received: _Received) -> str | None:
    location = received.location
    if received.location_count != 1 or not location:
        return None
    if re.search(r"[^\x21-\x7e]", location):
        return None
    try:
        parsed = urllib.parse.urlsplit(location)
    except ValueError:
        return None
    host_pattern = (
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"(?:blob\.core\.windows\.net|actions\.githubusercontent\.com)"
    )
    return (
        location
        if parsed.scheme == "https" and "#" not in location and re.fullmatch(host_pattern, parsed.netloc, re.IGNORECASE)
        else None
    )


def _follow_current_job_logs(state: _ObservationState, initial: _Received) -> tuple[str, _Received]:
    name, received = "current-job-logs", initial
    hop = 0
    while received.status in REDIRECT_STATUSES:
        if hop == 3:
            _fail(state, "redirect-limit-exceeded")
        location = _storage_location(received)
        if location is None:
            _fail(state, "redirect-location-invalid")
        hop += 1
        name = f"current-job-logs-storage-{hop:02d}"
        request = urllib.request.Request(location, headers={"User-Agent": USER_AGENT})
        received = _exchange(state, name, request, f"current-job-log-storage-hop-{hop}")
    return name, received


def _emit_marker(state: _ObservationState, identity: _Context, job_id: int) -> bytes:
    marker = (
        f"PR785_CURRENT_JOB_OBSERVER run={identity.run} attempt={identity.attempt} job={job_id} "
        f"event={identity.revision} workflow={identity.workflow_revision} phase=before-log-fetch"
    )
    sys.stdout.write(marker + "\n")
    sys.stdout.flush()
    emission = {"marker": marker, "emitted_at_utc": datetime.now(UTC).isoformat()}
    (state.output / "marker-emission.json").write_text(json.dumps(emission, indent=2) + "\n")
    return marker.encode("ascii")


def _marker_matches(raw: bytes, expected: bytes) -> int:
    timestamp = rb"(?:[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z )?"
    pattern = rb"(?m)^" + timestamp + re.escape(expected) + rb"(?=\r?\n|\Z)"
    return sum(1 for _ in re.finditer(pattern, raw))


def _main() -> None:
    identity = _context()
    run, attempt, revision, workflow_revision, context = identity
    output = Path("platform-prerequisite-observations")
    output.mkdir(mode=0o700, exist_ok=False)
    opener = urllib.request.OpenerDirector()
    opener.add_handler(urllib.request.ProxyHandler({}))
    opener.add_handler(urllib.request.HTTPSHandler())
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    opener.add_handler(urllib.request.HTTPErrorProcessor())
    state = _ObservationState(output, opener, [])
    received = _observe(state, "jobs", f"repos/{REPOSITORY}/actions/runs/{run}/attempts/{attempt}/jobs?per_page=100")
    if received.status != 200:
        raise SystemExit(1)
    jobs = json.loads(received.raw)
    if jobs["total_count"] != 1 or len(jobs["jobs"]) != 1:
        raise SystemExit(1)
    job = jobs["jobs"][0]
    expected_job = {
        "name": JOB_NAME,
        "run_id": int(run),
        "run_attempt": int(attempt),
        "head_sha": revision,
        "status": "in_progress",
        "conclusion": None,
    }
    observed_job = {name: job[name] for name in expected_job}
    if observed_job != expected_job or type(job["id"]) is not int or job["id"] <= 0:
        raise SystemExit(1)
    marker = _emit_marker(state, identity, job["id"])
    initial = _observe(state, "current-job-logs", f"repos/{REPOSITORY}/actions/jobs/{job['id']}/logs")
    terminal_name, terminal = _follow_current_job_logs(state, initial)
    (output / "observation-only.json").write_text(
        json.dumps(
            {
                "kind": "platform-prerequisite-observation",
                "authority": False,
                "run_id": int(run),
                "attempt": int(attempt),
                "event_commit": revision,
                "workflow_revision": workflow_revision,
                "context": context,
                "event_and_workflow_revisions_equal": revision == workflow_revision,
                "job_id": job["id"],
                "observed_steps": job["steps"],
                "expected_future_step_names": ["Future step marker", "Upload prerequisite observations"],
                "compatibility": "unjudged",
                "policy_execution": False,
                "marker_emission": "marker-emission.json",
                "log_measurement": {
                    "terminal_response": terminal_name,
                    "http_status": terminal.status,
                    "payload_retained": True,
                    "marker_matches": _marker_matches(terminal.raw, marker),
                    "raw_file": terminal_name + ".raw",
                    "sha256": hashlib.sha256(terminal.raw).hexdigest(),
                },
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    _main()
