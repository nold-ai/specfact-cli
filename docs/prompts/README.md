# Prompt Validation System

This directory contains documentation and tools for validating slash command prompts to ensure they are correct, aligned with CLI commands, and provide good UX.

## Quick Start

### Run Automated Validation

```bash
# Validate all prompts
hatch run validate-prompts

# Or directly
python tools/validate_prompts.py
```

### Run Tests

```bash
# Run prompt validation tests
hatch test tests/unit/prompts/test_prompt_validation.py -v
```

## What Gets Validated

The automated validator checks:

1. **Structure**: Required sections present (CLI Enforcement, Wait States, Goal, Operating Constraints)
2. **CLI Alignment**: CLI commands match actual CLI, enforcement rules present
3. **Wait States**: Wait state rules and markers present
4. **Dual-Stack Workflow**: Three-phase workflow for applicable commands
5. **Consistency**: Consistent formatting and structure across prompts

## Validation Results

All 8 prompts currently pass validation:

- ✅ `specfact.01-import` (20 checks) - Import from codebase
- ✅ `specfact.02-plan` (15 checks) - Plan management (init, add-feature, add-story, update-idea, update-feature, update-story)
- ✅ `specfact.03-review` (15 checks) - Review plan and promote
- ✅ `specfact.04-sdd` (15 checks) - Create SDD manifest
- ✅ `specfact.05-enforce` (15 checks) - SDD enforcement
- ✅ `specfact.06-sync` (15 checks) - Sync operations
- ✅ `specfact.compare` (15 checks) - Compare plans
- ✅ `specfact.validate` (15 checks) - Validation suite

## Manual Review

See [PROMPT_VALIDATION_CHECKLIST.md](./PROMPT_VALIDATION_CHECKLIST.md) for:

- Detailed manual review checklist
- Testing scenarios with Copilot
- Common issues and fixes
- Continuous improvement process

## Files

- **`tools/validate_prompts.py`**: Automated validation tool
- **`tests/unit/prompts/test_prompt_validation.py`**: Unit tests for validator
- **`PROMPT_VALIDATION_CHECKLIST.md`**: Manual review checklist
- **`resources/prompts/`**: Prompt template files

## Integration

The validation tool is integrated into the development workflow:

- **Pre-commit**: Run `hatch run validate-prompts` before committing prompt changes
- **CI/CD**: Add validation step to CI pipeline
- **Development**: Run validation after updating any prompt

## Next Steps

1. **Test with Copilot**: Use the manual checklist to test each prompt in real scenarios
2. **Document Issues**: Document any issues found during testing
3. **Improve Prompts**: Update prompts based on testing feedback
4. **Expand Validation**: Add more checks as patterns emerge

---

**Last Updated**: 2025-12-02 (v0.11.4 - Active Plan Fallback, SDD Hash Stability)  
**Version**: 1.1
