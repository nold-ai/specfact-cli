"""
Content sanitizer for OpenSpec change proposals.

This module provides utilities to sanitize OpenSpec change proposal content
for public consumption, removing internal/competitive information while
preserving user-facing value propositions.
"""

from __future__ import annotations

import re
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


class ContentSanitizer:
    """
    Sanitize OpenSpec change proposal content for public issues.

    Removes internal/competitive information while preserving user-facing
    value propositions, feature descriptions, and acceptance criteria.
    """

    # Patterns for sections to remove
    _REMOVE_PATTERNS = [
        r"(?i)##\s*Competitive\s+Analysis.*?(?=##|\Z)",
        r"(?i)##\s*Market\s+Positioning.*?(?=##|\Z)",
        r"(?i)##\s*Implementation\s+Details.*?(?=##|\Z)",
        r"(?i)##\s*File-by-File\s+Changes.*?(?=##|\Z)",
        r"(?i)##\s*Effort\s+Estimate.*?(?=##|\Z)",
        r"(?i)##\s*Timeline.*?(?=##|\Z)",
        r"(?i)##\s*Technical\s+Architecture.*?(?=##|\Z)",
        r"(?i)##\s*Internal\s+Strategy.*?(?=##|\Z)",
    ]

    # Patterns for content to remove within sections
    _REMOVE_CONTENT_PATTERNS = [
        r"(?i)competitive\s+advantage",
        r"(?i)market\s+position",
        r"(?i)implementation\s+file:",
        r"(?i)effort:\s*\d+",
        r"(?i)timeline:\s*\d+",
    ]

    @beartype
    @require(lambda proposal_content: isinstance(proposal_content, str), "Proposal content must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def sanitize_proposal(self, proposal_content: str) -> str:
        """
        Sanitize change proposal content for public consumption.

        Removes:
        - Competitive analysis sections
        - Market positioning statements
        - Implementation details (file-by-file changes)
        - Effort estimates and timelines
        - Technical architecture details
        - Internal strategy sections

        Preserves:
        - User-facing value propositions
        - High-level feature descriptions
        - Acceptance criteria (user-facing)
        - External documentation links

        Args:
            proposal_content: Original proposal markdown content

        Returns:
            Sanitized proposal content
        """
        sanitized = proposal_content

        # Remove entire sections
        for pattern in self._REMOVE_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.DOTALL)

        # Remove content patterns within remaining sections
        for pattern in self._REMOVE_CONTENT_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Clean up extra whitespace
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)  # Max 2 consecutive newlines

        return sanitized.strip()

    @beartype
    @require(lambda code_repo: isinstance(code_repo, Path) or code_repo is None, "Code repo must be Path or None")
    @require(
        lambda planning_repo: isinstance(planning_repo, Path) or planning_repo is None,
        "Planning repo must be Path or None",
    )
    @require(
        lambda user_preference: isinstance(user_preference, bool) or user_preference is None,
        "User preference must be bool or None",
    )
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect_sanitization_need(
        self,
        code_repo: Path | None = None,
        planning_repo: Path | None = None,
        user_preference: bool | None = None,
    ) -> bool:
        """
        Detect if sanitization is needed based on repository setup and user preference.

        Logic:
        1. If user explicitly requests sanitization (`user_preference=True`), sanitize
        2. If user explicitly requests no sanitization (`user_preference=False`), don't sanitize
        3. If code repo != planning repo, default to sanitize
        4. If same repo, default to no sanitization

        Args:
            code_repo: Path to code repository (optional)
            planning_repo: Path to planning repository (optional)
            user_preference: Explicit user preference (True=sanitize, False=don't, None=auto-detect)

        Returns:
            True if sanitization needed, False otherwise
        """
        # User preference takes precedence
        if user_preference is not None:
            return user_preference

        # Auto-detect based on repository setup
        if code_repo is None or planning_repo is None:
            # Can't determine, default to sanitize for safety
            return True

        # Normalize paths for comparison
        try:
            code_repo_resolved = code_repo.resolve()
            planning_repo_resolved = planning_repo.resolve()
            return code_repo_resolved != planning_repo_resolved
        except Exception:
            # If resolution fails, default to sanitize for safety
            return True
