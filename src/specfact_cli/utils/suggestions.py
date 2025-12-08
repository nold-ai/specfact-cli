"""
Intelligent suggestions system for CLI commands.

This module provides utilities for suggesting next steps, fixes, and improvements
based on project context and current state.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from rich.console import Console
from rich.panel import Panel

from specfact_cli.utils.context_detection import ProjectContext, detect_project_context


console = Console()


@beartype
def suggest_next_steps(repo_path: Path, context: ProjectContext | None = None) -> list[str]:
    """
    Suggest next commands based on project context.

    Args:
        repo_path: Repository path
        context: Optional project context (will be detected if not provided)

    Returns:
        List of suggested command strings
    """
    if context is None:
        context = detect_project_context(repo_path)

    suggestions: list[str] = []

    # First-time setup suggestions
    if not context.has_plan and not context.has_config:
        suggestions.append("specfact import from-code --bundle <name>  # Import your codebase")
        suggestions.append("specfact init  # Initialize SpecFact configuration")
        return suggestions

    # Analysis suggestions
    if context.has_plan and context.contract_coverage < 0.5:
        suggestions.append("specfact analyze --bundle <name>  # Analyze contract coverage")
        suggestions.append("specfact import from-code --bundle <name>  # Update plan from code")

    # Specmatic integration suggestions
    if context.has_specmatic_config and not context.openapi_specs:
        suggestions.append("specfact spec validate --bundle <name>  # Validate API contracts")

    # Enforcement suggestions
    if context.has_plan and not context.last_enforcement:
        suggestions.append("specfact enforce sdd --bundle <name>  # Enforce quality gates")

    # Sync suggestions
    if context.has_plan:
        suggestions.append("specfact sync intelligent --bundle <name>  # Sync code and specs")

    return suggestions


@beartype
def suggest_fixes(error_message: str, context: ProjectContext | None = None) -> list[str]:
    """
    Suggest fixes for common errors.

    Args:
        error_message: Error message to analyze
        context: Optional project context

    Returns:
        List of suggested fix commands
    """
    suggestions: list[str] = []

    error_lower = error_message.lower()

    # Bundle not found
    if "bundle" in error_lower and ("not found" in error_lower or "does not exist" in error_lower):
        suggestions.append("specfact plan select  # Select an active plan bundle")
        suggestions.append("specfact import from-code --bundle <name>  # Create a new bundle")

    # Contract validation errors
    if "contract" in error_lower and ("violation" in error_lower or "invalid" in error_lower):
        suggestions.append("specfact analyze --bundle <name>  # Analyze contract violations")
        suggestions.append("specfact repro --bundle <name>  # Run validation suite")

    # Specmatic errors
    if "specmatic" in error_lower or "openapi" in error_lower:
        suggestions.append("specfact spec validate --bundle <name>  # Validate API contracts")
        suggestions.append("specfact spec test --bundle <name>  # Run contract tests")

    # Import errors
    if "import" in error_lower and "failed" in error_lower:
        suggestions.append("specfact import from-code --bundle <name> --repo .  # Retry import")

    return suggestions


@beartype
def suggest_improvements(context: ProjectContext) -> list[str]:
    """
    Suggest improvements based on analysis.

    Args:
        context: Project context

    Returns:
        List of suggested improvement commands
    """
    suggestions: list[str] = []

    # Low contract coverage
    if context.contract_coverage < 0.3:
        suggestions.append("specfact analyze --bundle <name>  # Identify missing contracts")
        suggestions.append("specfact import from-code --bundle <name>  # Extract contracts from code")

    # Missing OpenAPI specs
    if context.has_plan and not context.openapi_specs:
        suggestions.append("specfact generate contracts --bundle <name>  # Generate OpenAPI contracts")

    # No Specmatic config
    if context.openapi_specs and not context.has_specmatic_config:
        suggestions.append("specfact spec init --bundle <name>  # Initialize Specmatic configuration")

    # Outdated enforcement
    if context.last_enforcement:
        suggestions.append("specfact enforce sdd --bundle <name>  # Re-run quality gates")

    return suggestions


@beartype
def print_suggestions(suggestions: list[str], title: str = "💡 Suggestions") -> None:
    """
    Print suggestions in a formatted panel.

    Args:
        suggestions: List of suggestion strings
        title: Panel title
    """
    if not suggestions:
        return

    suggestion_text = "\n".join(f"  • {s}" for s in suggestions)
    console.print(
        Panel(
            suggestion_text,
            title=title,
            border_style="cyan",
        )
    )
