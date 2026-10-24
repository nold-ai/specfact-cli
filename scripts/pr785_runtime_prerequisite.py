"""Observe two read-only service responses. No policy/admission outcome."""

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


REPOSITORY = "nold-ai/specfact-cli"
JOB_NAME = "PR785 runtime platform prerequisites"
LIMIT = 4 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
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
    output = Path("platform-prerequisite-observations")
    output.mkdir(mode=0o700, exist_ok=False)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    observations = []

    def observe(name, path):
        request = urllib.request.Request(
            "https://api.github.com/" + path,
            headers={
                "Authorization": "Bearer " + os.environ["GH_TOKEN"],
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "specfact-pr785-read-only-prerequisite",
            },
        )
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        except (urllib.error.URLError, OSError, TimeoutError):
            observations.append(
                {
                    "name": name,
                    "endpoint": path,
                    "http_status": None,
                    "transport": "unavailable",
                    "response_retained": False,
                }
            )
            (output / "responses.json").write_text(json.dumps(observations, indent=2) + "\n")
            raise SystemExit(1) from None
        with response:
            raw = response.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise SystemExit(1)
            status = response.code
            location = response.headers.get("Location")
            record = {
                "name": name,
                "endpoint": path,
                "http_status": status,
                "request_id": response.headers.get("X-GitHub-Request-Id"),
                "date": response.headers.get("Date"),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "redirect_present": location is not None,
                "redirect_sha256": hashlib.sha256(location.encode()).hexdigest() if location else None,
            }
        (output / (name + ".raw")).write_bytes(raw)
        observations.append(record)
        (output / "responses.json").write_text(json.dumps(observations, indent=2) + "\n")
        return status, raw

    status, raw = observe("jobs", f"repos/{REPOSITORY}/actions/runs/{run}/attempts/{attempt}/jobs?per_page=100")
    if status != 200:
        raise SystemExit(1)
    jobs = json.loads(raw)
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
    observe("current-job-logs", f"repos/{REPOSITORY}/actions/jobs/{job['id']}/logs")
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
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
