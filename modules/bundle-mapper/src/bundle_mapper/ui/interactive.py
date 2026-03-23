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


def _render_bundle_mapping(mapping: BundleMapping, available_bundles: list[str]) -> None:
    """Render the confidence panel for the selected bundle mapping."""
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
    if available_bundles:
        lines.append(f"Available bundles: {len(available_bundles)}")

    console.print(Panel("\n".join(lines), title="Bundle mapping"))


def _select_available_bundle(available_bundles: list[str]) -> str | None:
    """Prompt the user to choose from the full bundle list."""
    for i, bundle_id in enumerate(available_bundles, 1):
        console.print(f"  {i}. {bundle_id}")
    idx = Prompt.ask("Enter number", default="1")
    try:
        choice = int(idx)
    except ValueError:
        return None
    if 1 <= choice <= len(available_bundles):
        return available_bundles[choice - 1]
    return None


def _select_candidate_bundle(choice: str, candidates: list[tuple[str, float]]) -> str | None:
    """Return the candidate bundle chosen by number, if valid."""
    if not choice.isdigit() or not candidates:
        return None
    index = int(choice)
    if 1 <= index <= len(candidates):
        return candidates[index - 1][0]
    return None


def _resolve_bundle_choice(
    choice: str,
    primary: str | None,
    available_bundles: list[str],
    candidates: list[tuple[str, float]],
) -> str | None:
    """Resolve the prompt choice into a bundle id or None."""
    if choice == "Q":
        return None
    if choice == "A" and primary:
        return primary
    if choice == "S" and available_bundles:
        return _select_available_bundle(available_bundles)

    selected_candidate = _select_candidate_bundle(choice, candidates)
    if selected_candidate:
        return selected_candidate
    return primary


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

    _render_bundle_mapping(mapping, available_bundles)
    if auto_accept_high and conf >= 0.8 and primary:
        return primary

    prompt_default: str | None = "A" if conf >= 0.5 else None
    raw_choice = Prompt.ask(
        "Accept (A), choose number from list (1-N), show all (S), skip (Q)",
        default=prompt_default,
    )
    choice = (raw_choice or "").strip().upper()
    return _resolve_bundle_choice(choice, primary, available_bundles, candidates)
