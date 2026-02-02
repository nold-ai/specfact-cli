# Change: Story complexity and splitting hints support

## Why

The backlog-refinement spec (openspec/specs/backlog-refinement/spec.md) includes "Story Complexity Analysis" and related scenarios (complexity score, multi-sprint detection, splitting suggestion in refinement output), but this behavior is not implemented. Teams need complexity scores considering story points and business value, flagging of stories > 13 points for potential splitting, suggestions to split into multiple stories under the same feature with rationale, and splitting suggestion included in refinement output when a story is complex. Without this, refinement sessions do not surface size/scope risks and teams may commit to oversized stories.

## What Changes

- **NEW**: Implement complexity calculation (story_points, business_value) and a configurable threshold (e.g. 13 points) for "needs splitting" flag.
- **NEW**: Add splitting detection that suggests split points and rationale (e.g. by acceptance criteria or logical boundaries).
- **EXTEND**: Integrate into **backlog refine** flow (`specfact backlog refine`): when refinement completes for a complex story, include a "Story splitting suggestion" block in the output (and in export-to-tmp format) with recommended split points and rationale. All agile/backlog features stay under the backlog command group; no top-level scrum/refine command.
- **EXTEND**: Documentation (backlog-refinement guide, reference) for complexity and splitting hints.
- **EXTEND** (plan E3): Splitting suggestions SHALL consider dependency edges (minimize cross-team coupling) and "blast radius" signals (modules touched, component tags when available). Provide patch output (patch-mode-preview-apply): "split proposal" as suggested child stories with titles + AC + links. **Acceptance**: Splitting recommendation includes "dependency impact" section.

## Capabilities

- **story-complexity**: Complexity score (story_points, business_value), needs_splitting predicate (configurable threshold), splitting suggestion (rationale + split points), integration into refinement output/export; dependency-aware splitting (edges, blast radius) and patch output for split proposal when dependency analysis and patch mode are available.

## Impact

- **Affected specs**: New `openspec/changes/story-complexity-splitting-hints-support/specs/story-complexity/spec.md` (Given/When/Then for complexity score, needs splitting, splitting suggestion in refinement output); references main `openspec/specs/backlog-refinement/spec.md` Story Complexity Analysis.
- **Affected code**: `src/specfact_cli/commands/backlog_commands.py` (integrate complexity/splitting into refine); `src/specfact_cli/` (new or existing module for complexity score, splitting suggestion).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/backlog-refinement.md for complexity and splitting hints.
- **Integration points**: Existing `specfact backlog refine`; BacklogItem (story_points, business_value, acceptance_criteria); optional AI hint for split boundaries; provider-agnostic.
- **Backward compatibility**: Additive only; refinement output gains optional splitting suggestion section for complex stories; threshold configurable.

## Source Tracking

- **GitHub Issue**: #171
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/171>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
