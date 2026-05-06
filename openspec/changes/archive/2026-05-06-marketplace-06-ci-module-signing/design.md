# Design: CI-Driven Module Signing On PR Approval

## Context

Module signing uses an Ed25519 or RSA private key (`SPECFACT_MODULE_PRIVATE_SIGN_KEY`) with passphrase
(`SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`) to produce a detached signature over the full module
payload. Both secrets are already configured as GitHub repository secrets and are used by the existing
`publish-modules.yml` and `create-release` workflows. The signing script (`scripts/sign-modules.py`)
supports fully non-interactive operation via environment variables, falling back to
`getpass.getpass()` only when stdin is a tty and no secret is available — that fallback is the
blocker.

Two places enforce `--require-signature` today regardless of branch context:

1. `scripts/pre-commit-smart-checks.sh` — always runs `verify --require-signature` as the first
   pre-commit gate; blocks every local commit when no key is present.
2. `.github/workflows/pr-orchestrator.yml` `verify-module-signatures` job — all subsequent jobs
   (`needs: [verify-module-signatures]`), so unsigned modules block the entire CI matrix on any
   branch.

The trust boundary that matters is `main`: modules published to the registry always come from
`main`, and the end-user install path always verifies signatures against the public key. Signatures
on feature or dev branches carry no trust value for end users; they only serve as a CI gate that
today has no automated path to satisfy without the private key locally.

## Goals / Non-Goals

**Goals:**

- Eliminate the local private-key requirement for all development on non-`main` branches.
- Sign changed module manifests automatically via CI secrets when a PR to `dev` or `main` is
  approved, committing the signed manifests back to the PR branch before merge.
- Enforce `--require-signature` only at the `main` trust boundary (PR targeting `main` and push to
  `main`).
- Make non-interactive development (AI agents, Cursor, headless CI) on feature/dev branches fully
  functional without any signing setup.

**Non-Goals:**

- Changing module install-time verification (always `--require-signature` from the main registry).
- Replacing the `create-release` post-merge signing step (kept as a safety net).
- Changing `publish-modules.yml` or the public key in `resources/keys/`.
- Adding signing support to external/third-party repositories.

## Decisions

### Decision 1: Trigger on `pull_request_review` (approved), not on PR open/sync

**Chosen**: `pull_request_review` with `types: [submitted]`, filtered on
`github.event.review.state == 'approved'` and `github.event.pull_request.base.ref in [dev, main]`.

**Alternatives considered**:

- *On PR open/sync*: Signs on every push to the branch. Wastes secrets API calls for each force-push
  or fixup commit. Also signs before code review, which means reviewers see unsigned manifests and
  the signing commit arrives as a surprise after approval.
- *On merge to dev/main*: Too late for the pre-merge `--require-signature` verify gate to pass.
  Would require removing the pre-merge verify or adding a post-merge fix-up commit.
- *Manual `workflow_dispatch`*: Requires human to remember to trigger it; defeats the automation
  goal.

**Rationale**: Approval is the natural trust signal. The PR author's implementation is accepted;
the signing commit is a deterministic consequence of that acceptance, not an implementation
artifact. It also means CI re-runs on the signing commit, giving a clean green check on the
signed manifests.

### Decision 2: Push signed manifests back to the PR branch (write-back pattern)

**Chosen**: The signing workflow checks out the PR head, runs `sign-modules.py`, commits, and
pushes using `GITHUB_TOKEN` with `contents: write`.

**Alternatives considered**:

- *In-job sign + verify (no push-back)*: Signs and verifies in the same job but never persists the
  signed manifests. `main` would receive unsigned manifests; the signing would be ephemeral.
- *Sign on merge queue*: GitHub merge queues are not available on the free plan; introduces
  dependency on billing tier.
- *Require developers to sign before approval*: Reverts to the current broken state.

**Avoiding CI loop**: `GITHUB_TOKEN`-triggered pushes do NOT re-run workflows by default in GitHub
Actions. The signing commit will appear in the PR timeline but will not re-trigger the approval
workflow. If stricter loop prevention is needed, the commit message includes `[skip ci]`.

**Idempotency**: If the workflow runs twice (e.g., two approvals), `sign-modules.py` with
`--changed-only` detects no payload change since the last sign commit and skips. The resulting
manifest is byte-for-byte identical due to deterministic YAML serialisation.

