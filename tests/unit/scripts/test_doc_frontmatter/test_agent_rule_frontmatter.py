#!/usr/bin/env python3
"""Tests for agent-rule frontmatter validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests.helpers.doc_frontmatter import write_enforced
from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


VALID_AGENT_RULE_FRONTMATTER = """---
title: "Agent Rules Index"
id: agent-rules-index
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
always_load: true
applies_when:
  - session-bootstrap
priority: 0
blocking: true
user_interaction_required: false
stop_conditions:
  - canonical rule index missing
depends_on: []
---

# Agent Rules Index
"""


class TestAgentRuleFrontmatterModel:
    """Pydantic model for deterministic agent-rule frontmatter."""

    def test_model_validate_accepts_valid_rule_dict(
        self, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        agent_rule_model = check_doc_frontmatter_module.AgentRuleFrontmatter
        data = {
            "title": "Agent Rules Index",
            "id": "agent-rules-index",
            "doc_owner": "specfact-cli",
            "tracks": ["AGENTS.md", "docs/agent-rules/**"],
            "last_reviewed": "2026-04-10",
            "exempt": False,
            "exempt_reason": "",
            "always_load": True,
            "applies_when": ["session-bootstrap"],
            "priority": 0,
            "blocking": True,
            "user_interaction_required": False,
            "stop_conditions": ["canonical rule index missing"],
            "depends_on": [],
        }

        rec = agent_rule_model.model_validate(data)
        assert rec.id == "agent-rules-index"
        assert rec.always_load is True
        assert rec.priority == 0
        assert rec.applies_when == ["session-bootstrap"]


class TestAgentRuleFrontmatterValidation:
    """Integration-style validation of docs/agent-rules files."""

    def test_validation_accepts_valid_agent_rule_file(
        self, monkeypatch: pytest.MonkeyPatch, check_doc_frontmatter_module: CheckDocFrontmatterModule
    ) -> None:
        validation_main = check_doc_frontmatter_module.main
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            rules_dir = root / "docs" / "agent-rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "INDEX.md").write_text(VALID_AGENT_RULE_FRONTMATTER, encoding="utf-8")
            write_enforced(root, "docs/agent-rules/INDEX.md")

            result = validation_main([])
            assert result == 0

    def test_validation_rejects_missing_agent_rule_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        check_doc_frontmatter_module: CheckDocFrontmatterModule,
    ) -> None:
        validation_main = check_doc_frontmatter_module.main
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            monkeypatch.setenv("DOC_FRONTMATTER_ROOT", str(root))
            rules_dir = root / "docs" / "agent-rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "INDEX.md").write_text(
                """---
title: "Agent Rules Index"
id: agent-rules-index
doc_owner: specfact-cli
tracks:
  - AGENTS.md
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
always_load: true
priority: 0
blocking: true
user_interaction_required: false
stop_conditions:
  - canonical rule index missing
depends_on: []
---

# Agent Rules Index
""",
                encoding="utf-8",
            )
            write_enforced(root, "docs/agent-rules/INDEX.md")

            result = validation_main([])
            assert result != 0
            err = capsys.readouterr().err
            assert "docs/agent-rules/INDEX.md" in err
            assert "applies_when" in err
