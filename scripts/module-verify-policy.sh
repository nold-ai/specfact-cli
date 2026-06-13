#!/usr/bin/env bash
# Canonical flag bundles for scripts/verify-modules-signature.py.
# Keep consumers in sync:
#   - scripts/run_verify_modules_policy.sh (hatch aliases strict|pr|push-orchestrator)
#   - scripts/pre-commit-verify-modules.sh (branch-aware require vs omit)
#   - .github/workflows/pr-orchestrator.yml (verify-module-signatures job)
#   - .github/workflows/sign-modules.yml (verify job: push strict vs PR/dispatch relaxed)
#
# shellcheck disable=SC2034
VERIFY_MODULES_STRICT=(--require-signature --enforce-version-bump --payload-from-filesystem)
VERIFY_MODULES_PR=(--enforce-version-bump --skip-checksum-verification)
# Dev push verification in PR orchestrator: checksum + version, signatures handled by sign-modules.
# Main PRs and main pushes should use VERIFY_MODULES_STRICT at the release trust boundary.
VERIFY_MODULES_PUSH_ORCHESTRATOR=(--enforce-version-bump --payload-from-filesystem)
