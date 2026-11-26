## Why

A protected promotion can point at a reviewed release tree whose development history contains commits that the main signature policy rejects. A new, signed topic can preserve the release tree while carrying verifiable source Requirements evidence.

## What Changes

- Let a signed one-commit topic use evidence from a named, independently verified source pull request against the current protected development tip.
- Require the release topic and source pull request to have identical complete Git trees.
- Run provenance verification from the protected main revision and preserve the existing full promotion Code Review.

The dependency backport carries #799's direct admission for the official
pycparser 3.12 wheel. Only SHA-256
`a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e`
is accepted in the frozen graph, which excludes the source distribution.
The historical expiring record remains a test fixture. The trust checker
still rejects that record after its expiry and blocks the 3.0 release
family across all three frozen dependency graphs.
