## Context

The hardening target is a PR pipeline that proves runtime behavior before merge without turning every pull request into a full release rehearsal. The workflow already has mature process checks, but the riskiest gaps are package/runtime validation timing, advisory coverage, and self-review bias.

## Decisions

- Keep `tests` as the single full-suite owner; add targeted jobs for package runtime, SAST, and cross-platform smoke instead of duplicating the full suite.
- Gate the package runtime matrix only for code paths that can affect runtime, packaging, module discovery, command docs, or workflow execution.
- Build a wheel once in the package runtime job and install that wheel in isolated environments for pip/pipx/uvx-style checks.
- Treat Semgrep and Bandit as independent evidence: they run outside `specfact code review` and upload raw artifacts.
- Keep Windows smoke scheduled/manual at first; make macOS PR-blocking for changed runtime/package paths.
- Start mutation testing as scheduled advisory evidence, with explicit critical-module targeting and an uploaded baseline report.

## Risks / Trade-offs

- CI time increases. Mitigation: path-gate package matrix and macOS smoke; keep Windows scheduled until stable.
- Wheel runtime checks may expose module checkout assumptions. Mitigation: use existing paired-branch module checkout logic and emit per-launcher logs.
- Coverage enforcement can block useful work. Mitigation: use governed exception/profile work for temporary waivers, not silent advisory workflow behavior.

## Migration Plan

1. Add spec deltas and workflow policy tests.
2. Capture failing-before evidence for policy/property tests.
3. Implement workflow hardening, threshold enforcement, property tests, and mutation baseline job.
4. Validate with focused pytest, workflow lint/static checks, OpenSpec strict validation, and internal wiki graph rebuild.
