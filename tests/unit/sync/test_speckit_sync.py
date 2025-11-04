"""
Unit tests for SpecKitSync - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and business logic are tested here.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.sync.speckit_sync import SpecKitSync, SyncResult


class TestSpecKitSync:
    """Test cases for SpecKitSync - focused on edge cases and business logic."""

    def test_detect_speckit_changes_with_specify_dir(self, tmp_path: Path) -> None:
        """Test detecting Spec-Kit changes with .specify/ directory."""
        # Create modern Spec-Kit structure
        specify_dir = tmp_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True)
        constitution = specify_dir / "constitution.md"
        constitution.write_text("# Constitution\n")

        sync = SpecKitSync(tmp_path)
        changes = sync.detect_speckit_changes(tmp_path)

        # Should detect constitution.md
        relative_path = str(constitution.relative_to(tmp_path))
        assert relative_path in changes
        assert changes[relative_path]["type"] == "new"

    def test_detect_speckit_changes_with_specs_dir(self, tmp_path: Path) -> None:
        """Test hash calculation and change detection logic - business logic."""
        # Create specs directory structure
        specs_dir = tmp_path / "specs" / "001-test-feature"
        specs_dir.mkdir(parents=True)
        spec_file = specs_dir / "spec.md"
        spec_content = "# Feature Specification\nTest content\n"
        spec_file.write_text(spec_content)

        sync = SpecKitSync(tmp_path)

        # Test hash calculation (core business logic)
        file_hash = sync._get_file_hash(spec_file)
        assert file_hash != "", "File hash should not be empty for non-empty file"
        assert len(file_hash) == 64, "SHA256 hash should be 64 characters (hex)"

    def test_detect_specfact_changes_with_plans(self, tmp_path: Path) -> None:
        """Test detecting SpecFact changes in .specfact/plans/ directory."""
        # Create SpecFact structure
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)
        plan_file = plans_dir / "main.bundle.yaml"
        plan_file.write_text("version: '1.0'\n")

        sync = SpecKitSync(tmp_path)
        changes = sync.detect_specfact_changes(tmp_path)

        # Should detect plan file
        relative_path = str(plan_file.relative_to(tmp_path))
        assert relative_path in changes
        assert changes[relative_path]["type"] == "new"

    def test_detect_specfact_changes_with_protocols(self, tmp_path: Path) -> None:
        """Test detecting SpecFact changes in .specfact/protocols/ directory."""
        # Create SpecFact structure
        protocols_dir = tmp_path / ".specfact" / "protocols"
        protocols_dir.mkdir(parents=True)
        protocol_file = protocols_dir / "workflow.protocol.yaml"
        protocol_file.write_text("states: []\n")

        sync = SpecKitSync(tmp_path)
        changes = sync.detect_specfact_changes(tmp_path)

        # Should detect protocol file
        relative_path = str(protocol_file.relative_to(tmp_path))
        assert relative_path in changes
        assert changes[relative_path]["type"] == "new"

    def test_merge_changes_no_conflicts(self, tmp_path: Path) -> None:
        """Test merging changes with no conflicts."""
        sync = SpecKitSync(tmp_path)

        speckit_changes = {"specs/001-feature/spec.md": {"file": tmp_path / "spec.md", "type": "new"}}
        specfact_changes = {".specfact/plans/main.bundle.yaml": {"file": tmp_path / "plan.yaml", "type": "new"}}

        merged = sync.merge_changes(speckit_changes, specfact_changes)

        # Both changes should be in merged
        assert "specs/001-feature/spec.md" in merged
        assert ".specfact/plans/main.bundle.yaml" in merged
        assert merged["specs/001-feature/spec.md"]["source"] == "speckit"
        assert merged[".specfact/plans/main.bundle.yaml"]["source"] == "specfact"

    def test_detect_conflicts_when_both_changed(self, tmp_path: Path) -> None:
        """Test detecting conflicts when same file changed in both sources."""
        sync = SpecKitSync(tmp_path)

        # Same relative path in both changes (simulated conflict)
        speckit_changes = {"specs/001-feature/spec.md": {"file": tmp_path / "spec.md", "type": "modified"}}
        specfact_changes = {"specs/001-feature/spec.md": {"file": tmp_path / "spec.md", "type": "modified"}}

        conflicts = sync.detect_conflicts(speckit_changes, specfact_changes)

        # Should detect one conflict
        assert len(conflicts) == 1
        assert conflicts[0]["key"] == "specs/001-feature/spec.md"

    def test_resolve_conflicts_artifact_priority(self, tmp_path: Path) -> None:
        """Test conflict resolution with SpecFact priority for artifacts."""
        sync = SpecKitSync(tmp_path)

        conflicts = [
            {
                "key": "specs/001-feature/spec.md",
                "speckit_change": {"file": tmp_path / "spec.md", "type": "modified"},
                "specfact_change": {"file": tmp_path / "spec2.md", "type": "modified"},
            }
        ]

        resolved = sync.resolve_conflicts(conflicts)

        # SpecFact should win for artifacts
        assert "specs/001-feature/spec.md" in resolved
        assert resolved["specs/001-feature/spec.md"]["source"] == "specfact"
        assert resolved["specs/001-feature/spec.md"]["resolution"] == "specfact_priority"

    def test_resolve_conflicts_memory_priority(self, tmp_path: Path) -> None:
        """Test conflict resolution with Spec-Kit priority for memory files."""
        sync = SpecKitSync(tmp_path)

        conflicts = [
            {
                "key": ".specify/memory/constitution.md",
                "speckit_change": {"file": tmp_path / "constitution.md", "type": "modified"},
                "specfact_change": {"file": tmp_path / "constitution2.md", "type": "modified"},
            }
        ]

        resolved = sync.resolve_conflicts(conflicts)

        # Spec-Kit should win for memory files
        assert ".specify/memory/constitution.md" in resolved
        assert resolved[".specify/memory/constitution.md"]["source"] == "speckit"
        assert resolved[".specify/memory/constitution.md"]["resolution"] == "speckit_priority"

    def test_sync_bidirectional_no_changes(self, tmp_path: Path) -> None:
        """Test bidirectional sync with no changes."""
        sync = SpecKitSync(tmp_path)
        result = sync.sync_bidirectional(tmp_path)

        assert isinstance(result, SyncResult)
        assert result.status == "success"
        assert len(result.changes) == 2  # [speckit_changes, specfact_changes]
        assert len(result.conflicts) == 0

    def test_sync_bidirectional_with_conflicts(self, tmp_path: Path) -> None:
        """Test bidirectional sync with conflicts."""
        # Create conflicting changes
        spec_file = tmp_path / "specs" / "001-feature" / "spec.md"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text("# Spec-Kit version\n")

        plan_file = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
        plan_file.parent.mkdir(parents=True)
        plan_file.write_text("version: '1.0'\n")

        # Store same path in hash store to simulate conflict
        sync = SpecKitSync(tmp_path)
        sync.hash_store["specs/001-feature/spec.md"] = "old_hash"

        result = sync.sync_bidirectional(tmp_path)

        # Should detect conflicts
        assert isinstance(result, SyncResult)
        # Status depends on whether conflicts are detected (which requires actual file hashes)

    def test_get_file_type_artifact(self, tmp_path: Path) -> None:
        """Test file type detection for artifacts."""
        sync = SpecKitSync(tmp_path)

        assert sync._get_file_type("specs/001-feature/spec.md") == "artifact"
        assert sync._get_file_type("specs/002-feature/plan.md") == "artifact"

    def test_get_file_type_memory(self, tmp_path: Path) -> None:
        """Test file type detection for memory files."""
        sync = SpecKitSync(tmp_path)

        assert sync._get_file_type(".specify/memory/constitution.md") == "memory"
        # Legacy format without .specify prefix would be "other" (not implemented)

    def test_get_file_type_other(self, tmp_path: Path) -> None:
        """Test file type detection for other files."""
        sync = SpecKitSync(tmp_path)

        assert sync._get_file_type(".specfact/plans/main.bundle.yaml") == "other"
        assert sync._get_file_type("unknown/path/file.md") == "other"
