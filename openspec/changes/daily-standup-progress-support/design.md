# Design: Daily standup and progress support

## Bridge adapter integration

- **Standup view**: Reads from existing OpenSpec change proposals and/or backlog adapter data (same sources as `specfact sync bridge` and backlog commands). No new adapter contract; reuse existing list/fetch APIs.
- **Post standup comment**: When user opts in, use existing GitHub (and optionally ADO) adapter to add a comment to the linked issue. GitHub: use Issues API `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` with standup body. ADO: use Work Item Comments API if available; otherwise document as future extension.
- **Adapter capability**: Adapters that support "post comment" expose a method (e.g. `post_comment(issue_id, body)`) or equivalent; standup command calls it when adapter supports it and user opts in. Read-only or unsupported adapters return a clear "not supported" so the CLI does not attempt to post.

## Sequence (post standup comment)

```
User → specfact standup --post-standup --standup-text "Yesterday: X. Today: Y. Blockers: Z"
  → CLI resolves change proposal → Source Tracking → issue number + repo
  → CLI gets adapter for repo (e.g. GitHub)
  → If adapter supports post_comment: adapter.post_comment(issue_number, formatted_body)
  → GitHub API: POST .../issues/{n}/comments
  → CLI reports success or failure
```

## Contract enforcement

- New public functions (e.g. standup view builder, comment poster) shall have @icontract and @beartype.
- Adapter interface extension (post_comment) optional with default "not supported" to keep backward compatibility.

## Fallback / offline

- Standup view is read-only from local/cached data; no network required for view-only.
- Post comment requires network and auth; failure (rate limit, auth) is reported; no silent swallow.

## Alignment with existing sync bridge

- Existing `specfact sync bridge --add-progress-comment` and `--track-code-changes` already add progress comments to GitHub issues. Standup comment can reuse or extend that path (e.g. standup format as a variant of progress comment) to avoid duplicate comment-posting logic. Standup/progress is exposed under the backlog command group as `specfact backlog daily` (no top-level standup or scrum command).
