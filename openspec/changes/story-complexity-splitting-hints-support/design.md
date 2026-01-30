# Design: Story complexity and splitting hints support

## Complexity score and needs_splitting

- **Complexity score**: Function of story_points and business_value (e.g. weighted combination or simple threshold on story_points). Configurable threshold (default 13) for "needs splitting"; stories above threshold are flagged.
- **needs_splitting(item, threshold)**: Predicate: True when item.story_points > threshold (or when complexity score exceeds threshold if score is used). Handle missing story_points (e.g. treat as 0 or skip). New public APIs shall have @icontract and @beartype.
- **Configuration**: Threshold may be read from project config (e.g. `.specfact/` or refinement config); default 13 if not set.

## Splitting suggestion

- **Input**: BacklogItem (story_points, business_value, acceptance_criteria); optional AI hint for split boundaries.
- **Output**: Rationale (text) + recommended split points (e.g. list of boundaries derived from acceptance_criteria or heuristic). Provider-agnostic; use BacklogItem fields; optional AI for finer boundaries.
- **Integration**: When refinement completes for an item, if needs_splitting(item, threshold), append "Story splitting suggestion" block to refinement result; include in CLI output and in export-to-tmp format.

## Sequence (refine with splitting suggestion)

```
User → specfact backlog refine [args]
  → Refinement runs (existing flow)
  → For each refined item: compute complexity / needs_splitting(threshold)
  → If needs_splitting: generate splitting suggestion (rationale + split points)
  → Append splitting suggestion to item output and export-to-tmp
  → Emit refinement output (CLI and/or export)
```

## Contract enforcement

- Complexity score and needs_splitting shall have @icontract and @beartype where they are public APIs.
- Splitting suggestion generator: same; handle missing fields without crash.

## Fallback / offline

- No network required for complexity or threshold; optional AI hint for split boundaries may require network if used; design for offline-first (heuristic split points from acceptance_criteria when AI unavailable).
