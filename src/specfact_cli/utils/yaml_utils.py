"""
YAML utilities.

This module provides helpers for YAML parsing and serialization.

CrossHair: skip (ruamel.yaml initialization performs plugin filesystem discovery)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


class YAMLUtils:
    """Helper class for YAML operations."""

    @beartype
    @require(lambda indent_mapping: indent_mapping > 0, "Indent mapping must be positive")
    @require(lambda indent_sequence: indent_sequence > 0, "Indent sequence must be positive")
    def __init__(self, preserve_quotes: bool = True, indent_mapping: int = 2, indent_sequence: int = 2) -> None:
        """
        Initialize YAML utilities.

        Args:
            preserve_quotes: Whether to preserve quotes in strings
            indent_mapping: Indentation for mappings (must be > 0)
            indent_sequence: Indentation for sequences (must be > 0)
        """
        self.preserve_quotes = preserve_quotes
        self.indent_mapping = indent_mapping
        self.indent_sequence = indent_sequence
        self.yaml = self._new_yaml()

    def _new_yaml(self) -> YAML:
        """Return a fresh ruamel YAML writer/reader for one operation."""
        yaml = YAML()
        yaml.preserve_quotes = self.preserve_quotes
        cast(Any, yaml).indent(mapping=self.indent_mapping, sequence=self.indent_sequence)
        yaml.default_flow_style = False
        # Configure to quote boolean-like strings to prevent YAML parsing issues
        # YAML parsers interpret "Yes", "No", "True", "False", "On", "Off" as booleans
        yaml.default_style = None  # Let ruamel.yaml decide, but we'll quote manually
        return yaml

    @beartype
    @require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
    @ensure(lambda result: result is not None, "Must return parsed content")
    def load(self, file_path: Path | str) -> Any:
        """
        Load YAML from file.

        Args:
            file_path: Path to YAML file (must exist)

        Returns:
            Parsed YAML content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        yaml = self._new_yaml()
        with open(file_path, encoding="utf-8") as f:
            loader = cast(Callable[[Any], Any], yaml.load)
            return loader(f)

    @beartype
    @require(lambda yaml_string: isinstance(yaml_string, str), "YAML string must be str")
    @ensure(lambda result: result is not None, "Must return parsed content")
    def load_string(self, yaml_string: str) -> Any:
        """
        Load YAML from string.

        Args:
            yaml_string: YAML content as string

        Returns:
            Parsed YAML content
        """
        yaml = self._new_yaml()
        loader = cast(Callable[[Any], Any], yaml.load)
        return loader(yaml_string)

    @beartype
    @require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
    def dump(self, data: Any, file_path: Path | str) -> None:
        """
        Dump data to YAML file.

        Args:
            data: Data to serialize
            file_path: Output file path
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Quote boolean-like strings to prevent YAML parsing issues
        data = self._quote_boolean_like_strings(data)

        # Use context manager for proper file handling
        # Thread-local YAML instances ensure thread-safety
        yaml = self._new_yaml()
        with open(file_path, "w", encoding="utf-8") as f:
            dumper = cast(Callable[..., None], yaml.dump)
            dumper(data, f)
            # Explicit flush to ensure data is written before context exits
            # This helps prevent "I/O operation on closed file" errors in parallel operations
            f.flush()

    @beartype
    def _quote_boolean_like_strings(self, data: Any) -> Any:
        """
        Recursively quote boolean-like strings to prevent YAML parsing issues.

        YAML parsers interpret "Yes", "No", "True", "False", "On", "Off" as booleans
        unless they're quoted. This function ensures these values are quoted.

        Optimized: early exit for simple types, avoids unnecessary recursion overhead.
        For large structures (>100 items), processes directly without pre-check to avoid
        double traversal overhead.

        Args:
            data: Data structure to process

        Returns:
            Data structure with boolean-like strings quoted
        """
        boolean_like_strings = {"yes", "no", "true", "false", "on", "off", "Yes", "No", "True", "False", "On", "Off"}

        if isinstance(data, str):
            return DoubleQuotedScalarString(data) if data in boolean_like_strings else data
        if isinstance(data, dict):
            return self._quote_dict_boolean_like(data, boolean_like_strings)
        if isinstance(data, list):
            return self._quote_list_boolean_like(data, boolean_like_strings)
        return data

    def _quote_dict_boolean_like(self, data: dict[Any, Any], boolean_like_strings: set[str]) -> dict[Any, Any]:
        if len(data) > 100:
            return {k: self._quote_boolean_like_strings(v) for k, v in data.items()}
        needs_processing = any(
            (isinstance(v, str) and v in boolean_like_strings) or isinstance(v, (dict, list)) for v in data.values()
        )
        if not needs_processing:
            return data
        return {k: self._quote_boolean_like_strings(v) for k, v in data.items()}

    def _quote_list_boolean_like(self, data: list[Any], boolean_like_strings: set[str]) -> list[Any]:
        if len(data) > 100:
            return [self._quote_boolean_like_strings(item) for item in data]
        needs_processing = any(
            (isinstance(item, str) and item in boolean_like_strings) or isinstance(item, (dict, list)) for item in data
        )
        if not needs_processing:
            return data
        return [self._quote_boolean_like_strings(item) for item in data]

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def dump_string(self, data: Any) -> str:
        """
        Dump data to YAML string.

        Args:
            data: Data to serialize

        Returns:
            YAML string
        """
        from io import StringIO

        yaml = self._new_yaml()
        stream = StringIO()
        dumper = cast(Callable[..., None], yaml.dump)
        dumper(data, stream)
        return stream.getvalue()

    @beartype
    @require(lambda base: isinstance(base, dict), "Base must be dictionary")
    @require(lambda overlay: isinstance(overlay, dict), "Overlay must be dictionary")
    @ensure(lambda result: isinstance(result, dict), "Must return dictionary")
    def merge_yaml(self, base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two YAML dictionaries.

        Args:
            base: Base dictionary
            overlay: Overlay dictionary (takes precedence)

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_yaml(result[key], value)
            else:
                result[key] = value

        return result


# Convenience functions for quick operations


@beartype
@require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
@ensure(lambda result: result is not None, "Must return parsed content")
def load_yaml(file_path: Path | str) -> Any:
    """
    Load YAML from file (convenience function).

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML content
    """
    utils = YAMLUtils()
    return utils.load(file_path)


@beartype
@require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
def dump_yaml(data: Any, file_path: Path | str) -> None:
    """
    Dump data to YAML file (convenience function).

    Args:
        data: Data to serialize
        file_path: Output file path
    """
    utils = YAMLUtils()
    utils.dump(data, file_path)


@beartype
@ensure(lambda result: isinstance(result, str), "Must return string")
def yaml_to_string(data: Any) -> str:
    """
    Convert data to YAML string (convenience function).

    Args:
        data: Data to serialize

    Returns:
        YAML string
    """
    utils = YAMLUtils()
    return utils.dump_string(data)


@beartype
@require(lambda yaml_string: isinstance(yaml_string, str), "YAML string must be str")
@ensure(lambda result: result is not None, "Must return parsed content")
def string_to_yaml(yaml_string: str) -> Any:
    """
    Parse YAML string (convenience function).

    Args:
        yaml_string: YAML content as string

    Returns:
        Parsed YAML content
    """
    utils = YAMLUtils()
    return utils.load_string(yaml_string)
