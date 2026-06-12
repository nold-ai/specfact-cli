"""
Intelligent suggestions system for CLI commands.

This module provides utilities for suggesting next steps, fixes, and improvements
based on project context and current state.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel

from specfact_cli.utils.context_detection import ProjectContext, detect_project_context
from specfact_cli.utils.contract_predicates import repo_path_exists


console = Console()


def _suggest_fixes_error_nonempty(error_message: str, context: ProjectContext | None) -> bool:
    return error_message.strip() != ""


@beartype
@require(repo_path_exists, "repo_path must exist")
@ensure(lambda result: isinstance(result, list), "Must return list")
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
        suggestions.append("specfact code import --repo . <name>  # Import your codebase")
        suggestions.append("specfact init  # Initialize SpecFact configuration")
        return suggestions

    # Analysis suggestions
    if context.has_plan and context.contract_coverage < 0.5:
        suggestions.append("specfact code analyze contracts --bundle <name>  # Analyze contract coverage")
        suggestions.append("specfact code import --repo . <name>  # Update the project bundle from code")

    # Specmatic integration suggestions
    if context.has_specmatic_config and not context.openapi_specs:
        suggestions.append("specfact spec validate --bundle <name>  # Validate API contracts")

    # Enforcement suggestions
    if context.has_plan and not context.last_enforcement:
        suggestions.append("specfact govern enforce sdd <name>  # Enforce quality gates")

    # Sync suggestions
    if context.has_plan:
        suggestions.append("specfact project sync intelligent <name>  # Sync code and specs")

    return suggestions


@beartype
@require(_suggest_fixes_error_nonempty, "error_message must not be empty")
@ensure(lambda result: isinstance(result, list), "Must return list")
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
        suggestions.append("specfact project --help  # Inspect available project bundle commands")
        suggestions.append("specfact code import --repo . <name>  # Create a new bundle from code")

    # Contract validation errors
    if "contract" in error_lower and ("violation" in error_lower or "invalid" in error_lower):
        suggestions.append("specfact code analyze contracts --bundle <name>  # Analyze contract violations")
        suggestions.append("specfact code repro --repo .  # Run validation suite")

    # Specmatic errors
    if "specmatic" in error_lower or "openapi" in error_lower:
        suggestions.append("specfact spec validate --bundle <name>  # Validate API contracts")
        suggestions.append("specfact spec test --bundle <name>  # Run contract tests")

    # Import errors
    if "import" in error_lower and "failed" in error_lower:
        suggestions.append("specfact code import --repo . <name>  # Retry import")

    return suggestions


@beartype
@ensure(lambda result: isinstance(result, list), "Must return list")
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
        suggestions.append("specfact code analyze contracts --bundle <name>  # Identify missing contracts")
        suggestions.append("specfact code import --repo . <name>  # Extract contracts from code")

    # Missing OpenAPI specs
    if context.has_plan and not context.openapi_specs:
        suggestions.append("specfact generate contracts --bundle <name>  # Generate OpenAPI contracts")

    # No Specmatic config
    if context.openapi_specs and not context.has_specmatic_config:
        suggestions.append("specfact spec init --bundle <name>  # Initialize Specmatic configuration")

    # Outdated enforcement
    if context.last_enforcement:
        suggestions.append("specfact govern enforce sdd <name>  # Re-run quality gates")

    return suggestions


@beartype
@require(lambda suggestions: isinstance(suggestions, list), "suggestions must be a list")
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
