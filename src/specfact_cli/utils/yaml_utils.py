"""
YAML utilities.

This module provides helpers for YAML parsing and serialization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from ruamel.yaml import YAML


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
        self.yaml = YAML()
        self.yaml.preserve_quotes = preserve_quotes
        self.yaml.indent(mapping=indent_mapping, sequence=indent_sequence)
        self.yaml.default_flow_style = False

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

        with open(file_path, encoding="utf-8") as f:
            return self.yaml.load(f)

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
        return self.yaml.load(yaml_string)

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

        with open(file_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

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

        stream = StringIO()
        self.yaml.dump(data, stream)
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
