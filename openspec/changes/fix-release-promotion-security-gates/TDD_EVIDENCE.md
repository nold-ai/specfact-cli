# TDD Evidence

Change: `fix-release-promotion-security-gates`

Baseline: `origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c`

## Failing before

Timestamp: 2026-09-02 00:17:45 Europe/Berlin

Environment: macOS arm64, Python 3.13.14, pytest 9.1.1. The interpreter came
from the existing repository-frozen environment; the clean replay worktree had
no synchronized environment yet. Production files remained identical to
`origin/dev` apart from the OpenSpec-native archive of already-completed #689.

Command:

```text
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest \
  tests/unit/security/test_release_promotion_security_gates.py -q
```

Result: expected failure, exit 1; 11 collected, 11 failed. Each scenario failed
at its intended pre-fix observation: uv cache enabled; manual dispatch present;
npm cache present; Semgrep/MCP old graph and waiver; Code Review lock unbound;
Pylint exception leaked; archive Git results unchecked; `python -m pytest`
shadowable; invalid UTF-8 diagnostic leaked; `rg` lacked `--`; version remained
0.55.3.

## Passing after

Timestamp: 2026-09-02 01:43 Europe/Berlin

The independent frozen diff scan added four boundary regressions after the
initial red commit: exact regenerated Code Review closure, one immutable merge
base, credential-free proof execution, and a separate fresh-runner review
handoff that authenticates the exact head and installs tools before artifact
download.
Before their implementation, the extended focused run collected 18 tests and
failed 7 at those new contract points.

Focused passing command:

```text
.venv/bin/pytest -q \
  tests/unit/security/test_release_promotion_security_gates.py \
  tests/unit/scripts/test_check_license_compliance.py \
  tests/unit/scripts/test_dependency_trust_review.py \
  tests/unit/scripts/test_requirements_evidence_pre_commit.py \
  tests/unit/scripts/test_requirements_proof_executor.py \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py \
  tests/unit/workflows/test_requirements_evidence_producer_regressions.py \
  tests/unit/workflows/test_trustworthy_green_checks.py
```

Result: exit 0; 153 passed.

Final CI-equivalent full gate used the repository's
`tools/smart_test_coverage.py run --level full` on Python 3.12 with the locked
module fixture commit `69f075819be5e1ceca1446b026b0417f19e584ca` and tree
`5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`. Result: exit 0; 3,068
passed, 10 skipped, no failures; coverage collection completed at 64%.

Additional passing evidence:

- exact frozen closure regeneration and `uv lock --check`;
- both frozen `security_audit_gate.py` invocations with no unreviewed advisories;
- environment-scoped license gate with Pylint 4.0.7 isolated to Code Review;
- Ruff formatting/lint, BasedPyright (0 errors), actionlint, yamllint, docs contracts;
- strict module signatures for all four bundled manifests;
- Semgrep SAST (0 findings) and Bandit (0 medium/high findings).
