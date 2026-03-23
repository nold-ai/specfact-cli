"""
Mapping history persistence: save and load user-confirmed mappings from config.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable
from urllib.parse import quote, unquote

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
    @require(lambda item: item is not None, "item is required")
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


@beartype
@require(lambda item: item is not None, "item is required")
@ensure(lambda result: bool(result), "item key must be non-empty")
def item_key(item: _ItemLike) -> str:
    """Build a stable key for history lookup (area, assignee, tags)."""
    area = quote((item.area or "").strip(), safe="")
    assignee = quote((item.assignees[0] if item.assignees else "").strip(), safe="")
    # Use comma-separated, URL-encoded tag values to avoid delimiter collisions.
    tags = [quote(t.strip(), safe="") for t in sorted(t.strip() for t in item.tags if t)]
    tags_str = ",".join(tags)
    return f"area={area};assignee={assignee};tags={tags_str}"


def _parse_modern_key(k: str) -> tuple[str, str, str]:
    """Parse the modern area=...;assignee=...;tags=a,b format."""
    data: dict[str, str] = {}
    for seg in k.split(";"):
        if "=" in seg:
            name, val = seg.split("=", 1)
            data[name.strip()] = val.strip()
    area = unquote(data.get("area", ""))
    assignee = unquote(data.get("assignee", ""))
    tags_raw = data.get("tags", "")
    tags = [unquote(tag) for tag in tags_raw.split(",") if tag]
    return (area, assignee, ",".join(tags))


def _parse_legacy_key(k: str) -> tuple[str, str, str]:
    """Parse the legacy area=...|assignee=...|tags=a|b format."""
    data: dict[str, str] = {}
    segments = k.split("|")
    idx = 0
    while idx < len(segments):
        seg = segments[idx]
        if "=" in seg:
            name, val = seg.split("=", 1)
            name = name.strip()
            val = val.strip()
            if name == "tags":
                tag_parts = [val] if val else []
                j = idx + 1
                while j < len(segments) and "=" not in segments[j]:
                    if segments[j]:
                        tag_parts.append(segments[j].strip())
                    j += 1
                data["tags"] = ",".join(tag_parts)
                idx = j
                continue
            data[name] = val
        idx += 1
    return (data.get("area", ""), data.get("assignee", ""), data.get("tags", ""))


@beartype
@require(lambda key_a: bool(cast(str, key_a).strip()), "key_a must be non-empty")
@require(lambda key_b: bool(cast(str, key_b).strip()), "key_b must be non-empty")
def item_keys_similar(key_a: str, key_b: str) -> bool:
    """Return True if keys share at least 2 of 3 non-empty components (area, assignee, tags). Empty fields are ignored to avoid matching unrelated items."""
    parser = _parse_modern_key if ";" in key_a else _parse_legacy_key
    a1, a2, a3 = parser(key_a)
    parser = _parse_modern_key if ";" in key_b else _parse_legacy_key
    b1, b2, b3 = parser(key_b)
    matches = 0
    if a1 and b1 and a1 == b1:
        matches += 1
    if a2 and b2 and a2 == b2:
        matches += 1
    if a3 and b3 and a3 == b3:
        matches += 1
    return matches >= 2


@beartype
@require(
    lambda config_path: config_path is None or cast(Path, config_path).exists() or not cast(Path, config_path).exists(),
    "Path valid",
)
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
            raw = yaml.safe_load(f)
            data = cast(dict[str, Any], raw if isinstance(raw, dict) else {})
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
@ensure(lambda result: isinstance(result, dict), "returns configuration dictionary")
def load_bundle_mapping_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load backlog.bundle_mapping section from config; return dict with rules, history, thresholds."""
    if config_path is None:
        config_path = Path.home() / ".specfact" / "config.yaml"
    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            data = cast(dict[str, Any], raw if isinstance(raw, dict) else {})
    backlog_raw = data.get("backlog")
    backlog = cast(dict[str, Any], backlog_raw) if isinstance(backlog_raw, dict) else {}
    bm_raw = backlog.get("bundle_mapping")
    bm = cast(dict[str, Any], bm_raw) if isinstance(bm_raw, dict) else {}

    def _safe_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    hist_raw = bm.get("history", {})
    history_norm: dict[str, Any] = cast(dict[str, Any], hist_raw) if isinstance(hist_raw, dict) else {}
    return {
        "rules": bm.get("rules", []),
        "history": history_norm,
        "explicit_label_prefix": bm.get("explicit_label_prefix", DEFAULT_LABEL_PREFIX),
        "auto_assign_threshold": _safe_float(bm.get("auto_assign_threshold"), DEFAULT_AUTO_ASSIGN_THRESHOLD),
        "confirm_threshold": _safe_float(bm.get("confirm_threshold"), DEFAULT_CONFIRM_THRESHOLD),
    }
