"""Regression coverage for OpenSpec artifact-rule parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_all_openspec_artifact_rules_are_strings() -> None:
    config = cast(dict[str, Any], yaml.safe_load((REPOSITORY_ROOT / "openspec" / "config.yaml").read_text()))
    rules = cast(dict[str, list[object]], config["rules"])

    assert rules
    assert all(isinstance(rule, str) for artifact_rules in rules.values() for rule in artifact_rules)
