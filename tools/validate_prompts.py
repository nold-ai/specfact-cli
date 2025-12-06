"""Prompt validation tool for slash command prompts.

This tool validates that prompt templates are:
1. Structurally correct (required sections present)
2. Aligned with CLI commands (commands match actual CLI)
3. Aligned with flow logic (dual-stack pattern, wait states)
4. Consistent across all prompts
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


console = Console()

# Required sections for all prompts (matching actual prompt structure)
REQUIRED_SECTIONS = [
    ("User Input", "## User Input"),
    ("Purpose", "## Purpose"),
    ("Parameters", "## Parameters"),
    ("Workflow", "## Workflow"),
    ("CLI Enforcement", "## CLI Enforcement"),
    ("Expected Output", "## Expected Output"),
    ("Common Patterns", "## Common Patterns"),
    ("Context", "## Context"),
]

# CLI commands that should be referenced (new slash command names)
CLI_COMMANDS = {
    "specfact.01-import": "specfact import from-code",
    "specfact.02-plan": "specfact plan <operation>",  # init, add-feature, add-story, update-idea, update-feature, update-story
    "specfact.03-review": "specfact plan review",  # Also handles promote
    "specfact.04-sdd": "specfact plan harden",
    "specfact.05-enforce": "specfact enforce sdd",
    "specfact.06-sync": "specfact sync bridge",
    "specfact.07-contracts": "specfact analyze contracts",  # Also uses generate contracts-prompt and contracts-apply
    "specfact.compare": "specfact plan compare",
    "specfact.validate": "specfact repro",
}

# Required CLI enforcement rules (checking for key phrases, flexible matching)
CLI_ENFORCEMENT_RULES = [
    ("execute CLI", ["execute CLI", "Execute CLI", "ALWAYS execute CLI", "use SpecFact CLI"]),
    ("CLI commands", ["CLI commands", "CLI command", "specfact", "Use SpecFact CLI"]),
    ("never modify", ["never modify", "Never modify", "NEVER modify", "do not modify", "Do not modify"]),
    ("CLI output", ["CLI output", "Use CLI output", "CLI output as grounding"]),
]

# Required wait state rules (optional - only for interactive workflows)
# These are checked as warnings, not errors, since not all prompts need them
WAIT_STATE_RULES = [
    "consider the user input",
    "WAIT FOR USER RESPONSE",
]

# Commands that should have dual-stack workflow
DUAL_STACK_COMMANDS = ["specfact.01-import", "specfact-import-from-code"]  # New and legacy names


class PromptValidator:
    """Validates prompt templates."""

    def __init__(self, prompt_path: Path) -> None:
        """Initialize validator with prompt path."""
        self.prompt_path = prompt_path
        self.prompt_name = prompt_path.stem
        self.content = prompt_path.read_text(encoding="utf-8")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: list[dict[str, Any]] = []

    def validate_structure(self) -> bool:
        """Validate prompt structure (required sections)."""
        passed = True

        for section_name, section_marker in REQUIRED_SECTIONS:
            if section_marker not in self.content:
                self.errors.append(f"Missing required section: {section_name}")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "Structure",
                        "section": section_name,
                        "status": "✓",
                        "message": "Section present",
                    }
                )

        return passed

    def validate_cli_alignment(self) -> bool:
        """Validate CLI command alignment."""
        passed = True

        # Check if CLI command is mentioned
        expected_command = CLI_COMMANDS.get(self.prompt_name)
        if expected_command:
            if expected_command not in self.content:
                self.errors.append(f"CLI command '{expected_command}' not found in prompt")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "CLI Alignment",
                        "section": "CLI Command",
                        "status": "✓",
                        "message": f"Command '{expected_command}' found",
                    }
                )

        # Check CLI enforcement rules (flexible matching)
        for rule_name, rule_variants in CLI_ENFORCEMENT_RULES:
            found = any(variant in self.content for variant in rule_variants)
            if not found:
                self.warnings.append(f"CLI enforcement rule not found: '{rule_name}' (checked variants: {', '.join(rule_variants[:2])}...)")
            else:
                self.checks.append(
                    {
                        "check": "CLI Alignment",
                        "section": "Enforcement Rule",
                        "status": "✓",
                        "message": f"Rule '{rule_name}' found",
                    }
                )

        return passed

    def validate_wait_states(self) -> bool:
        """Validate wait state rules (optional - only warnings)."""
        passed = True

        # Check for User Input section with $ARGUMENTS placeholder
        if "## User Input" not in self.content:
            self.errors.append("Missing '## User Input' section")
            passed = False
        elif "$ARGUMENTS" not in self.content:
            self.errors.append("Missing $ARGUMENTS placeholder in User Input section")
            passed = False
        else:
            self.checks.append(
                {
                    "check": "Wait States",
                    "section": "User Input",
                    "status": "✓",
                    "message": "User Input section with $ARGUMENTS found",
                }
            )

        # Check for user input instruction
        if "consider the user input" not in self.content.lower():
            self.warnings.append("User input instruction not found (should include 'You **MUST** consider the user input before proceeding')")
        else:
            self.checks.append(
                {
                    "check": "Wait States",
                    "section": "User Input Instruction",
                    "status": "✓",
                    "message": "User input instruction found",
                }
            )

        # Check for explicit wait state markers (optional - only for interactive workflows)
        wait_markers = ["WAIT FOR USER RESPONSE", "DO NOT CONTINUE"]
        for marker in wait_markers:
            if marker in self.content:
                self.checks.append(
                    {
                        "check": "Wait States",
                        "section": "Wait Marker",
                        "status": "✓",
                        "message": f"Marker '{marker}' found",
                    }
                )

        return passed

    def validate_dual_stack_workflow(self) -> bool:
        """Validate dual-stack enrichment workflow (if applicable)."""
        if self.prompt_name not in DUAL_STACK_COMMANDS:
            return True  # Not required for this command

        passed = True

        # Check for dual-stack workflow section (flexible matching)
        dual_stack_markers = [
            ("Dual-Stack Workflow", ["Dual-Stack Workflow", "Dual-stack workflow", "dual-stack workflow", "## Workflow"]),
            ("Phase 1: CLI Grounding", ["Phase 1: CLI Grounding", "Phase 1", "CLI Grounding", "Execute CLI", "1. **Execute CLI"]),
            ("Phase 2: LLM Enrichment", ["Phase 2: LLM Enrichment", "Phase 2", "LLM Enrichment", "2. **LLM Enrichment", "enrichment"]),
            ("Phase 3: CLI Artifact Creation", ["Phase 3: CLI Artifact Creation", "Phase 3", "CLI Artifact Creation", "3. **Present"]),
        ]

        for marker_name, marker_variants in dual_stack_markers:
            found = any(variant in self.content for variant in marker_variants)
            if not found:
                self.errors.append(f"Missing dual-stack workflow marker: '{marker_name}' (checked variants: {', '.join(marker_variants[:2])}...)")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "Dual-Stack",
                        "section": "Workflow Phase",
                        "status": "✓",
                        "message": f"Phase '{marker_name}' found",
                    }
                )

        # Check for enrichment report location
        if ".specfact/reports/enrichment" not in self.content:
            self.warnings.append("Enrichment report location not specified")
        else:
            self.checks.append(
                {
                    "check": "Dual-Stack",
                    "section": "Enrichment Location",
                    "status": "✓",
                    "message": "Enrichment report location specified",
                }
            )

        return passed

    def validate_consistency(self) -> bool:
        """Validate consistency with other prompts."""
        passed = True

        # Check for consistent formatting
        if "$ARGUMENTS" not in self.content:
            self.errors.append("Missing $ARGUMENTS placeholder in User Input section")
            passed = False
        else:
            self.checks.append(
                {
                    "check": "Consistency",
                    "section": "Placeholders",
                    "status": "✓",
                    "message": "$ARGUMENTS placeholder found",
                }
            )

        # Check for {ARGS} placeholder in Context section
        if "## Context" in self.content:
            if "{ARGS}" not in self.content:
                self.warnings.append("Missing {ARGS} placeholder in Context section")
            else:
                self.checks.append(
                    {
                        "check": "Consistency",
                        "section": "Placeholders",
                        "status": "✓",
                        "message": "{ARGS} placeholder found",
                    }
                )

        # Check for description in frontmatter
        if not self.content.startswith("---"):
            self.errors.append("Missing frontmatter with description")
            passed = False
        elif "description:" not in self.content[:200]:  # Check first 200 chars for frontmatter
            self.warnings.append("Frontmatter may be missing description field")
        else:
            self.checks.append(
                {
                    "check": "Consistency",
                    "section": "Frontmatter",
                    "status": "✓",
                    "message": "Frontmatter with description found",
                }
            )

        # Check for main title (H1)
        if not self.content.startswith("# SpecFact"):
            # Allow for frontmatter before title
            if "# SpecFact" not in self.content[:500]:  # Check first 500 chars
                self.warnings.append("Main title (H1) may be missing or not starting with '# SpecFact'")

        return passed

    def validate_all(self) -> dict[str, Any]:
        """Run all validations."""
        results = {
            "prompt": self.prompt_name,
            "path": str(self.prompt_path),
            "errors": [],
            "warnings": [],
            "checks": [],
            "passed": True,
        }

        # Run all validations
        structure_ok = self.validate_structure()
        cli_ok = self.validate_cli_alignment()
        wait_ok = self.validate_wait_states()
        dual_stack_ok = self.validate_dual_stack_workflow()
        consistency_ok = self.validate_consistency()

        results["errors"] = self.errors
        results["warnings"] = self.warnings
        results["checks"] = self.checks
        results["passed"] = (
            structure_ok and cli_ok and wait_ok and dual_stack_ok and consistency_ok and len(self.errors) == 0
        )

        return results


def validate_all_prompts(prompts_dir: Path | None = None) -> list[dict[str, Any]]:
    """Validate all prompt templates."""
    if prompts_dir is None:
        prompts_dir = Path(__file__).parent.parent / "resources" / "prompts"

    results = []
    # Match both specfact.*.md and specfact-*.md patterns
    for prompt_file in sorted(prompts_dir.glob("specfact.*.md")):
        validator = PromptValidator(prompt_file)
        results.append(validator.validate_all())

    return results


def print_validation_report(results: list[dict[str, Any]]) -> int:
    """Print validation report.

    Returns:
        Exit code: 0 if all prompts passed, 1 if any failed
    """
    console.print("\n[bold cyan]Prompt Validation Report[/bold cyan]\n")

    # Summary table
    summary_table = Table(title="Validation Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Prompt", style="cyan")
    summary_table.add_column("Status", style="green")
    summary_table.add_column("Errors", justify="right")
    summary_table.add_column("Warnings", justify="right")
    summary_table.add_column("Checks", justify="right")

    for result in results:
        status = "[green]✓ PASS[/green]" if result["passed"] else "[red]✗ FAIL[/red]"
        summary_table.add_row(
            result["prompt"],
            status,
            str(len(result["errors"])),
            str(len(result["warnings"])),
            str(len(result["checks"])),
        )

    console.print(summary_table)

    # Detailed errors
    all_errors = [r for r in results if r["errors"]]
    if all_errors:
        console.print("\n[bold red]Errors:[/bold red]\n")
        for result in all_errors:
            console.print(f"[red]✗ {result['prompt']}[/red]")
            for error in result["errors"]:
                console.print(f"  - {error}")

    # Detailed warnings
    all_warnings = [r for r in results if r["warnings"]]
    if all_warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
        for result in all_warnings:
            console.print(f"[yellow]⚠ {result['prompt']}[/yellow]")
            for warning in result["warnings"]:
                console.print(f"  - {warning}")

    # Overall status
    total_passed = sum(1 for r in results if r["passed"])
    total_failed = len(results) - total_passed

    console.print(f"\n[bold]Overall:[/bold] {total_passed}/{len(results)} prompts passed")
    if total_failed > 0:
        console.print(f"[red]{total_failed} prompts failed validation[/red]")
        return 1

    return 0


def main() -> int:
    """Main entry point."""
    results = validate_all_prompts()
    return print_validation_report(results)


if __name__ == "__main__":
    import sys

    sys.exit(main())
