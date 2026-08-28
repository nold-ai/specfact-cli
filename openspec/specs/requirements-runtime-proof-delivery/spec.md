# requirements-runtime-proof-delivery Specification

## Purpose

TBD - created by archiving change fix-retained-red-proof-provenance. Update Purpose after archive.

## Requirements

### Requirement: Producer-Bound Retained Red Proof

Core SHALL bind every runner-produced red report to the immutable source tree,
pull-request merge base, selected committed test bytes, retained failing JUnit,
and actual proof toolchain before publishing it for later final reconciliation.
Core SHALL fail closed instead of publishing a structurally usable retained proof
when any required binding is unavailable, inconsistent, or malformed.

#### Scenario: Red execution publishes complete immutable bindings

- **GIVEN** a validated Requirements plan executes exact pytest selectors at a committed source
- **AND** reconciliation classifies the retained JUnit result as a passing red-stage decision
- **WHEN** core prepares the red artifact for upload
- **THEN** it SHALL record the source tree and pull-request merge base from Git objects
- **AND** it SHALL record a digest of each selected test blob at the source commit
- **AND** it SHALL record consistent runner, Python, and pytest identities emitted by the proof process
- **AND** the unchanged artifact SHALL pass retained-proof validation on a later eligible descendant.

#### Scenario: Missing or inconsistent producer evidence fails closed

- **GIVEN** a red report or its JUnit lacks a required source, selector, failure, digest, or toolchain binding
- **WHEN** core attempts to prepare retained evidence
- **THEN** it SHALL reject the artifact without synthesizing the missing value from a later run
- **AND** the Requirements workflow SHALL remain non-green after retaining a diagnostic.

#### Scenario: Existing tamper and chronology checks remain enforced

- **GIVEN** a bound red artifact is tracked by the pull request, altered, stale, or not chronologically before implementation
- **WHEN** a later final run validates it
- **THEN** the existing provenance validator SHALL reject it deterministically
- **AND** no compatibility fallback SHALL downgrade the rejection.

#### Scenario: Producer repair bootstraps from exact failing ledger

- **GIVEN** the released producer cannot create the newly required bindings for its own repair branch
- **AND** an unedited repository-member issue authorization binds the issue, pull request, branch, signed red commit, exact failing run/artifact, mapping, plan, immutable ledger prefix, and expiry
- **WHEN** the producer repair reaches final reconciliation
- **THEN** only that named change MAY use the exact approved ledger instead of its structurally incomplete red artifact
- **AND** the authorized red commit SHALL be a strict test-only ancestor of the final source
- **AND** the final run SHALL still execute every mapped selector and produce a complete current-run proof
- **AND** no other change or digest MAY reuse the bootstrap path.
