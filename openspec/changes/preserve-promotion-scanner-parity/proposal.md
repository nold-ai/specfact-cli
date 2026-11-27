## Why

The 0.55.19 release source reconciles the reviewed scanner fixes already on
`main` with the current development release. A fresh source PR needs evidence
that the packaged CLI still carries those fixes.

## What Changes

- Preserve the reviewed scanner, OpenAPI, and isolated runtime fixes from #803.
- Retain the protected development Requirements workflow and frozen dependencies.
- Exercise the public async scanner command on the exact promotion source.

Refs #771 and #803.
