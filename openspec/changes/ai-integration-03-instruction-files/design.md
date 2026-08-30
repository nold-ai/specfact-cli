## Context

The original change mixed platform setup with validation/remediation workflow content. The new boundary makes instruction files lightweight routing surfaces: the signed module owns workflow semantics, #251 owns verified installation/export, and #253 emits only managed references and gates.

Research reviewed on 2026-08-25:

- OpenSpec uses one workflow intent with different generated command forms and supports updating planning artifacts before apply: <https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md>
- Spec Kit puts clarify/checklist/analyze before implement and documents harness-specific command forms: <https://github.github.com/spec-kit/reference/agentic-sdd.html>
- Spec Kit's base CLI does not own AGENTS.md/CLAUDE.md; its opt-in `agent-context` extension owns the managed section: <https://github.com/github/spec-kit/blob/main/AGENTS.md>

## Goals / Non-Goals

**Goals:**

- Emit compact pre-implementation gate references into supported instruction surfaces.
- Preserve one canonical workflow identity and resolve each harness-native invocation form.
- Use owned markers and install inventories for idempotent regeneration and safe removal.
- Respect existing OpenSpec, Spec Kit, and repository governance instead of replacing it.

**Non-Goals:**

- Duplicate the preflight phases or validator rules in generated text.
- Install the skill or package external harness adapters.
- Modify user-authored instruction content outside managed sections.

## Decisions

### 1. Minimal gate contract

Every generated preflight reference conveys five rules:

1. select and validate the intended change before implementation;
2. invoke the installed canonical preflight workflow in the harness-native form;
3. require a current explicitly approved seal for the captured inputs;
4. stop on blocked, unknown, stale, ambiguous, or concurrent-work results;
5. return material refinements to the owning artifact and rerun before implementation.

Detailed phases, CLI flags, evidence interpretation, and refinement dialogue remain in the module-owned skill.

### 2. Managed sections, not full-file ownership

Generated instructions use stable start/end markers and an inventory containing target path, generator version, workflow identity, and content digest. Generation is idempotent and updates only the owned section. Missing or malformed markers stop with a diagnostic instead of rewriting the file.

### 3. OpenSpec ordering reference

For OpenSpec projects, the generated section places `specfact-preflight` after proposal/spec/design/tasks are ready and strict validation succeeds, and before `/opsx:apply`, `/openspec:apply`, or equivalent implementation. It does not modify OpenSpec's own generated command files.

### 4. Spec Kit extension compatibility

For Spec Kit, generated content integrates through the enabled `agent-context` extension or another explicitly owned project section. The base Specify CLI is not assumed to manage AGENTS.md. The reference places preflight after the relevant clarify/checklist/analyze loop and before `/speckit.implement` or its harness-native equivalent.

### 5. Harness invocation comes from installed metadata

The generator reads #251's verified skill installation/descriptor data and emits the target's supported form, such as slash, dollar-prefixed, or instruction-driven invocation. It never guesses syntax from the harness name alone.

### 6. Adapter packaging remains downstream

Issue #253 may know instruction target formats already supported by core, but it does not create a Codex plugin, ECC companion, or hatch3r pack. Preflight-04 consumes this managed-section contract.

## Risks / Trade-offs

- **Large always-loaded context:** Keep the gate compact and load skill details only on invocation.
- **Marker corruption:** Fail closed and provide a manual recovery diff.
- **Upstream workflow churn:** Version target mappings and test against selected OpenSpec/Spec Kit fixtures.
- **Unsupported invocation:** Require installed descriptor metadata rather than guessed aliases.

## Migration and Rollback

Existing generated validation prose is replaced only within explicitly owned sections after preview. Rollback restores the previous managed section or removes it using the inventory; user-authored surrounding content is preserved.

## Open Questions Deferred to Implementation

- Exact marker names shared across AGENTS.md and harness-specific files.
- Which existing instruction targets are in the first supported core matrix.
- Whether a missing Spec Kit `agent-context` extension should produce setup guidance or a hard stop under strict policy.
