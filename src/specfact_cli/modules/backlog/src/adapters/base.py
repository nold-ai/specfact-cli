"""Shared mapping utilities for backlog bridge converters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


@beartype
class MappingBackedConverter:
    """Converter base class using key mapping definitions."""

    def __init__(
        self,
        *,
        service_name: str,
        default_to_bundle: dict[str, str],
        default_from_bundle: dict[str, str],
        mapping_file: str | None = None,
    ) -> None:
        self._logger = get_bridge_logger(__name__)
        self._service_name = service_name
        self._to_bundle_map = dict(default_to_bundle)
        self._from_bundle_map = dict(default_from_bundle)
        self._apply_mapping_override(mapping_file)

    @beartype
    def _apply_mapping_override(self, mapping_file: str | None) -> None:
        if mapping_file is None:
            return
        mapping_path: Path | None = None
        try:
            mapping_path = Path(mapping_file)
            raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("mapping file root must be a dictionary")
            to_bundle = raw.get("to_bundle")
            from_bundle = raw.get("from_bundle")
            if isinstance(to_bundle, dict):
                self._to_bundle_map.update({str(k): str(v) for k, v in to_bundle.items()})
            if isinstance(from_bundle, dict):
                self._from_bundle_map.update({str(k): str(v) for k, v in from_bundle.items()})
        except Exception as exc:
            self._logger.warning(
                "Backlog bridge '%s': invalid custom mapping '%s'; using defaults (%s)",
                self._service_name,
                mapping_path if mapping_path is not None else mapping_file,
                exc,
            )

    @staticmethod
    @beartype
    @require(lambda source_key: source_key.strip() != "", "Source key must not be empty")
    def _read_value(payload: dict[str, Any], source_key: str) -> Any:
        """Read value from payload by dotted source key."""
        if source_key in payload:
            return payload[source_key]
        current: Any = payload
        for part in source_key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Bundle payload must be a dictionary")
    def to_bundle(self, external_data: dict) -> dict:
        """Map external payload to bundle payload."""
        bundle: dict[str, Any] = {}
        for bundle_key, source_key in self._to_bundle_map.items():
            value = self._read_value(external_data, source_key)
            if value is not None:
                bundle[bundle_key] = value
        return bundle

    @beartype
    @ensure(lambda result: isinstance(result, dict), "External payload must be a dictionary")
    def from_bundle(self, bundle_data: dict) -> dict:
        """Map bundle payload to external payload."""
        external: dict[str, Any] = {}
        for source_key, bundle_key in self._from_bundle_map.items():
            value = bundle_data.get(bundle_key)
            if value is not None:
                external[source_key] = value
        return external
