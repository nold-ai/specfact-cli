"""Simple in-memory policy registry for module extensions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from beartype import beartype
from icontract import ensure, require

from ..config.policy_config import PolicyConfig
from ..models.policy_result import PolicyResult


PolicyEvaluator = Callable[[PolicyConfig, list[dict[str, Any]]], list[PolicyResult]]


@beartype
class PolicyRegistry:
    """Registry for policy evaluators contributed by other modules."""

    def __init__(self) -> None:
        self._evaluators: dict[str, PolicyEvaluator] = {}

    @require(lambda name: name.strip() != "", "Policy evaluator name must not be empty")
    @ensure(lambda self, name: name in self._evaluators, "Evaluator must be registered")
    def register(self, name: str, evaluator: PolicyEvaluator) -> None:
        """Register a named evaluator."""
        self._evaluators[name] = evaluator

    def list_names(self) -> list[str]:
        """Return registered evaluator names."""
        return sorted(self._evaluators.keys())

    def get_all(self) -> list[PolicyEvaluator]:
        """Return evaluators in registration order."""
        return [self._evaluators[name] for name in self.list_names()]
