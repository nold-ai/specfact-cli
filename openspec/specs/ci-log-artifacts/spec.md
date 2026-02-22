# ci-log-artifacts Specification

## Purpose
TBD - created by archiving change ci-01-pr-orchestrator-log-artifacts. Update Purpose after archive.
## Requirements
### Requirement: Full Test Logs from Smart-Test-Full in CI

The PR orchestrator workflow SHALL run the full test suite via `hatch run smart-test-full` (or equivalent) so that test and coverage logs are written under `logs/tests/`, and those logs SHALL be uploaded as workflow artifacts so they can be downloaded when a run fails.

**Rationale**: Today only snippets appear in the GitHub UI; full logs are needed to diagnose failures without re-running locally.

#### Scenario: Tests Job Produces and Uploads Test Logs

**Given**: A PR or push that triggers the PR orchestrator and runs the Tests job (code changed, not dev→main skip)

**When**: The Tests job runs `hatch run smart-test-full` (or a step that invokes the smart-test script with level `full`)

**Then**: The smart-test script writes test run output and coverage output to files under `logs/tests/` (e.g. `full_test_run_<timestamp>.log`, `full_coverage_<timestamp>.log` or equivalent), and a subsequent step uploads the contents of `logs/tests/` (and any existing `logs/tests/coverage/coverage.xml`) as a workflow artifact (e.g. name `test-logs` or `test-logs-py312`)

**Acceptance Criteria**:

- Tests job runs full suite in a way that generates log files under `logs/tests/`
- Artifact upload step uses `actions/upload-artifact@v4` with path including `logs/tests/`
- Artifacts are available for download from the Actions run (on failure or always, per policy)

#### Scenario: Download Test Logs After Failed Tests Job

**Given**: The Tests job failed (e.g. smart-test-full exited non-zero)

**When**: A developer opens the workflow run in GitHub Actions and goes to the Artifacts section

**Then**: An artifact (e.g. `test-logs`) is present and contains at least one test log file and, when coverage was run, coverage XML or coverage log, so the developer can inspect full output without re-running locally

**Acceptance Criteria**:

- Failed runs that produced logs have a downloadable artifact with those logs
- Artifact naming is consistent so it can be referenced in docs

---

### Requirement: Repro Logs and Reports Attached to CI Run

The contract-first-ci job (which runs `specfact repro`) SHALL capture repro command stdout/stderr to a log file and SHALL upload that log file plus the repro report directory (e.g. `.specfact/reports/enforcement/`) as workflow artifacts so they can be downloaded when the job fails.

**Rationale**: Repro failures are currently hard to diagnose from CI because only step output (truncated) is visible; full repro output and report YAMLs are needed.

#### Scenario: Contract-First-CI Job Captures and Uploads Repro Logs

**Given**: The contract-first-ci job runs `specfact repro --verbose --crosshair-required --budget 120` (or equivalent)

**When**: The repro command runs (whether it passes or fails)

**Then**: (1) Stdout and stderr of the repro command are captured to a file under `logs/repro/` (e.g. `repro_<timestamp>.log`), and (2) the contents of `.specfact/reports/enforcement/` (if present) are uploaded together with the repro log as workflow artifacts (e.g. `repro-logs` and `repro-reports` or a single `repro-artifacts` artifact)

**Acceptance Criteria**:

- Repro command output is written to a file in `logs/repro/` (directory created if needed)
- Upload step runs after repro (e.g. `if: always()`) so artifacts are available even when repro fails
- Artifact(s) include the repro log file and any report YAMLs under `.specfact/reports/enforcement/`

#### Scenario: Download Repro Artifacts After Failed Repro Step

**Given**: The contract-first-ci job ran and the repro step failed (or completed with issues)

**When**: A developer opens the workflow run and goes to the Artifacts section

**Then**: An artifact such as `repro-logs` or `repro-reports` is present and contains the full repro log and report files so the developer can diagnose without re-running `specfact repro` locally

**Acceptance Criteria**:

- Naming and path are documented so developers know where to find repro logs and reports
- Align with existing specfact.yml behavior (that workflow already uploads `.specfact/reports/enforcement/*.yaml`) for consistency

---

### Requirement: Documentation for CI Log Artifacts

The documentation SHALL describe where to find test and repro log artifacts in GitHub Actions and how to use them for debugging failed runs.

**Rationale**: Contributors need to know that artifacts exist and what they contain.

#### Scenario: Contributor Finds CI Artifact Documentation

**Given**: A contributor has a failed CI run and wants to debug without re-running locally

**When**: They look in the contributing guide, troubleshooting guide, or a reference section on CI

**Then**: They find a short section explaining that test logs and repro logs/reports are uploaded as artifacts, how to download them from the Actions run (Artifacts section), and what each artifact contains (test output, coverage, repro stdout/stderr, repro report YAMLs)

**Acceptance Criteria**:

- At least one doc page (e.g. `docs/guides/troubleshooting.md` or `docs/contributing/`) includes a subsection on CI artifacts
- Section is copy-paste or link friendly (e.g. "Go to the run → Artifacts → download test-logs or repro-logs")

