"""Pure environment-scope matching for reviewed license exceptions."""

from __future__ import annotations

from typing import Literal

from beartype import beartype
from icontract import ensure


EnvironmentAllowlistScope = Literal["dev-only", "code-review-only"]


@beartype
@ensure(lambda result: isinstance(result, bool))
def environment_allowlist_entry_matches(
    entry: dict[str, str],
    license_expr: str,
    version: str,
    *,
    allowlist_scope: EnvironmentAllowlistScope,
    require_version: bool = False,
) -> bool:
    """Return whether one reviewed entry matches the exact environment observation."""
    entry_license = entry.get("license", "").strip().lower()
    reviewed_version = entry.get("version", "").strip()
    return (
        entry.get("scope") == allowlist_scope
        and bool(entry_license)
        and entry_license == license_expr.strip().lower()
        and (reviewed_version == version.strip() if reviewed_version else not require_version)
    )