### Decision 3: Branch-aware pre-commit — policy bundles in `module-verify-policy.sh`

**Chosen**: `scripts/git-branch-module-signature-flag.sh` emits `require` on `main` and `omit` elsewhere
(including detached `HEAD`). `scripts/pre-commit-verify-modules.sh` sources
`scripts/module-verify-policy.sh` and runs **`VERIFY_MODULES_STRICT`** vs **`VERIFY_MODULES_PR`**
(`--skip-checksum-verification` on omit so local commits are not blocked by stale checksums before CI
re-signs). There is **no** `--allow-unsigned` on `verify-modules-signature.py` (that flag belongs to
**`sign-modules.py`** for explicit test signing).

**Rationale**: Removes the local key and local re-sign loop for routine feature work. The `main`
pre-commit guard stays strict; protected-branch enforcement also runs in **`sign-modules.yml`** on
push to `dev`/`main` after auto-sign.

### Decision 4: New standalone workflow `sign-modules-on-approval.yml`

**Chosen**: New file rather than adding a job to `pr-orchestrator.yml`.

**Rationale**: The signing workflow uses a different trigger (`pull_request_review`) than the
orchestrator (`pull_request` / `push`). Mixing triggers in one file creates confusion about when
each job runs. A standalone file also makes it trivial to audit, disable, or restrict permissions
independently.

### Decision 5: `verify-module-signatures` in pr-orchestrator uses the same policy file

**Chosen**: The job sources `scripts/module-verify-policy.sh`. **Pull requests** use **`VERIFY_MODULES_PR`**
(aligned with pre-commit omit). **Pushes** use **`VERIFY_MODULES_PUSH_ORCHESTRATOR`** (payload checksum +
version bump). This job does **not** pass `--require-signature`; strict signed verification for pushes
to `dev`/`main` lives in **`sign-modules.yml`** after auto-sign.

**Rationale**: PR orchestrator stays a fast compatibility gate; signing and strict verify stay coupled in
the module hardening workflow.

## Risks / Trade-offs

- **Risk: Signed manifests committed by CI bot may confuse reviewers** — the signing commit appears
  after approval and looks like extra changes. Mitigation: commit message is clear
  (`chore(modules): ci sign changed modules [skip ci]`); no source files are touched, only
  `integrity:` blocks in `module-package.yaml` manifests.

- **Risk: `contents: write` permission on signing workflow** — broader than read-only CI jobs.
  Mitigation: the job is scoped to run only when `review.state == 'approved'` and the base branch
  is `dev` or `main`; the job writes only to `module-package.yaml` files and nothing else;
  GITHUB_TOKEN is repository-scoped.

- **Risk: Signing commit not included in merge** — if a reviewer approves, the signing job fires,
  but the author merges an old SHA before the signing commit lands. Mitigation: the
  `verify-module-signatures` job on PR to `main` runs `--require-signature`; if the merge SHA
  precedes the signing commit, CI blocks the merge.

- **Risk: sign-modules.py `--changed-only` base-ref in write-back context** — after the signing
  commit, the PR head changes. If CI re-runs verify with the new head, `--changed-only` must still
  resolve the correct base. Mitigation: use `origin/<base-branch>` as the base ref, not `HEAD~1`.

- **Trade-off: Two-step PR to main (approve → wait for signing commit → merge)** — introduces a
  brief delay (~30 s) between approval and a merge-ready green check. Acceptable given the security
  benefit and the infrequency of main merges.

## Migration Plan

1. Merge this change on `dev` first (no `--require-signature` on dev PRs; no signing needed).
2. The signing workflow activates when the next PR to `main` is approved.
3. The pre-commit hook change is backward-compatible: developers on non-`main` branches
   immediately benefit; `main`-branch hotfixes still require a signed commit (which the CI will
   produce via the approval trigger).
4. No rollback complexity: reverting the three workflow files and the shell script restores the
   prior behaviour exactly.

## Open Questions

- Should the signing commit be GPG-signed by the bot (using a separate signing key) to make the
  provenance chain auditable in `git log --show-signature`? Deferred to a future governance change.
- Should `dev`-branch modules be published to a separate "dev" registry endpoint so internal testers
  can install signed dev builds? Deferred to a future marketplace change.
