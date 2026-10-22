# Test-first evidence

## Local RED before production edits

Captured on 2026-10-22 Europe/Berlin against main commit 5262efb0 in the
dedicated release worktree. The final exact mapping selects 34 tests.
Result: **19 failed, 15 passed, 0 errors, 0 skipped**. The unchanged frozen
main dependencies ran in a newly bootstrapped private Python 3.12 environment.
The baseline runtime version remains 0.55.4.

Observed failures include the compromised emSign certificate fingerprint in the
hash-pinned certifi wheel, an outside GitPython submodule reaching the clone
boundary, and PyJWT inspection mutating caller options. The source distribution
build fails because modules/bundle-mapper is absent. The other failures establish
old tooling selections, old documentation selections, missing bounded JSON floor,
the missing approved MCP record, old Semgrep selection, and old release metadata.
The expiry and future-review cases fail on the missing register's different
diagnostic. Existing negative audit cases and hostile wheel controls pass.

The exact frozen PyJWT probe also executes signed and padded token decoding.
No installed verifier PyJWT import supplies that compatibility evidence.

Local command:

```sh
. /private/tmp/specfact-release-20261022/red-owner/env.sh
python - <<'PYTEST'
import json
import subprocess
import sys
from pathlib import Path
root = Path("/private/tmp/specfact-release-20261022/red-owner")
selectors = json.loads((root / "selectors.json").read_text())
raise SystemExit(subprocess.call([
    sys.executable, "-m", "pytest", "--override-ini", "addopts=", "-q",
    f"--junitxml={root / 'mapped-local-red.xml'}", *selectors,
]))
PYTEST
```

Local artifacts:

- `/private/tmp/specfact-release-20261022/red-owner/selectors.json`
- `/private/tmp/specfact-release-20261022/red-owner/mapped-local-red.log`
- `/private/tmp/specfact-release-20261022/red-owner/mapped-local-red.xml`
- JUnit SHA256 `1de2aacfd11fc90c4bf422e2824adadaa9aeeacbeef5297eaff28081e79defec`

## Native planning and review status

`openspec validate isolate-semgrep-security-runtime --strict` passes.
Ruff checks pass for all seven changed test files.
The released immutable fixture's native staged `planned` gate passes.
Its source mapping digest is `sha256:8e3941ca05ccf9bceaea351df6cc1e642508debfc4ab87ecdc7b6b9cc45e6820`.
The combined plan digest is `sha256:9ef1ef74652759ecb82f7af7c8fa2b19c1d36b0d0bf043e2ed9b1a764bae95b2`.
Independent AI technical review accepted this exact mapping and its 34 selectors.
The retained review is `requirements-proof/independent-review.md`, SHA256
`a981d9f787bd7dab64650254f50ebaa74cef55b79af64441c41525d7ced9692e`.
The acceptance record identifies that reviewer and does not represent human authority.

Native test-authored acceptance, normal local hooks, a test-first commit, and
retained native CI RED are still required before any production changes.
Local JUnit does not replace native CI provenance. Mapping, selected tests,
ancestor conftest files, and transitive Python imports must freeze after native RED.
No prior dev admission or local signing supplies native evidence.

## Final verification still required

After native RED, verify the refreshed official artifacts and both strict audit
lanes, actual Ruby compatibility and documentation builds, changelog scope,
published-runtime byte equality except authorized versions, strict signatures,
and all required quality and CI gates. Merge and publication remain unauthorized.

## Test-first commit checks

The normal pre-commit hooks passed, including native test-authored planning,
format, lint, workflow and Markdown checks, and enforced Code Review.
Code Review reported 0 errors, 45 warnings and 3 informational observations.
All 45 warnings and two observations point to unchanged existing test bodies.
Their retention is a narrow baseline exception for this dependency-only release,
not a waiver of a required check. The new observation concerns the frozen JWT
probe's 48-line install, subprocess and assertion sequence. That explicit
sequence keeps its authenticated delivery artifact and isolated interpreter
visible. No additional wrapper or shared mutable fixture is introduced solely
to reduce its line count. Independent mapping review verified this boundary.

The exact local report and changed-line comparison are retained under
`/private/tmp/specfact-release-20261022/red-owner/test-only-code-review.json` and
`code-review-line-triage.json`. Native CI RED and final release gates remain pending.
