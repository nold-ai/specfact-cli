#!/usr/bin/env python3
"""Render deterministic SPDX 2.3 evidence from a local ``pip inspect`` report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, cast


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
    metadata = cast(dict[str, object], item).get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("pip inspect installed entries must contain metadata")
    typed_metadata = cast(dict[str, object], metadata)
    name = typed_metadata.get("name")
    version = typed_metadata.get("version")
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


def _append_native_inventory(sbom: dict[str, Any], inventory: dict[str, Any]) -> None:
    package_id = _package_identifier(inventory["name"])
    files = [
        {
            "SPDXID": f"SPDXRef-NativeFile-{index}",
            "fileName": "./native/" + item["path"],
            "checksums": [
                {"algorithm": "SHA256", "checksumValue": item["sha256"]},
                {"algorithm": "SHA1", "checksumValue": item["sha1"]},
            ],
            "licenseConcluded": "NOASSERTION",
            "licenseInfoInFiles": ["NOASSERTION"],
            "copyrightText": "NOASSERTION",
        }
        for index, item in enumerate(inventory["files"])
    ]
    sbom["files"] = files
    sbom["packages"].append(
        {
            "SPDXID": package_id,
            "name": inventory["name"],
            "versionInfo": inventory["version"],
            "supplier": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "sourceInfo": (
                "Verified extracted SDK composition; upstream Semgrep wheel "
                + inventory["artifact_url"]
                + " SHA256 "
                + inventory["artifact_sha256"]
                + "; vendor inputs "
                + json.dumps(inventory.get("vendor_artifacts", []), sort_keys=True)
            ),
            "filesAnalyzed": True,
            "packageVerificationCode": {
                "packageVerificationCodeValue": hashlib.sha1(
                    "".join(sorted(item["sha1"] for item in inventory["files"])).encode("ascii"),
                    usedforsecurity=False,
                ).hexdigest()
            },
            "licenseDeclared": "NOASSERTION",
            "licenseConcluded": "NOASSERTION",
            "licenseInfoFromFiles": ["NOASSERTION"],
            "copyrightText": "NOASSERTION",
            "comment": (
                f"Verified native composition for {inventory['platform']}; policy SHA256 {inventory['policy_sha256']}. "
                "THIRD_PARTY_NOTICES.html is supplier attribution, not a list of asserted installed packages. "
                "Upstream engine metadata declares LGPL-2.1-or-later; the composition includes other libraries. "
                "File-level NOASSERTION is not license or advisory clearance."
            ),
        }
    )
    sbom["documentDescribes"].append(package_id)
    relationships: list[dict[str, str]] = [
        {"spdxElementId": package_id, "relationshipType": "CONTAINS", "relatedSpdxElement": item["SPDXID"]}
        for item in files
    ]
    sbom["relationships"] = relationships
    _append_native_components(sbom, inventory, package_id, files)
    binding = json.dumps(
        {"python_namespace": sbom["documentNamespace"], "native": inventory},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    sbom["documentNamespace"] = "https://specfact.dev/sbom/locked-delivery/" + hashlib.sha256(binding).hexdigest()


def _append_native_components(
    sbom: dict[str, Any], inventory: dict[str, Any], package_id: str, files: list[dict[str, Any]]
) -> None:
    relationships: list[dict[str, str]] = sbom["relationships"]
    native_files: dict[str, dict[str, Any]] = {item["path"]: item for item in inventory["files"]}
    file_ids = {item["path"]: record["SPDXID"] for item, record in zip(inventory["files"], files, strict=True)}
    for index, component in enumerate(inventory.get("components", [])):
        component_id = f"SPDXRef-NativeComponent-{index}"
        record = {
            "SPDXID": component_id,
            "name": component["name"],
            "supplier": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "packageVerificationCode": {
                "packageVerificationCodeValue": hashlib.sha1(
                    "".join(sorted(native_files[path]["sha1"] for path in component["files"])).encode("ascii"),
                    usedforsecurity=False,
                ).hexdigest()
            },
            "licenseInfoFromFiles": ["NOASSERTION"],
            "licenseDeclared": "NOASSERTION",
            "licenseConcluded": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "sourceInfo": component["source_info"],
            "comment": "Retained notice paths: "
            + json.dumps(component["notice_paths"], sort_keys=True)
            + ". Notice references are not a conclusion of complete license or advisory coverage.",
        }
        if "version" in component:
            record["versionInfo"] = component["version"]
        sbom["packages"].append(record)
        relationships.append(
            {"spdxElementId": package_id, "relationshipType": "CONTAINS", "relatedSpdxElement": component_id}
        )
        relationships.extend(
            {"spdxElementId": component_id, "relationshipType": "CONTAINS", "relatedSpdxElement": file_ids[path]}
            for path in component["files"]
        )


def _native_inventory() -> dict[str, Any]:
    provider_path = Path(__file__).resolve().parents[1] / ".github/actions/setup-frozen-python/provision_semgrep.py"
    spec = importlib.util.spec_from_file_location("_delivery_native_provider", provider_path)
    if spec is None or spec.loader is None:
        raise ValueError("Native delivery provider is unavailable")
    provider = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = provider
    spec.loader.exec_module(provider)
    return provider._installed_inventory()


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
        _append_native_inventory(sbom, _native_inventory())
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
