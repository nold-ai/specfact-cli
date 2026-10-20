from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import TypeGuard

from scripts import candidate_runner as runner


BASE = Path(__file__).resolve().parents[3]


def _is_object_list(value: object) -> TypeGuard[list[dict[str, object]]]:
    return isinstance(value, list) and all(
        isinstance(item, dict) and all(isinstance(key, str) for key in item) for item in value
    )


class CandidateBoundaries(unittest.TestCase):
    def setUp(self) -> None:
        self.recipe = json.loads((BASE / "ci/semgrep-distribution.json").read_text())
        self.runtime = json.loads((BASE / "ci/semgrep-runtime.json").read_text())
        self.wheels: list[dict[str, str]] = [
            {
                "platform": w["platform_tag"],
                "filename": w["filename"].replace("semgrep-1.179.0-", "specfact_semgrep-1.179.0.post1-"),
                "sha256": str(i) * 64,
                "upstream_sha256": w["upstream_sha256"],
            }
            for i, w in enumerate(self.recipe["wheels"])
        ]
        self.manifest: dict[str, object] = {
            "source_commit": "a" * 40,
            "source_files": {"scripts/candidate_runner.py": "f" * 64},
            "recipe_sha256": "b" * 64,
            "runtime_sha256": "c" * 64,
            "wheels": self.wheels,
        }
        self.inventory = {
            "specfact-semgrep": "1.179.0.post1",
            "mcp": "1.30.0",
            "certifi": "2026.10.19",
        }

    def _matrix_cells(self) -> list[dict[str, object]]:
        cells = runner.matrix(self.recipe, self.runtime)["include"]
        assert _is_object_list(cells)
        return cells

    def reports(self) -> list[dict[str, object]]:
        wheels = {w["platform"]: w for w in self.wheels}
        reports: list[dict[str, object]] = []
        for cell in self._matrix_cells():
            platform = cell["platform"]
            python_version = cell["python_version"]
            assert isinstance(platform, str)
            assert isinstance(python_version, str)
            reports.append(
                {
                    "platform": platform,
                    "python_version": python_version,
                    "source_commit": self.manifest["source_commit"],
                    "source_files": self.manifest["source_files"],
                    "recipe_sha256": self.manifest["recipe_sha256"],
                    "runtime_sha256": self.manifest["runtime_sha256"],
                    "candidate_sha256": wheels[platform]["sha256"],
                    "upstream_sha256": wheels[platform]["upstream_sha256"],
                    "status": "runtime-passed",
                    "native": True,
                    "checks": dict.fromkeys(runner.CHECKS, True),
                    "actual_inventory": self.inventory,
                    "audit_status": "pending-unpublished-fork",
                    "pending": [
                        "actual-fork-advisory-lookup",
                        "core-installed-module-contract",
                    ],
                }
            )
        return reports

    def test_matrix_exact_seven_by_three(self) -> None:
        self.assertEqual(len(self._matrix_cells()), 21)

    def test_matrix_rejects_duplicate_missing_extra_platforms_and_versions(self) -> None:
        for field, value in [
            ("wheels", self.runtime["wheels"][:-1]),
            ("wheels", self.runtime["wheels"] + [self.runtime["wheels"][0]]),
            ("python_versions", ["3.11", "3.12"]),
            ("python_versions", ["3.11", "3.12", "3.13", "3.13"]),
        ]:
            runtime = copy.deepcopy(self.runtime)
            runtime[field] = value
            with (
                self.subTest(field=field, value=len(value)),
                self.assertRaises(ValueError),
            ):
                runner.matrix(self.recipe, runtime)

    def test_musl_images_must_have_exact_digests(self) -> None:
        self.runtime["wheels"][4]["containers"]["3.11"] = "python:3.11-alpine"
        with self.assertRaises(ValueError):
            runner.matrix(self.recipe, self.runtime)

    def test_host_rejects_wrong_arch_libc_and_python(self) -> None:
        observed = {
            "system": "Linux",
            "machine": "x86_64",
            "python_version": "3.13.7",
            "implementation": "CPython",
            "libc": ["glibc", "2.39"],
        }
        runner.validate_host("manylinux_2_34_x86_64", "3.13", observed)
        for tag, version in [
            ("manylinux_2_34_aarch64", "3.13"),
            ("musllinux_1_2_x86_64", "3.13"),
            ("manylinux_2_34_x86_64", "3.12"),
        ]:
            with self.subTest(tag=tag, version=version), self.assertRaises(ValueError):
                runner.validate_host(tag, version, observed)
        observed["libc"] = ["glibc", "2.33"]
        with self.assertRaises(ValueError):
            runner.validate_host("manylinux_2_34_x86_64", "3.13", observed)

    def test_hash_guard_rejects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wheel.whl"
            path.write_bytes(b"candidate")
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            runner.assert_hash(path, expected)
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                runner.assert_hash(path, expected)

    def test_inventory_normalization_rejects_duplicate_ownership(self) -> None:
        with self.assertRaises(ValueError):
            runner.normalize_inventory([{"name": "A_B", "version": "1"}, {"name": "a-b", "version": "1"}])
        with self.assertRaises(ValueError):
            runner.validate_inventory(dict(self.inventory, semgrep="1.179.0"))
        with self.assertRaises(ValueError):
            runner.validate_inventory(dict(self.inventory, mcp="1.29.0"))
        with self.assertRaises(ValueError):
            runner.validate_inventory(dict(self.inventory, certifi="2026.9.1"))

    def test_audit_exact_coverage_rejects_unknown_skips_missing_duplicates_and_vulns(
        self,
    ) -> None:
        dependencies: list[dict[str, object]] = [
            {"name": k, "version": v, "vulns": []} for k, v in self.inventory.items()
        ]
        runner.audit_coverage(self.inventory, {"dependencies": dependencies})
        bad: list[list[dict[str, object]]] = [
            dependencies[:-1],
            [*dependencies, dependencies[0]],
            [*dependencies, {"name": "extra", "version": "1", "vulns": []}],
        ]
        skipped = copy.deepcopy(dependencies)
        skipped[0]["skip_reason"] = "unknown package"
        bad.append(skipped)
        vulnerable = copy.deepcopy(dependencies)
        vulnerable[1]["vulns"] = [{"id": "CVE-test"}]
        bad.append(vulnerable)
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                runner.audit_coverage(self.inventory, {"dependencies": rows})

    def test_exact_aggregate_remains_prepublication(self) -> None:
        result = runner.aggregate(self.manifest, self.reports(), self.recipe, self.runtime)
        self.assertEqual(result["status"], "candidate-runtime-passed-publication-pending")
        pending = result["pending"]
        assert isinstance(pending, list)
        self.assertIn("actual-fork-advisory-lookup", pending)
        self.assertFalse(result["canonical_security_audit_passed"])

    def test_aggregate_rejects_missing_duplicate_and_mixed_evidence(self) -> None:
        reports = self.reports()
        bad = [reports[:-1], [*reports, reports[0]]]
        for field, value in [
            ("source_commit", "d" * 40),
            ("source_files", {}),
            ("recipe_sha256", "d" * 64),
            ("runtime_sha256", "d" * 64),
            ("candidate_sha256", "d" * 64),
            ("upstream_sha256", "d" * 64),
            ("native", False),
            ("status", "failed"),
        ]:
            changed = copy.deepcopy(reports)
            changed[0][field] = value
            bad.append(changed)
        for changed in bad:
            with (
                self.subTest(first=changed[0], count=len(changed)),
                self.assertRaises(ValueError),
            ):
                runner.aggregate(self.manifest, changed, self.recipe, self.runtime)

    def test_aggregate_rejects_missing_check(self) -> None:
        reports = self.reports()
        checks = reports[0]["checks"]
        assert isinstance(checks, dict)
        del checks["mcp_stdio"]
        with self.assertRaises(ValueError):
            runner.aggregate(self.manifest, reports, self.recipe, self.runtime)


if __name__ == "__main__":
    unittest.main()
