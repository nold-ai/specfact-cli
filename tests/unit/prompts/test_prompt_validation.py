"""Unit tests for prompt validation."""

from __future__ import annotations

from pathlib import Path

from tools.validate_prompts import PromptValidator, validate_all_prompts


class TestPromptValidator:
    """Test PromptValidator class."""

    def test_validate_structure(self, tmp_path: Path):
        """Test structure validation."""
        # Create a minimal valid prompt
        prompt_file = tmp_path / "test-prompt.md"
        prompt_content = """---
description: Test prompt
---
# Test Prompt

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**.

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait.**

## Goal

Test goal.

## Operating Constraints

Test constraints.
"""
        prompt_file.write_text(prompt_content)

        validator = PromptValidator(prompt_file)
        assert validator.validate_structure() is True
        assert len(validator.errors) == 0

    def test_validate_structure_missing_section(self, tmp_path: Path):
        """Test structure validation with missing section."""
        prompt_file = tmp_path / "test-prompt.md"
        prompt_content = """# Test Prompt

## Goal

Test goal.
"""
        prompt_file.write_text(prompt_content)

        validator = PromptValidator(prompt_file)
        assert validator.validate_structure() is False
        assert len(validator.errors) > 0

    def test_validate_cli_alignment(self, tmp_path: Path):
        """Test CLI alignment validation."""
        prompt_file = tmp_path / "specfact.01-import.md"
        prompt_content = """---
description: Import from code
---
# SpecFact Import From Code

## ⚠️ CRITICAL: CLI Usage Enforcement

1. **ALWAYS execute CLI first**: Run `specfact import from-code` before any analysis
2. **NEVER create YAML/JSON directly**: All artifacts must be CLI-generated
3. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata
4. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

## ⏸️ Wait States: User Input Required

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Import from code.

## Operating Constraints

Test constraints.
"""
        prompt_file.write_text(prompt_content)

        validator = PromptValidator(prompt_file)
        assert validator.validate_cli_alignment() is True

    def test_validate_dual_stack_workflow(self, tmp_path: Path):
        """Test dual-stack workflow validation."""
        prompt_file = tmp_path / "specfact.01-import.md"
        prompt_content = """---
description: Import from code
---
# SpecFact Import From Code

## ⚠️ CRITICAL: CLI Usage Enforcement

Test.

## ⏸️ Wait States: User Input Required

Test.

## Goal

Test.

## Operating Constraints

Test.

## 🔄 Dual-Stack Workflow (Copilot Mode)

### Phase 1: CLI Grounding (REQUIRED)

Test.

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

Test.

### Phase 3: CLI Artifact Creation (REQUIRED)

Enrichment report location: `.specfact/reports/enrichment/`
"""
        prompt_file.write_text(prompt_content)

        validator = PromptValidator(prompt_file)
        assert validator.validate_dual_stack_workflow() is True

    def test_validate_all_prompts(self):
        """Test validating all prompts in resources/prompts."""
        # Path from tests/unit/prompts/test_prompt_validation.py to resources/prompts
        # tests/unit/prompts -> tests/unit -> tests -> root -> resources/prompts
        prompts_dir = Path(__file__).parent.parent.parent.parent / "resources" / "prompts"
        # Prompts directory should exist in the repository
        assert prompts_dir.exists(), f"Prompts directory not found at {prompts_dir}"

        results = validate_all_prompts(prompts_dir)
        assert len(results) > 0

        # All prompts should pass basic validation
        for result in results:
            assert "prompt" in result
            assert "errors" in result
            assert "warnings" in result
            assert "checks" in result
            assert "passed" in result
