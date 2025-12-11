"""
Utility functions for validating and analyzing acceptance criteria.

This module provides shared logic for detecting code-specific acceptance criteria
to prevent false positives in ambiguity scanning and plan enrichment.
"""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda acceptance: isinstance(acceptance, str), "Acceptance must be string")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_simplified_format_criteria(acceptance: str) -> bool:
    """
    Check if acceptance criteria use the new simplified format (post-GWT refactoring).

    The new simplified format patterns include:
    - "Must verify X works correctly (see contract examples)"
    - "Must verify X works correctly"
    - Similar patterns with "verify", "validate", "check" + "works correctly" + optional "(see contract examples)"

    These are VALID and should NOT be flagged as vague, as they reference contract examples
    in OpenAPI files for detailed test cases.

    Args:
        acceptance: Acceptance criteria text to check

    Returns:
        True if criteria use the simplified format, False otherwise
    """
    acceptance_lower = acceptance.lower()

    # Pattern: "Must verify ... works correctly (see contract examples)"
    # or "Must verify ... works correctly"
    simplified_patterns = [
        r"must\s+verify.*works\s+correctly.*\(see\s+contract",
        r"must\s+verify.*works\s+correctly",
        r"verify.*works\s+correctly.*\(see\s+contract",
        r"validate.*works\s+correctly.*\(see\s+contract",
        r"check.*works\s+correctly.*\(see\s+contract",
    ]

    return any(re.search(pattern, acceptance_lower) for pattern in simplified_patterns)


@beartype
@require(lambda acceptance: isinstance(acceptance, str), "Acceptance must be string")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_code_specific_criteria(acceptance: str) -> bool:
    """
    Check if acceptance criteria are already code-specific (should not be replaced).

    Code-specific criteria contain:
    - Method signatures: method(), method(param: type)
    - Class names: ClassName, ClassName.method()
    - File paths: src/, path/to/file.py
    - Type hints: : Path, : str, -> bool
    - Specific return values: returns dict with 'key'
    - Specific assertions: ==, in, >=, <=

    Args:
        acceptance: Acceptance criteria text to check

    Returns:
        True if criteria are code-specific, False if vague/generic
    """
    acceptance_lower = acceptance.lower()

    # FIRST: Check for generic placeholders that indicate non-code-specific
    # If found, return False immediately (don't enrich)
    generic_placeholders = [
        "interact with the system",
        "perform the action",
        "access the system",
        "works correctly",
        "works as expected",
        "is functional and verified",
    ]

    if any(placeholder in acceptance_lower for placeholder in generic_placeholders):
        return False

    # SECOND: Check for vague patterns that should be enriched
    # Use word boundaries to avoid false positives (e.g., "works" in "workspace")
    vague_patterns = [
        r"\bis\s+implemented\b",
        r"\bis\s+functional\b",
        r"\bworks\b",  # Word boundary prevents matching "workspace", "framework", etc.
        r"\bis\s+done\b",
        r"\bis\s+complete\b",
        r"\bis\s+ready\b",
    ]
    if any(re.search(pattern, acceptance_lower) for pattern in vague_patterns):
        return False  # Not code-specific, should be enriched

    # THIRD: Check for code-specific indicators
    code_specific_patterns = [
        # Method signatures with parentheses
        r"\([^)]*\)",  # method() or method(param)
        r":\s*(path|str|int|bool|dict|list|tuple|set|float|bytes|any|none)",  # Type hints
        r"->\s*(path|str|int|bool|dict|list|tuple|set|float|bytes|any|none)",  # Return type hints
        # File paths
        r"src/",
        r"tests/",
        r"\.py",
        r"\.yaml",
        r"\.json",
        # Class names (PascalCase with method/dot, or in specific contexts)
        r"[A-Z][a-zA-Z0-9]*\.",
        r"[A-Z][a-zA-Z0-9]*\(",
        r"returns\s+[A-Z][a-zA-Z0-9]{3,}\b",  # Returns ClassName (4+ chars)
        r"instance\s+of\s+[A-Z][a-zA-Z0-9]{3,}\b",  # instance of ClassName
        r"\b[A-Z][a-zA-Z0-9]{4,}\b",  # Standalone class names (5+ chars, PascalCase) - avoids common words
        # Specific assertions
        r"==\s*['\"]",
        r"in\s*\(",
        r">=\s*\d",
        r"<=\s*\d",
        r"returns\s+(dict|list|tuple|set|str|int|bool|float)\s+with",
        r"returns\s+[A-Z][a-zA-Z0-9]*",  # Returns a class instance
        # NetworkX, Path.resolve(), etc.
        r"nx\.",
        r"Path\.",
        r"resolve\(\)",
        # Version strings, specific values
        r"version\s*=\s*['\"]",
        r"version\s*==\s*['\"]",
    ]

    for pattern in code_specific_patterns:
        if re.search(pattern, acceptance, re.IGNORECASE):
            # Verify match is not a common word
            matches = re.findall(pattern, acceptance, re.IGNORECASE)
            common_words = [
                "given",
                "when",
                "then",
                "user",
                "system",
                "developer",
                "they",
                "the",
                "with",
                "from",
                "that",
            ]
            # Filter out common words from matches
            if isinstance(matches, list):
                actual_matches = [m for m in matches if isinstance(m, str) and m.lower() not in common_words]
            else:
                actual_matches = [matches] if isinstance(matches, str) and matches.lower() not in common_words else []

            if actual_matches:
                return True

    # If no code-specific patterns found, it's not code-specific
    return False
