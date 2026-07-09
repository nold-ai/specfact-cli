---
layout: default
title: Validation Evidence Contracts
permalink: /reference/validation-evidence-contracts/
description: Core contracts for deterministic validation evidence and requirements-first traceability.
keywords: [validation, evidence, traceability, requirements]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/evidence.py
  - src/specfact_cli/traceability.py
last_reviewed: 2026-07-09
exempt: false
exempt_reason: ""
---

# Validation Evidence Contracts

Core exposes typed contracts only. Module runtimes own command flags, evidence
file persistence, and rendering.

- `EvidenceEnvelope` derives `PASS`, `PASS_WITH_ADVISORY`, or `FAIL` and its CI
  exit code from typed result summaries.
- `ArtifactRecord`, `ArtifactLink`, and `build_artifact_index(...)` provide a
  generic, deterministic, JSON-serializable index for normalized inputs from
  requirements, architecture, specifications, code, tests, contracts, and other
  adapters.
- The index classifies unlinked artifacts, dangling links, duplicate identities,
  and self-referential contradictions; rebuild results report changed and
  removed identities.
- `requirements_to_artifact_records(...)` is the first integrated adapter.
  Architecture and other inputs are optional; their absence does not create a
  finding.

Use these contracts as inputs to validation and governance modules; they do not
introduce a `specfact trace` command, index-file persistence, or requirements
authoring workflow.
