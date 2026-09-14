# Align core Code Review runtime documentation

## Why

Core's generated command artifacts use an older module fixture and omit portable runtime commands and project configuration/runtime options. Package/root accountability checks do not certify complete command parity.

## What Changes

- Give Docs Review an independent immutable module source lock with commit/tree verification while preserving Requirements approved source identity.
- Regenerate and validate core command artifacts with the exact signed module input and test normalized Code Review command, argument, option and subgroup parity. Both documentation scripts honor the separate source context during canonical hooks.
- Extend the core registration/handoff contract for runtime inspect/prepare and route exact semantics to modules documentation.

## Impact

Affected specs: generated-command-overview, code-review-module. Affected code: Docs Review workflow and focused documentation validation; generated JSON/Markdown/llms artifacts. No core runtime behavior, Requirements authority, module publication gate, or module signature policy changes.

## Source Tracking and Readiness

Core issue #728, parent Feature #356 / Epic #194; documentation, bug, openspec, change-proposal and code-review labels; owner djm81; SpecFact CLI project Todo at readiness. Native blocker/blocked-by lists empty. User-authorized follow-up to modules #473 / PR #474 comment4009357746. Current core base45776bf0ee64e0a9cef07ee5d3c324114d8ac44f. Reviewed signed modules source is commit `2e095f1350fecb7e7eda0bcfba6bad89a6d82c88` / tree `8846ce1b47538ea78d600b7c82bfd2ccd1761ee2`. This documentation input is not public registry installation acceptance. Existing core #725/#726 Requirements scopes remain independent.

## Prospective delivery cycle

This branch re-delivers the reviewed documentation change prospectively from untouched public dev `45776bf0ee64e0a9cef07ee5d3c324114d8ac44f`. Original PR #729 and commit `4181e05aa4827f2957fcc21a41aed38d4077636d` remain intact. Their local TDD and passing execution are historical evidence; this branch makes no retrospective protected-RED claim.

The first phase contains only OpenSpec and tests, with genuine regression selectors selected for a new independently reviewed failing-first plan. Positive, preservation, existing rejection and parity fault-injection tests remain mandatory CI controls. Normal protected workflow must retain authentic RED evidence before any implementation is applied. The final phase applies the reviewed behavior without modifying selected test files or proof support; no Requirements policy, maturity threshold or execution authority changes.
