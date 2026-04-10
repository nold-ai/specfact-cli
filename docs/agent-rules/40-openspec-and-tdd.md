---
layout: default
title: Agent OpenSpec and TDD
permalink: /contributing/agent-rules/openspec-and-tdd/
description: OpenSpec selection, change validation, and strict TDD order for behavior changes.
keywords: [agents, openspec, tdd, change-validation, evidence]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - openspec/config.yaml
  - openspec/CHANGE_ORDER.md
  - docs/agent-rules/**
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-openspec-and-tdd
always_load: false
applies_when:
  - implementation
  - openspec-change-selection
priority: 40
blocking: true
user_interaction_required: true
stop_conditions:
  - no valid OpenSpec change
  - change stale or superseded
  - failing-before evidence missing
depends_on:
  - agent-rules-index
  - agent-rules-non-negotiable-checklist
---

# Agent OpenSpec and TDD

## OpenSpec workflow

- Before modifying application code, verify that an active OpenSpec change explicitly covers the requested modification.
- Skip only when the user explicitly says `skip openspec` or `implement without openspec change`.
- The existence of any open change is not sufficient; the change must cover the requested scope.
- If no change exists, clarify whether the work needs a new change, a modified existing change, or a delta.

## Internal wiki and strategic context

When a **sibling internal repository** is available on disk (typical layout: this repository’s parent directory also contains `specfact-cli-internal`, so the internal wiki resolves under `../specfact-cli-internal/wiki/` relative to this repo root), use that wiki as **read-only** input for design decisions. Do not copy wiki content into this public tree.

Before **designing or materially scoping** a new OpenSpec change, read these wiki files when they exist: resolve each wiki-relative path against the sibling checkout so you open an **absolute path** on the host (for example join this repository root with `../specfact-cli-internal/wiki/hot.md` and canonicalize) and read the file directly:

- `wiki/hot.md` for current blocker state
- `wiki/graph.md` to see what the change unblocks or depends on
- The relevant concept page under `wiki/concepts/` (for example `wiki/concepts/clean-code-principles.md`)

If the sibling checkout or a given wiki file is missing, continue without it for **reading** design context; see **When the internal wiki checkout is missing** below for **writing** the wiki mirror.

### Wiki mirror for active OpenSpec changes (`wiki/sources/<change-id>.md`)

Whenever you change an **active** `openspec/changes/<change-id>/` change in a way that would mislead someone who only reads the internal wiki—for example you edit `proposal.md` (scope, **Why**, **What changes**), `design.md`, `tasks.md` story or ordering, or dependency / prerequisite text—you must also update the matching page in the internal wiki:

- **Path (sibling checkout):** `../specfact-cli-internal/wiki/sources/<change-id>.md` (resolve to an absolute path when editing).
- **Update at least:** `depends-on`, `blocks`, `external-deps`, and `status` so they match the change; adjust the short summary if the intent shifted. Align any other mirrored fields that page uses.
- **Then**, with the internal repo as cwd:

```bash
cd ../specfact-cli-internal && python3 scripts/wiki_rebuild_graph.py
```

**Carve-out:** You do **not** need to edit the wiki for every checkbox tick or typo-only edits—only when the **story**, **scope**, or **dependency picture** changes.

### When the internal wiki checkout is missing

If `specfact-cli-internal` is **not** available in the expected sibling layout, **do not** imply the wiki was updated. Instead:

- Add an explicit **merge checklist item** or **follow-up** such as: update `wiki/sources/<change-id>.md` (depends-on / blocks / external-deps / status / summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.

### Internal wiki maintenance (sibling `specfact-cli-internal`)

Automation for the internal wiki lives in the **sibling checkout** (`../specfact-cli-internal/` relative to this repo root), not in this repository. The scripts assume the **process current working directory is the internal repository root**; running them from `specfact-cli` or any other directory breaks path resolution and script logic.

When that checkout exists and you **ship work** (for example after merges to `dev` or `main` that change OpenSpec or GitHub tracking), **change directory into the internal checkout first**, then invoke Python (from this repo’s root, a typical pattern is):

```bash
cd ../specfact-cli-internal && python3 scripts/wiki_openspec_gh_status.py
```

If you changed **many** `docs/agent-rules/` frontmatter blocks or other wiki-linked metadata, also run:

```bash
cd ../specfact-cli-internal && python3 scripts/wiki_rebuild_graph.py
```

If your shell’s cwd is not this public repo root, use the correct relative or absolute path to the internal checkout instead of `../specfact-cli-internal`.

Do not copy script output or wiki bodies into this public tree; commit wiki updates only in the internal repository.

## Change validity

- Never implement from a change id alone.
- Revalidate the selected change against current repository reality, dependency state, and possible superseding work.
- Use `openspec validate <change-id> --strict` and, where appropriate, the workflow validator to capture dependency and interface impact.

## Strict TDD order

1. Update or add spec deltas first.
2. Add or modify tests mapped to spec scenarios.
3. Run tests and capture a failing result before production edits.
4. Only then modify production code.
5. Re-run tests and quality gates until passing.

## Evidence

Record the failing-before and passing-after runs in `openspec/changes/<change-id>/TDD_EVIDENCE.md`. Behavior work is blocked until failing-first evidence exists.

## Archive after merge (mandatory)

- When a change is implemented and merged (or otherwise complete), **finalize it only with the OpenSpec CLI** from the repository root: `openspec archive <change-id>`.
- The CLI merges delta specs into `openspec/specs/` and moves the change to `openspec/changes/archive/<dated-prefix>-<change-id>/`. **Do not** manually `mv` or rename `openspec/changes/<change-id>/` into `archive/`.
- Use `-y` / `--yes` only when automation must skip confirmation prompts; default is interactive confirmation.
- Reserve `openspec archive <change-id> --skip-specs` for rare cases with no spec deltas (for example pure infrastructure or confirmed doc-only closes) with explicit user agreement.
- Avoid `--no-validate` unless the user explicitly accepts that trade-off; default is validated archive.
