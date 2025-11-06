"""Interactive prompt utilities for CLI commands."""

from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table


console = Console()


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
@require(lambda default: default is None or isinstance(default, str), "Default must be None or string")
@ensure(lambda result: isinstance(result, str), "Must return string")
def prompt_text(message: str, default: str | None = None, required: bool = True) -> str:
    """
    Prompt user for text input.

    Args:
        message: Prompt message
        default: Default value
        required: Whether input is required

    Returns:
        User input string
    """
    while True:
        result = Prompt.ask(message, default=default if default else "")
        if result or not required:
            return result
        console.print("[yellow]This field is required[/yellow]")


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
@require(lambda separator: isinstance(separator, str) and len(separator) > 0, "Separator must be non-empty string")
@ensure(lambda result: isinstance(result, list), "Must return list")
@ensure(lambda result: all(isinstance(item, str) for item in result), "All items must be strings")
def prompt_list(message: str, separator: str = ",") -> list[str]:
    """
    Prompt user for comma-separated list input.

    Args:
        message: Prompt message
        separator: List item separator

    Returns:
        List of strings
    """
    result = Prompt.ask(f"{message} (comma-separated)")
    if not result:
        return []
    return [item.strip() for item in result.split(separator) if item.strip()]


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
def prompt_dict(message: str) -> dict[str, Any]:
    """
    Prompt user for key:value pairs.

    Args:
        message: Prompt message

    Returns:
        Dictionary of key-value pairs
    """
    console.print(f"\n[bold]{message}[/bold]")
    console.print("Enter key:value pairs (one per line, empty line to finish)")

    result = {}
    while True:
        line = Prompt.ask("  ", default="")
        if not line:
            break

        if ":" not in line:
            console.print("[yellow]Format should be key:value[/yellow]")
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        # Try to convert to number if possible
        try:
            if "." in value:
                result[key] = float(value)
            else:
                result[key] = int(value)
        except ValueError:
            result[key] = value

    return result


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
def prompt_confirm(message: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        message: Prompt message
        default: Default value

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(message, default=default)


@beartype
@require(lambda title: isinstance(title, str) and len(title) > 0, "Title must be non-empty string")
@require(lambda data: isinstance(data, dict), "Data must be dictionary")
def display_summary(title: str, data: dict[str, Any]) -> None:
    """
    Display a summary table.

    Args:
        title: Table title
        data: Data to display
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    for key, value in data.items():
        if isinstance(value, list):
            value_str = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value_str = ", ".join(f"{k}={v}" for k, v in value.items())
        else:
            value_str = str(value)
        table.add_row(key, value_str)

    console.print(table)


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✅ {message}[/bold green]")


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]❌ {message}[/bold red]")


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[bold blue]ℹ️  {message}[/bold blue]")


@beartype
@require(lambda title: isinstance(title, str) and len(title) > 0, "Title must be non-empty string")
def print_section(title: str) -> None:
    """Print section header."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")
