"""Shared persona ownership helpers."""

from __future__ import annotations

import fnmatch
from typing import Any

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda section_pattern: isinstance(section_pattern, str), "Section pattern must be str")
@require(lambda path: isinstance(path, str), "Path must be str")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def match_section_pattern(section_pattern: str, path: str) -> bool:
    """Check if a path matches a section pattern."""
    pattern = section_pattern.replace(".*", "/*")
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, section_pattern)


@beartype
@require(lambda persona: isinstance(persona, str), "Persona must be str")
@require(lambda manifest: manifest is not None, "Manifest must be provided")
@require(lambda section_path: isinstance(section_path, str), "Section path must be str")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def check_persona_ownership(persona: str, manifest: Any, section_path: str) -> bool:
    """Check if persona owns a section."""
    personas = getattr(manifest, "personas", None)
    if not isinstance(personas, dict):
        return False
    if persona not in personas:
        return False

    persona_mapping = personas[persona]
    return any(match_section_pattern(pattern, section_path) for pattern in persona_mapping.owns)
