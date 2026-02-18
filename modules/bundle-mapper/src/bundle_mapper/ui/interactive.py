"""
Interactive bundle mapping UI: prompt user with confidence visualization (Rich).
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from bundle_mapper.models.bundle_mapping import BundleMapping


console = Console()


@beartype
@require(lambda mapping: mapping is not None, "Mapping must not be None")
@ensure(
    lambda result: result is None or isinstance(result, str),
    "Returns bundle_id or None",
)
def ask_bundle_mapping(
    mapping: BundleMapping,
    available_bundles: list[str] | None = None,
    auto_accept_high: bool = False,
) -> str | None:
    """
    Prompt user to accept or change bundle assignment.

    Displays confidence (✓ high / ? medium / ! low), suggested bundle, alternatives.
    Options: accept, select from candidates, show all bundles (S), skip (Q).
    Returns selected bundle_id or None if skipped.
    """
    available_bundles = available_bundles or []
    conf = mapping.confidence
    primary = mapping.primary_bundle_id
    candidates = mapping.candidates
    explanation = mapping.explained_reasoning

    if conf >= 0.8:
        label = "[green]✓ HIGH CONFIDENCE[/green]"
    elif conf >= 0.5:
        label = "[yellow]? MEDIUM CONFIDENCE[/yellow]"
    else:
        label = "[red]! LOW CONFIDENCE[/red]"

    lines = [
        f"{label}",
        f"Suggested bundle: [bold]{primary or '—'}[/bold]",
        explanation,
    ]
    if candidates:
        lines.append("Alternatives: " + ", ".join(f"{b} ({s:.2f})" for b, s in candidates[:5]))

    console.print(Panel("\n".join(lines), title="Bundle mapping"))
    if auto_accept_high and conf >= 0.8 and primary:
        return primary

    choice = (
        Prompt.ask(
            "Accept (A), choose number from list (1-N), show all (S), skip (Q)",
            default="A",
        )
        .strip()
        .upper()
    )

    if choice == "Q":
        return None
    if choice == "A" and primary:
        return primary
    if choice == "S" and available_bundles:
        for i, b in enumerate(available_bundles, 1):
            console.print(f"  {i}. {b}")
        idx = Prompt.ask("Enter number", default="1")
        try:
            i = int(idx)
            if 1 <= i <= len(available_bundles):
                return available_bundles[i - 1]
        except ValueError:
            pass
        return None
    if choice.isdigit() and candidates:
        i = int(choice)
        if 1 <= i <= len(candidates):
            return candidates[i - 1][0]
    return primary
