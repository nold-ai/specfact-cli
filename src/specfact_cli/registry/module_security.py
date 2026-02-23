"""Module security helpers: denylist enforcement and publisher trust decisions."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import typer
from beartype import beartype

from specfact_cli.utils.metadata import get_metadata, update_metadata


DEFAULT_DENYLIST_PATH = Path.home() / ".specfact" / "module-denylist.txt"
TRUSTED_PUBLISHERS_KEY = "trusted_module_publishers"
OFFICIAL_PUBLISHERS = {"nold-ai"}
_TRUTHY = {"1", "true", "yes"}


@beartype
def is_official_publisher(publisher_name: str | None) -> bool:
    """Return True when publisher is official."""
    normalized = (publisher_name or "").strip().lower()
    return normalized in OFFICIAL_PUBLISHERS


@beartype
def get_denylist_path() -> Path:
    """Return configured module denylist path."""
    configured = os.environ.get("SPECFACT_MODULE_DENYLIST_FILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_DENYLIST_PATH


@beartype
def get_denylisted_modules(path: Path | None = None) -> set[str]:
    """Load denylisted module ids from file."""
    denylist_path = path or get_denylist_path()
    if not denylist_path.exists():
        return set()
    items: set[str] = set()
    for raw_line in denylist_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            items.add(line.lower())
    return items


@beartype
def assert_module_allowed(module_name: str) -> None:
    """Raise when module is denylisted."""
    normalized = module_name.strip().lower()
    if not normalized:
        raise ValueError("Module name must be non-empty")
    denylisted = get_denylisted_modules()
    if normalized not in denylisted:
        return
    denylist_path = get_denylist_path()
    raise ValueError(
        f"Module '{module_name}' is denylisted and cannot be installed or bootstrapped (denylist: {denylist_path})."
    )


@beartype
def get_trusted_publishers() -> set[str]:
    """Return persisted trusted non-official publishers."""
    metadata = get_metadata()
    raw = metadata.get(TRUSTED_PUBLISHERS_KEY, [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip().lower() for item in raw if str(item).strip()}


@beartype
def _persist_trusted_publishers(publishers: set[str]) -> None:
    """Persist trusted publishers in user metadata."""
    update_metadata(**{TRUSTED_PUBLISHERS_KEY: sorted(publishers)})


@beartype
def trust_flag_enabled() -> bool:
    """Return True when explicit trust env override is enabled."""
    return os.environ.get("SPECFACT_TRUST_NON_OFFICIAL", "").strip().lower() in _TRUTHY


@beartype
def ensure_publisher_trusted(
    publisher_name: str | None,
    *,
    trust_non_official: bool = False,
    non_interactive: bool = False,
    confirm_callback: Callable[[str], bool] | None = None,
) -> None:
    """Ensure non-official publisher is trusted before proceeding."""
    normalized = (publisher_name or "").strip().lower()
    if not normalized or is_official_publisher(normalized):
        return

    trusted = get_trusted_publishers()
    if normalized in trusted:
        return

    if trust_non_official or trust_flag_enabled():
        trusted.add(normalized)
        _persist_trusted_publishers(trusted)
        return

    if non_interactive:
        raise ValueError(f"Publisher '{publisher_name}' is non-official. Re-run with --trust-non-official to continue.")

    confirm = confirm_callback or (lambda message: typer.confirm(message, default=False))
    accepted = confirm(
        f"Publisher '{publisher_name}' is non-official and may be unsafe. Trust this publisher for future installs?"
    )
    if not accepted:
        raise ValueError(f"Publisher '{publisher_name}' was not trusted; installation cancelled.")

    trusted.add(normalized)
    _persist_trusted_publishers(trusted)
