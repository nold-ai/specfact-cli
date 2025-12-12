"""
Structured data I/O utilities for SpecFact CLI.

Provides helpers to load and dump JSON/YAML consistently with format detection.
"""

import json
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.yaml_utils import YAMLUtils


class StructuredFormat(str, Enum):
    """Supported structured data formats."""

    YAML = "yaml"
    JSON = "json"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value

    @classmethod
    @beartype
    def from_string(cls, value: str | None, default: Optional["StructuredFormat"] = None) -> "StructuredFormat":
        """
        Convert string to StructuredFormat (defaults to YAML).

        Args:
            value: String representation (json/yaml)
            default: Default format when value is None/empty
        """
        if not value:
            return StructuredFormat.YAML if default is None else default
        try:
            return StructuredFormat(value.lower())
        except ValueError as exc:  # pragma: no cover - guarded by Typer choices
            raise ValueError(f"Unsupported format: {value}") from exc

    @classmethod
    @beartype
    def from_path(cls, path: Path | str | None, default: Optional["StructuredFormat"] = None) -> "StructuredFormat":
        """
        Infer format from file path suffix.

        Args:
            path: Path or string with extension
            default: Fallback when extension is unknown
        """
        if path is None:
            return StructuredFormat.YAML if default is None else default

        suffixes = Path(path).suffixes
        for suffix in reversed(suffixes):
            lowered = suffix.lower()
            if lowered in (".yaml", ".yml"):
                return StructuredFormat.YAML
            if lowered == ".json":
                return StructuredFormat.JSON
        return StructuredFormat.YAML if default is None else default


# Thread-local storage for YAML instances to ensure thread-safety
# ruamel.yaml.YAML() is not thread-safe, so we create one per thread
_thread_local = threading.local()


def _get_yaml_instance() -> YAMLUtils:
    """Get thread-local YAML instance for thread-safe operations."""
    if not hasattr(_thread_local, "yaml"):
        _thread_local.yaml = YAMLUtils()
    return _thread_local.yaml


# Module-level instance for backward compatibility (single-threaded use)
_yaml = YAMLUtils()


@beartype
def structured_extension(format: StructuredFormat) -> str:
    """Return canonical file extension for structured format."""
    return ".json" if format == StructuredFormat.JSON else ".yaml"


@beartype
@require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
@ensure(lambda result: result is not None, "Must return parsed content")
def load_structured_file(file_path: Path | str, format: StructuredFormat | None = None) -> Any:
    """
    Load structured data (JSON or YAML) from file.

    Args:
        file_path: Path to file
        format: Optional explicit format. Auto-detected from suffix when omitted.
    """
    path = Path(file_path)
    # Check if path is a directory (should not happen, but handle gracefully)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"Cannot load structured file: path is a directory: {path}")
    fmt = format or StructuredFormat.from_path(path)

    if fmt == StructuredFormat.JSON:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    # Use thread-local YAML instance for thread-safety (though loading is less critical)
    yaml_instance = _get_yaml_instance()
    return yaml_instance.load(path)


@beartype
@require(lambda file_path: isinstance(file_path, (Path, str)), "File path must be Path or str")
def dump_structured_file(data: Any, file_path: Path | str, format: StructuredFormat | None = None) -> None:
    """
    Dump structured data (JSON or YAML) to file.

    Thread-safe: Uses thread-local YAML instance for parallel operations.

    Args:
        data: Serializable payload
        file_path: Destination path
        format: Optional explicit format (auto-detect by suffix when omitted)
    """
    path = Path(file_path)
    fmt = format or StructuredFormat.from_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == StructuredFormat.JSON:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        # Use thread-local YAML instance for thread-safety
        # ruamel.yaml.YAML() is not thread-safe when used from multiple threads
        yaml_instance = _get_yaml_instance()
        yaml_instance.dump(data, path)


@beartype
@ensure(lambda result: isinstance(result, str), "Must return string output")
def dumps_structured_data(data: Any, format: StructuredFormat) -> str:
    """Serialize data to string for the requested structured format."""
    if format == StructuredFormat.JSON:
        return json.dumps(data, indent=2)
    # Use thread-local YAML instance for thread-safety
    yaml_instance = _get_yaml_instance()
    return yaml_instance.dump_string(data)


@beartype
@require(lambda payload: isinstance(payload, str), "Payload must be string")
@ensure(lambda result: result is not None, "Must return parsed content")
def loads_structured_data(payload: str, format: StructuredFormat) -> Any:
    """Deserialize structured payload string."""
    if format == StructuredFormat.JSON:
        return json.loads(payload)
    # Use thread-local YAML instance for thread-safety
    yaml_instance = _get_yaml_instance()
    return yaml_instance.load_string(payload)
