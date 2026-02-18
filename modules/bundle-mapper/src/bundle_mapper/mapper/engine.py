"""
BundleMapper engine: confidence-based mapping from backlog items to bundles.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from bundle_mapper.mapper.history import (
    item_key,
    item_keys_similar,
    load_bundle_mapping_config,
)
from bundle_mapper.models.bundle_mapping import BundleMapping


try:
    from specfact_cli.models.backlog_item import BacklogItem
except ImportError:
    BacklogItem = Any  # type: ignore[misc, assignment]

WEIGHT_EXPLICIT = 0.8
WEIGHT_HISTORICAL = 0.15
WEIGHT_CONTENT = 0.05
HISTORY_CAP = 10.0


def _tokenize(text: str) -> set[str]:
    """Lowercase, split by non-alphanumeric."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@beartype
class BundleMapper:
    """
    Computes mapping from backlog items to OpenSpec bundle ids using three signals:
    explicit labels (bundle:xyz), historical patterns, content similarity.
    """

    def __init__(
        self,
        available_bundle_ids: list[str] | None = None,
        config_path: Path | None = None,
        bundle_spec_keywords: dict[str, set[str]] | None = None,
    ) -> None:
        """
        Args:
            available_bundle_ids: Valid bundle ids (for explicit label validation).
            config_path: Path to .specfact config for rules/history.
            bundle_spec_keywords: Optional map bundle_id -> set of keywords from specs (for content similarity).
        """
        self._available_bundle_ids = set(available_bundle_ids or [])
        self._config_path = config_path
        self._config: dict[str, Any] = {}
        self._bundle_keywords = bundle_spec_keywords or {}

    def _load_config(self) -> dict[str, Any]:
        if not self._config:
            self._config = load_bundle_mapping_config(self._config_path)
        return self._config

    @beartype
    def _score_explicit_mapping(self, item: BacklogItem) -> tuple[str | None, float]:
        """Return (bundle_id, score) for explicit bundle:xyz tag, or (None, 0.0)."""
        prefix = self._load_config().get("explicit_label_prefix", "bundle:")
        for tag in item.tags:
            tag = (tag or "").strip()
            if tag.startswith(prefix):
                bundle_id = tag[len(prefix) :].strip()
                if bundle_id and (not self._available_bundle_ids or bundle_id in self._available_bundle_ids):
                    return (bundle_id, 1.0)
        return (None, 0.0)

    @beartype
    def _score_historical_mapping(self, item: BacklogItem) -> tuple[str | None, float]:
        """Return (bundle_id, score) from history, or (None, 0.0)."""
        key = item_key(item)
        history = self._load_config().get("history", {})
        best_bundle: str | None = None
        best_count = 0
        for hist_key, entry in history.items():
            if not item_keys_similar(key, hist_key):
                continue
            counts = entry.get("counts", {})
            for bid, cnt in counts.items():
                if cnt > best_count:
                    best_count = cnt
                    best_bundle = bid
        if best_bundle is None:
            return (None, 0.0)
        score = min(1.0, best_count / HISTORY_CAP)
        return (best_bundle, score)

    @beartype
    def _score_content_similarity(self, item: BacklogItem) -> list[tuple[str, float]]:
        """Return list of (bundle_id, score) by keyword overlap with item title/body."""
        text = f"{item.title} {item.body_markdown or ''}"
        tokens = _tokenize(text)
        if not tokens:
            return []
        results: list[tuple[str, float]] = []
        for bundle_id, keywords in self._bundle_keywords.items():
            sim = _jaccard(tokens, keywords)
            if sim > 0:
                results.append((bundle_id, sim))
        return sorted(results, key=lambda x: -x[1])

    @beartype
    def _explain_score(self, bundle_id: str, score: float, method: str) -> str:
        """Human-readable one-line explanation."""
        if method == "explicit_label":
            return f"Explicit label → {bundle_id} (confidence {score:.2f})"
        if method == "historical":
            return f"Historical pattern → {bundle_id} (confidence {score:.2f})"
        if method == "content_similarity":
            return f"Content similarity → {bundle_id} (confidence {score:.2f})"
        return f"{bundle_id} (confidence {score:.2f})"

    @beartype
    def _build_explanation(
        self,
        primary_bundle_id: str | None,
        confidence: float,
        candidates: list[tuple[str, float]],
        reasons: list[str],
    ) -> str:
        """Build full explanation string."""
        parts = [f"Confidence: {confidence:.2f}"]
        if reasons:
            parts.append("; ".join(reasons))
        if candidates:
            parts.append("Alternatives: " + ", ".join(f"{b}({s:.2f})" for b, s in candidates[:5]))
        return ". ".join(parts)

    @beartype
    @require(lambda item: item is not None, "Item must not be None")
    @ensure(
        lambda result: 0.0 <= result.confidence <= 1.0,
        "Confidence in [0, 1]",
    )
    def compute_mapping(self, item: BacklogItem) -> BundleMapping:
        """
        Compute mapping for one backlog item using weighted signals:
        0.8 * explicit + 0.15 * historical + 0.05 * content.
        """
        reasons: list[str] = []
        explicit_bundle, explicit_score = self._score_explicit_mapping(item)
        hist_bundle, hist_score = self._score_historical_mapping(item)
        content_list = self._score_content_similarity(item)

        primary_bundle_id: str | None = None
        weighted = 0.0

        if explicit_bundle and explicit_score > 0:
            primary_bundle_id = explicit_bundle
            weighted += WEIGHT_EXPLICIT * explicit_score
            reasons.append(self._explain_score(explicit_bundle, explicit_score, "explicit_label"))

        if hist_bundle and hist_score > 0:
            contrib = WEIGHT_HISTORICAL * hist_score
            if primary_bundle_id is None:
                primary_bundle_id = hist_bundle
                weighted += contrib
                reasons.append(self._explain_score(hist_bundle, hist_score, "historical"))
            elif hist_bundle == primary_bundle_id:
                weighted += contrib

        if content_list:
            best_content = content_list[0]
            contrib = WEIGHT_CONTENT * best_content[1]
            weighted += contrib
            if primary_bundle_id is None:
                primary_bundle_id = best_content[0]
                reasons.append(self._explain_score(best_content[0], best_content[1], "content_similarity"))

        confidence = min(1.0, weighted)
        candidates: list[tuple[str, float]] = []
        if primary_bundle_id:
            seen = {primary_bundle_id}
            for bid, sc in content_list:
                if bid not in seen:
                    seen.add(bid)
                    candidates.append((bid, sc * WEIGHT_CONTENT))
        explanation = self._build_explanation(primary_bundle_id, confidence, candidates, reasons)
        return BundleMapping(
            primary_bundle_id=primary_bundle_id,
            confidence=confidence,
            candidates=candidates[:10],
            explained_reasoning=explanation,
        )
