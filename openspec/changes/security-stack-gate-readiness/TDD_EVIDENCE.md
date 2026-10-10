# Gate readiness evidence

## Authored failures — 2026-10-11 Europe/Berlin

Specs precede tests; production files remain unchanged against dev
553b46f01c6581c96dc92133b6e77404c8df7cd9. The two selected regressions fail:

- Native stack resolution: the missing adapter prevents resolving an authentic
  root boundary; the parent assertion records a real failure.
- Direct smoke isolation: querying the actual launcher reports the running
  pytest environment prefix, outside the smoke workspace.

Command: `.venv/bin/python -m pytest -q -o addopts=''` with the two mapped
selectors. Result: **2 failed in 0.67 seconds**. Raw log retained at
`/private/tmp/specfact-security-stack-20261011/prerequisite-red.log`.
The child probes never mutate a shared installation. Their test bytes and
fixture are to remain frozen through implementation and final reconciliation.

Strict OpenSpec validation passes. The new-test self-review has zero findings.
The first planned mapping diagnostic identified the released provider's
requirement-slug scenario identity constraint. Correct the mapping metadata
before authored publication; this does not change test behavior or production.
No member authority is inferred from the implementation-agent acceptance record.
