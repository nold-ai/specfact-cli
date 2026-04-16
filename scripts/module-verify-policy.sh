#!/usr/bin/env bash
# Canonical flag bundles for scripts/verify-modules-signature.py.
# Keep consumers in sync:
#   - scripts/pre-commit-verify-modules.sh (branch-aware require vs omit)
#   - .github/workflows/pr-orchestrator.yml (verify-module-signatures job)
#   - .github/workflows/sign-modules.yml (verify job: push strict vs PR/dispatch relaxed)
#
# shellcheck disable=SC2034
VERIFY_MODULES_STRICT=(--require-signature --enforce-version-bump --payload-from-filesystem)
VERIFY_MODULES_PR=(--enforce-version-bump --skip-checksum-verification)
# Post-merge / push verification in PR orchestrator: checksum + version, signatures handled by sign-modules.
VERIFY_MODULES_PUSH_ORCHESTRATOR=(--enforce-version-bump --payload-from-filesystem)
