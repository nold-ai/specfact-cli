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

# Required sections for all prompts
REQUIRED_SECTIONS = [
    ("CRITICAL: CLI Usage Enforcement", "⚠️ CRITICAL: CLI Usage Enforcement"),
    ("Wait States: User Input Required", "⏸️ Wait States: User Input Required"),
    ("Goal", "## Goal"),
    ("Operating Constraints", "## Operating Constraints"),
]

# CLI commands that should be referenced (new slash command names)
CLI_COMMANDS = {
    "specfact.01-import": "specfact import from-code",
    "specfact.02-plan": "specfact plan <operation>",  # init, add-feature, add-story, update-idea, update-feature, update-story
    "specfact.03-review": "specfact plan review",  # Also handles promote
    "specfact.04-sdd": "specfact plan harden",
    "specfact.05-enforce": "specfact enforce sdd",
    "specfact.06-sync": "specfact sync bridge",
    "specfact.compare": "specfact plan compare",
    "specfact.validate": "specfact repro",
}

# Required CLI enforcement rules
CLI_ENFORCEMENT_RULES = [
    "ALWAYS execute CLI first",
    "NEVER create YAML/JSON directly",
    "NEVER bypass CLI validation",
    "Use CLI output as grounding",
]

# Required wait state rules
WAIT_STATE_RULES = [
    "Never assume",
    "Never continue",
    "Be explicit",
    "Provide options",
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

        # Check CLI enforcement rules
        for rule in CLI_ENFORCEMENT_RULES:
            if rule not in self.content:
                self.warnings.append(f"CLI enforcement rule not found: '{rule}'")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "CLI Alignment",
                        "section": "Enforcement Rule",
                        "status": "✓",
                        "message": f"Rule '{rule}' found",
                    }
                )

        return passed

    def validate_wait_states(self) -> bool:
        """Validate wait state rules."""
        passed = True

        for rule in WAIT_STATE_RULES:
            if rule not in self.content:
                self.warnings.append(f"Wait state rule not found: '{rule}'")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "Wait States",
                        "section": "Wait State Rule",
                        "status": "✓",
                        "message": f"Rule '{rule}' found",
                    }
                )

        # Check for explicit wait state markers
        wait_markers = ["WAIT FOR USER RESPONSE", "DO NOT CONTINUE"]
        for marker in wait_markers:
            if marker not in self.content:
                self.warnings.append(f"Wait state marker not found: '{marker}'")
            else:
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

        # Check for dual-stack workflow section
        dual_stack_markers = [
            "Dual-Stack Workflow",
            "Phase 1: CLI Grounding",
            "Phase 2: LLM Enrichment",
            "Phase 3: CLI Artifact Creation",
        ]

        for marker in dual_stack_markers:
            if marker not in self.content:
                self.errors.append(f"Missing dual-stack workflow marker: '{marker}'")
                passed = False
            else:
                self.checks.append(
                    {
                        "check": "Dual-Stack",
                        "section": "Workflow Phase",
                        "status": "✓",
                        "message": f"Phase '{marker}' found",
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
            self.errors.append("Missing $ARGUMENTS placeholder")
            passed = False

        # Check for description in frontmatter
        if not self.content.startswith("---"):
            self.warnings.append("Missing frontmatter with description")

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
    for prompt_file in sorted(prompts_dir.glob("specfact-*.md")):
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
