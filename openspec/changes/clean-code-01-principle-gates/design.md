# Design: clean-code-01-principle-gates

## Summary

This change is deliberately consumer-side. The review rule implementations, finding schema expansion, and policy-pack payload live in `nold-ai/specfact-cli-modules`. specfact-cli consumes those outputs in three places:

1. human and AI instruction surfaces
2. repo-local `specfact review` and CI gate wiring
3. governance/evidence paths that need to report clean-code results without redefining the traceability chain

## Decisions

### Charter source of truth

- Keep the full 7-principle charter canonical in the code-review skill and related clean-code instruction surfaces.
- Generated IDE instruction files remain aliases and only reference the charter.
- Do not duplicate the full charter into every platform-specific generated instruction file.

### Gate sequencing

- `code-review-zero-findings` must first prove the repo can pass the existing review set.
- `clean-code-02-expanded-review-module` then adds the new clean-code categories and staged KISS metrics.
- Only after those two prerequisites does specfact-cli turn the new categories into repo-level gating requirements.

### Staged KISS thresholds

- Phase A consumes LOC warning/error thresholds at `>80` / `>120`, with nesting and parameter-count checks enabled immediately.
- Phase B (`>40` / `>80`) remains a later cleanup step and is explicitly not part of this initial hardening change.

## Dependency notes

- `policy-02-packs-and-modes` stays authoritative for per-rule enforcement modes.
- `profile-01-config-layering` stays authoritative for tier defaults.
- `governance-01-evidence-output` stays authoritative for the evidence envelope.
- `validation-02-full-chain-engine` may call review as a side-channel, but clean-code results remain outside the core layer graph.
