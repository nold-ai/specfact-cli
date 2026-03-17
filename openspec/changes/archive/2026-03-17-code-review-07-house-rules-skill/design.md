# Design: house_rules Skill and Auto-Updater

## SKILL.md Structure (ai-integration-01 Standard)

```markdown
---
name: specfact-code-review
description: House rules for AI coding sessions derived from review findings
allowed-tools: []
---
# House Rules — AI Coding Context (v1)

Updated: 2026-03-10 | Module: nold-ai/specfact-code-review

## DO
- Keep functions under 120 LOC and cyclomatic complexity <= 12
- Add @require/@ensure (icontract) + @beartype to all new public APIs
- Run hatch run contract-test-contracts before any commit
- Guard all chained attribute access: a.b.c needs null-check or early return
- Return typed values from all public methods
- Write the test file BEFORE the feature file (TDD-first)
- Use get_logger(__name__) from common.logger_setup, never print()

## DON'T
- Don't mix read + write in the same method — split responsibilities
- Don't use bare except: or except Exception: pass
- Don't add # noqa / # type: ignore without inline justification
- Don't call repository.* and http_client.* in the same function
- Don't import at module level if it triggers network calls
- Don't hardcode secrets — use env vars via pydantic.BaseSettings
- Don't create functions > 120 lines

## TOP VIOLATIONS (auto-updated by specfact code review rules update)
<!-- auto-managed: do not edit manually -->
```

## Updater Algorithm

```python
def update_house_rules(skill_path: Path, runs: list[RunRecord]) -> None:
    content = skill_path.read_text()

    # Count violation frequency per rule in last 20 runs
    rule_counts = Counter()
    for run in runs[-20:]:
        for finding in run.findings:
            rule_counts[finding.rule] += 1

    # Rules to surface: >= 3 hits
    to_surface = [rule for rule, count in rule_counts.items() if count >= 3]

    # Parse existing TOP VIOLATIONS section
    # Replace content between auto-managed markers
    # Enforce 35 line cap by pruning oldest/lowest-frequency
    # Increment version, update timestamp
    # Write back

    # Mirror to .cursor/rules/house_rules.mdc
    mirror_path = Path(".cursor/rules/house_rules.mdc")
    if mirror_path.parent.exists():
        mirror_path.write_text(content)
```

## File Locations

In `specfact-cli` repo:
- `skills/specfact-code-review/SKILL.md` — the installable skill file
- `.cursor/rules/house_rules.mdc` — Cursor mirror (auto-maintained)

In `specfact-code-review` module (`specfact-cli-modules`):
- `rules/updater.py` — update algorithm
- `rules/commands.py` — show/update/init CLI subcommands

## Line Budget Management

With frontmatter (4 lines) + title (2) + DO section (9) + DON'T section (9) = 24 lines base.
Remaining budget for TOP VIOLATIONS: 35 - 24 = 11 lines.
At ~2 lines per violation entry, that's ~5 violations max in the TOP VIOLATIONS section.
Updater prunes to stay within budget, removing lowest-frequency entries first.
