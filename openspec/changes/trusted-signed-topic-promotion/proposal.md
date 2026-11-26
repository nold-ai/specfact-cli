## Why

A protected promotion can point at a reviewed release tree whose development history contains commits that the main signature policy rejects. A new, signed topic can preserve the release tree while carrying verifiable source Requirements evidence.

## What Changes

- Let a signed one-commit topic use evidence from a named, independently verified source pull request against the current protected development tip.
- Require the release topic and source pull request to have identical complete Git trees.
- Run provenance verification from the protected main revision and preserve the existing full promotion Code Review.
