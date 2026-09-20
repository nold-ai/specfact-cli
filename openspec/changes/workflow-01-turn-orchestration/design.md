## Ownership and integration

Use the existing module registry to expose the paired signed workflow package. Do not register a new built-in workflow engine beside init/module/upgrade. Repository configuration supplies its own gate commands and applicability; portable runtime does not hardcode Hatch, internal wiki paths or these two repositories. The core slice also maintains repository-local skill projection; module-owned reusable skill bodies are referenced, not hand-copied into a competing source of truth.

Canonical repository wrappers use `.agents/skills/specfact-{pre-validate,implement,verify,fix,autofix}` and the existing OpenSpec workflow skill. Supported projections follow observed harness discovery conventions with an explicit manifest; do not create duplicate active Codex registrations. A deterministic renderer owns generated files only, rejects unmanaged collisions and escaping/symlink destinations, and preserves unrelated custom files. Known AGENTS/CLAUDE differences are explicit transformations. Check mode writes nothing and runs for canonical, destination, renderer or manifest changes, including deletions, both locally and in CI. Fix parent-directory ignore rules so canonical files are genuinely tracked. This repository mechanism is distinct from generic customer installation/export #251.

## Check-only adapters

The current quality shell script is not a read-only verifier: it can format, generate command docs and stage files. Factor or call check-only commands for the workflow adapter. Declare gate scope and relevant input/config identities; use explicit index/worktree/immutable-range selection rather than inferring all modes from staged filenames. Verification may write ignored result/cache files, but must preserve source and index byte contents and must not regenerate tracked outputs. Explicit preparation/fix commands perform requested mutations and invalidate prior results.

Reuse test/contract/security/review outputs from the same candidate, environment and scope only when their identity and required producer completeness match. No duplicate evidence-only suite. Required missing tools, malformed output or unavailable producer versions remain non-passing with remediation diagnostics. Never turn a green review score into a pytest/security PASS. A required warning under effective contributor governance remains unresolved until handled by its owning policy; the workflow cannot invent a severity exception. C15 owns future calibrated policy.

Pre-validation treats changed referenced paths or upstream observations as drift signals requiring disposition, not proof that intent is invalid. ADDED capabilities may legitimately be absent; completed blockers can improve readiness. Bind the reviewed proposal/spec/task inputs explicitly rather than using the folder's last commit as approval. Existing backlog readiness does not cover every parent/label/project/concurrency check, so the repository governance adapter checks the uncovered native fields. Optional internal-wiki presence is repository configuration; absence produces a follow-up, not a product-wide dependency.

## Evidence and policy boundaries

Standalone verify and ordinary CI start from current inputs even in a fresh checkout without `.specfact/turn`. Workflow receipts support local resumption only. Core #740 owns authenticated current-run CI enforcement; R09 modules remains a pure reconciler supplied with outputs, without Git, test execution or network I/O. The workflow executes or references checks separately and preserves Requirements, review and security claims. Optional assurance selects the existing seal/conformance consumer; this adoption does not implement a substitute seal or upgrade local authority.

## Rollout and verification

Projection can be reviewed and merged independently. Then select an immutable compatible signed workflow release, check actual installed command discovery and pilot read-only verification on both repositories. Open bounded implementation PRs as each slice becomes reviewable, integrate before trusted pilot/policy activation, and retain existing required checks. Enable local repair after the scope and identity fixtures pass; opt-in PR automation is last. Do not merge or publish from the agent loop automatically.

Pilot cases: fresh session, partially staged file, unstaged/untracked changes, immutable PR range, missing tool, independent failed gate, generated-skill drift and explicitly selected assurance. Use existing CI timings and result artifacts to inspect duplicate work and failure detection; do not add a telemetry framework or promise measured savings. A wrong scope, silent failure acceptance or unexpected mutation disables adoption and restores its prior configuration/module pin.

## Research basis

Reviewed 2026-09-20: [Anthropic's long-running harness guidance](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) supports explicit progress/handoff and acceptance checks; [pstack babysit](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/babysit.md) separates CI and review completion. These inform the design, not a claim that framework prompts enforce repository policy. Local inspection of the mutating quality script and schema 1.6 report parser motivates check-only adapters and independent producer reports. No framework dependency is added.

## Signed Requirements compatibility gate

Before selecting or adopting workflow #483 for current-run Requirements integration, validate the exact immutable signed Requirements #481 publication and its schema-v3 `current_execution` contract against the actual core and workflow versions. Verify archive/manifest/payload signatures and identities, then exercise the exact installed pair with existing representative current-result fixtures. An absent, incompatible, unsigned or v2-only producer leaves runtime integration/adoption not ready; do not substitute a passing receipt or silently downgrade the contract. Repository skill projection remains independently deliverable, and core #740 retains policy cutover ownership.
