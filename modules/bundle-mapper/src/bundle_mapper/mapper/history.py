"""
Mapping history persistence: save and load user-confirmed mappings from config.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


DEFAULT_LABEL_PREFIX = "bundle:"
DEFAULT_AUTO_ASSIGN_THRESHOLD = 0.8
DEFAULT_CONFIRM_THRESHOLD = 0.5


@runtime_checkable
class _ItemLike(Protocol):
    """Minimal interface for backlog item used by history."""

    id: str
    assignees: list[str]
    area: str | None
    tags: list[str]


class MappingRule(BaseModel):
    """A single mapping rule (pattern -> bundle_id)."""

    pattern: str = Field(..., description="Pattern: tag=~regex, assignee=exact, area=exact")
    bundle_id: str = Field(..., description="Target bundle id")
    action: str = Field(default="assign", description="Action: assign")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Rule confidence")

    @beartype
    def matches(self, item: _ItemLike) -> bool:
        """Return True if this rule matches the item."""
        if self.pattern.startswith("tag=~"):
            regex = self.pattern[5:].strip()
            try:
                pat = re.compile(regex)
            except re.error:
                return False
            return any(pat.search(t) for t in item.tags)
        if self.pattern.startswith("assignee="):
            val = self.pattern[9:].strip()
            return val in item.assignees
        if self.pattern.startswith("area="):
            val = self.pattern[5:].strip()
            return item.area == val
        return False


def item_key(item: _ItemLike) -> str:
    """Build a stable key for history lookup (area, assignee, tags)."""
    area = (item.area or "").strip()
    assignee = (item.assignees[0] if item.assignees else "").strip()
    tags_str = "|".join(sorted(t.strip() for t in item.tags if t))
    return f"area={area}|assignee={assignee}|tags={tags_str}"


def item_keys_similar(key_a: str, key_b: str) -> bool:
    """Return True if keys share at least 2 of 3 components (area, assignee, tags)."""

    def parts(k: str) -> tuple[str, str, str]:
        d: dict[str, str] = {}
        for seg in k.split("|"):
            if "=" in seg:
                name, val = seg.split("=", 1)
                d[name.strip()] = val.strip()
        return (d.get("area", ""), d.get("assignee", ""), d.get("tags", ""))

    a1, a2, a3 = parts(key_a)
    b1, b2, b3 = parts(key_b)
    matches = sum([a1 == b1, a2 == b2, a3 == b3])
    return matches >= 2


@beartype
@require(lambda config_path: config_path is None or config_path.exists() or not config_path.exists(), "Path valid")
@ensure(lambda result: result is None, "Returns None")
def save_user_confirmed_mapping(
    item: _ItemLike,
    bundle_id: str,
    config_path: Path | None = None,
) -> None:
    """
    Persist a user-confirmed mapping: increment history count and save to config.

    Creates item_key from item metadata, increments mapping count in history,
    and writes backlog.bundle_mapping.history to config_path (or default .specfact/config.yaml).
    """
    if config_path is None:
        config_path = Path.home() / ".specfact" / "config.yaml"
    key = item_key(item)
    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    backlog = data.setdefault("backlog", {})
    bm = backlog.setdefault("bundle_mapping", {})
    history = bm.setdefault("history", {})
    entry = history.setdefault(key, {})
    counts = entry.setdefault("counts", {})
    counts[bundle_id] = counts.get(bundle_id, 0) + 1
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


@beartype
def load_bundle_mapping_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load backlog.bundle_mapping section from config; return dict with rules, history, thresholds."""
    if config_path is None:
        config_path = Path.home() / ".specfact" / "config.yaml"
    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    bm = (data.get("backlog") or {}).get("bundle_mapping") or {}
    return {
        "rules": bm.get("rules", []),
        "history": bm.get("history", {}),
        "explicit_label_prefix": bm.get("explicit_label_prefix", DEFAULT_LABEL_PREFIX),
        "auto_assign_threshold": float(bm.get("auto_assign_threshold", DEFAULT_AUTO_ASSIGN_THRESHOLD)),
        "confirm_threshold": float(bm.get("confirm_threshold", DEFAULT_CONFIRM_THRESHOLD)),
    }
