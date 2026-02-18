"""Tests for patch-mode module (spec: patch-mode — previewable, confirmable)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.modules.patch_mode.src.patch_mode.pipeline.applier import (
    apply_patch_local,
    apply_patch_write,
    preflight_check,
)
from specfact_cli.modules.patch_mode.src.patch_mode.pipeline.generator import generate_unified_diff
from specfact_cli.modules.patch_mode.src.patch_mode.pipeline.idempotency import check_idempotent, mark_applied


runner = CliRunner()


class TestGenerateUnifiedDiff:
    """Scenario: Generate patch from backlog refine (emit file, no apply)."""

    def test_generate_returns_string(self) -> None:
        """Given content, When generate_unified_diff, Then returns non-empty string."""
        out = generate_unified_diff("+line1\n+line2\n", description="test")
        assert isinstance(out, str)
        assert "test" in out or "+line1" in out

    def test_generate_with_target_path(self) -> None:
        """Given target path, When generate_unified_diff, Then result mentions path."""
        out = generate_unified_diff("content", target_path=Path("/tmp/foo"))
        assert "/tmp/foo" in out or "foo" in out


class TestApplyPatchLocal:
    """Scenario: Apply patch locally with preflight; no upstream write."""

    def test_apply_local_success(self, tmp_path: Path) -> None:
        """Given a patch file, When patch apply <file>, Then applies locally; no upstream."""
        patch_file = tmp_path / "p.diff"
        patch_file.write_text("--- a\n+++ b\n+line\n")
        result = runner.invoke(app, ["patch", "apply", str(patch_file)])
        assert result.exit_code == 0
        assert "Applied patch locally" in result.stdout or "apply" in result.stdout.lower()

    def test_apply_local_dry_run(self, tmp_path: Path) -> None:
        """Given a patch file, When patch apply --dry-run <file>, Then preflight only."""
        patch_file = tmp_path / "p.diff"
        patch_file.write_text("+line\n")
        result = runner.invoke(app, ["patch", "apply", str(patch_file), "--dry-run"])
        assert result.exit_code == 0

    def test_preflight_check_empty_fails(self, tmp_path: Path) -> None:
        """Given empty patch file, When preflight_check, Then False."""
        f = tmp_path / "empty.diff"
        f.write_text("")
        assert preflight_check(f) is False

    def test_apply_patch_local_returns_true_for_valid_file(self, tmp_path: Path) -> None:
        """Given valid patch file, When apply_patch_local, Then returns True."""
        patch_file = tmp_path / "x.diff"
        patch_file.write_text("+content\n")
        assert apply_patch_local(patch_file, dry_run=False) is True


class TestApplyPatchWrite:
    """Scenario: Write patch upstream with explicit confirmation; idempotent."""

    def test_apply_write_without_yes_skips(self, tmp_path: Path) -> None:
        """Given patch file, When patch apply --write without --yes, Then no write."""
        patch_file = tmp_path / "w.diff"
        patch_file.write_text("+line\n")
        result = runner.invoke(app, ["patch", "apply", str(patch_file), "--write"])
        assert result.exit_code == 0
        assert "skip" in result.stdout.lower() or "yes" in result.stdout.lower()

    def test_apply_write_with_yes_succeeds(self, tmp_path: Path) -> None:
        """Given patch file, When patch apply --write --yes, Then updates upstream (idempotent)."""
        patch_file = tmp_path / "w.diff"
        patch_file.write_text("+line\n")
        result = runner.invoke(app, ["patch", "apply", str(patch_file), "--write", "--yes"])
        assert result.exit_code == 0
        assert "Wrote" in result.stdout or "write" in result.stdout.lower() or "Applied" in result.stdout

    def test_apply_patch_write_confirmed_success(self, tmp_path: Path) -> None:
        """apply_patch_write with confirmed=True and valid file returns True."""
        patch_file = tmp_path / "z.diff"
        patch_file.write_text("+content\n")
        assert apply_patch_write(patch_file, confirmed=True) is True


class TestIdempotency:
    """Idempotent: no duplicate posted comments/updates."""

    def test_check_idempotent_false_when_not_marked(self, tmp_path: Path) -> None:
        """Given key not marked, When check_idempotent, Then False."""
        assert check_idempotent("unique-key-123", state_dir=tmp_path) is False

    def test_mark_applied_then_check_idempotent_true(self, tmp_path: Path) -> None:
        """Given key marked applied, When check_idempotent, Then True."""
        mark_applied("key-xyz", state_dir=tmp_path)
        assert check_idempotent("key-xyz", state_dir=tmp_path) is True
