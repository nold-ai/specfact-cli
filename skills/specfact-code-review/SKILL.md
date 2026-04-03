---
name: specfact-code-review
description: House rules for AI coding sessions derived from review findings
allowed-tools: []
---

# House Rules - AI Coding Context (v1)

Updated: 2026-03-16 | Module: nold-ai/specfact-code-review

## DO
- Ask whether tests should be included before repo-wide review; default to excluding tests unless test changes are the target
- Keep functions under 120 LOC and cyclomatic complexity <= 12
- Add @require/@ensure (icontract) + @beartype to all new public APIs
- Run hatch run contract-test-contracts before any commit
- Guard all chained attribute access: a.b.c needs null-check or early return
- Return typed values from all public methods
- Write the test file BEFORE the feature file (TDD-first)
- Use get_logger(__name__) from common.logger_setup, never print()

## DON'T
- Don't enable known noisy findings unless you explicitly want strict/full review output
- Don't mix read + write in the same method; split responsibilities
- Don't use bare except: or except Exception: pass
- Don't add # noqa / # type: ignore without inline justification
- Don't call repository.* and http_client.* in the same function
- Don't import at module level if it triggers network calls
- Don't hardcode secrets; use env vars via pydantic.BaseSettings
- Don't create functions > 120 lines

## TOP VIOLATIONS (auto-updated by specfact code review rules update)
<!-- auto-managed: do not edit manually -->
