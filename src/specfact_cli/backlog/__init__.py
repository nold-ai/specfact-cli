"""
Backlog refinement and template detection.

This module provides AI-assisted backlog refinement with template detection
and matching capabilities.
"""

from __future__ import annotations

from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.converter import (
    convert_ado_work_item_to_backlog_item,
    convert_github_issue_to_backlog_item,
)
from specfact_cli.backlog.template_detector import TemplateDetectionResult, TemplateDetector


__all__ = [
    "BacklogAIRefiner",
    "TemplateDetectionResult",
    "TemplateDetector",
    "convert_ado_work_item_to_backlog_item",
    "convert_github_issue_to_backlog_item",
]
