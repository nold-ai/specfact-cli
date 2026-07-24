#!/usr/bin/env python3
"""Render deterministic SPDX 2.3 evidence from a local ``pip inspect`` report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SPDX_CREATION_TIME = "1970-01-01T00:00:00Z"
SPDX_DOCUMENT_NAME = "specfact-cli-locked-delivery"


def _package_identifier(name: str) -> str:
    """Create a stable SPDX identifier from a Python distribution name."""
    normalized = re.sub(r"[^A-Za-z0-9.-]+", "-", name).strip("-")
    return f"SPDXRef-Package-{normalized or 'unnamed'}"


def _pypi_purl(name: str, version: str) -> str:
    """Return the normalized PyPI package URL used by SPDX external references."""
    normalized_name = re.sub(r"[-_.]+", "-", name).casefold()
    return f"pkg:pypi/{normalized_name}@{version}"


def _package_record(item: object) -> dict[str, str]:
    """Validate one installed-distribution record from ``pip inspect``."""
    if not isinstance(item, dict):
        raise ValueError("pip inspect installed entries must be objects")
    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("pip inspect installed entries must contain metadata")
    name = metadata.get("name")
    version = metadata.get("version")
    if not isinstance(name, str) or not name:
        raise ValueError("pip inspect package metadata.name must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ValueError("pip inspect package metadata.version must be a non-empty string")
    return {"name": name, "version": version}


def render_sbom(inspect_report: dict[str, object]) -> dict[str, object]:
    """Convert the installed distribution inventory into deterministic SPDX JSON."""
    installed = inspect_report.get("installed")
    if not isinstance(installed, list):
        raise ValueError("pip inspect report must contain an installed package list")

    records = sorted((_package_record(item) for item in installed), key=lambda item: item["name"].casefold())
    duplicate_names = [
        record["name"]
        for index, record in enumerate(records[1:], start=1)
        if record["name"].casefold() == records[index - 1]["name"].casefold()
    ]
    if duplicate_names:
        raise ValueError(f"pip inspect report contains duplicate package names: {', '.join(duplicate_names)}")

    inventory = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    inventory_digest = hashlib.sha256(inventory).hexdigest()
    packages = [
        {
            "SPDXID": _package_identifier(record["name"]),
            "copyrightText": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceLocator": _pypi_purl(record["name"], record["version"]),
                    "referenceType": "purl",
                }
            ],
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "name": record["name"],
            "supplier": "NOASSERTION",
            "versionInfo": record["version"],
        }
        for record in records
    ]
    return {
        "SPDXID": "SPDXRef-DOCUMENT",
        "creationInfo": {
            "created": SPDX_CREATION_TIME,
            "creators": ["Tool: specfact-cli render_locked_sbom.py"],
        },
        "dataLicense": "CC0-1.0",
        "documentDescribes": [package["SPDXID"] for package in packages],
        "documentNamespace": f"https://specfact.dev/sbom/locked-delivery/{inventory_digest}",
        "name": SPDX_DOCUMENT_NAME,
        "packages": packages,
        "spdxVersion": "SPDX-2.3",
    }


def main(argv: list[str] | None = None) -> int:
    """Render one SBOM file from one JSON report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", type=Path, required=True, dest="inspect_path")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        raw_payload: Any = json.loads(arguments.inspect_path.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValueError("pip inspect report must be a JSON object")
        sbom = render_sbom(raw_payload)
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
