"""Tests for patch-mode module (spec: patch-mode — previewable, confirmable)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner


pytest.importorskip("specfact_govern.patch_mode.patch_mode.commands.apply")
from specfact_govern.patch_mode.patch_mode.commands.apply import app as patch_app
from specfact_govern.patch_mode.patch_mode.pipeline.applier import (
    apply_patch_local,
    apply_patch_write,
    preflight_check,
)
from specfact_govern.patch_mode.patch_mode.pipeline.generator import generate_unified_diff
from specfact_govern.patch_mode.patch_mode.pipeline.idempotency import check_idempotent, mark_applied


runner = CliRunner()


class TestGenerateUnifiedDiff:
    """Scenario: Generate patch from backlog refine (emit file, no apply)."""

    def test_generate_returns_string(self) -> None:
        """Given content, When generate_unified_diff, Then returns non-empty string."""
        out = generate_unified_diff("line1\nline2\n", description="test")
        assert isinstance(out, str)
        assert "test" in out or "+line1" in out

    def test_generate_with_target_path(self) -> None:
        """Given target path, When generate_unified_diff, Then result mentions path."""
        out = generate_unified_diff("content", target_path=Path("/tmp/foo"))
        assert "/tmp/foo" in out or "foo" in out

    def test_generate_contains_unified_hunk_header(self) -> None:
        """Given content, When generate_unified_diff, Then emits valid unified hunk metadata."""
        out = generate_unified_diff("line1\nline2\n", target_path=Path("demo.txt"))
        assert out.startswith("--- /dev/null\n+++ b/demo.txt\n")
        assert "@@ -0,0 +1,2 @@" in out

    def test_generated_diff_is_applicable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given generated unified diff, When apply_patch_local, Then git apply accepts and creates file."""
        patch_file = tmp_path / "gen.diff"
        patch_file.write_text(
            generate_unified_diff("hello\nworld\n", target_path=Path("newfile.txt")), encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_local(patch_file, dry_run=False) is True
        assert (tmp_path / "newfile.txt").read_text(encoding="utf-8") == "hello\nworld\n"


class TestApplyPatchLocal:
    """Scenario: Apply patch locally with preflight; no upstream write."""

    def test_apply_local_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given a patch file, When patch apply <file>, Then applies locally; no upstream."""
        target = tmp_path / "sample.txt"
        target.write_text("old\n", encoding="utf-8")
        patch_file = tmp_path / "p.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-old
+new
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(patch_app, [str(patch_file)], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Applied patch locally" in result.stdout or "apply" in result.stdout.lower()

    def test_apply_local_dry_run(self, tmp_path: Path) -> None:
        """Given a patch file, When patch apply --dry-run <file>, Then preflight only."""
        patch_file = tmp_path / "p.diff"
        patch_file.write_text("+line\n")
        result = runner.invoke(patch_app, [str(patch_file), "--dry-run"])
        assert result.exit_code == 0

    def test_preflight_check_empty_fails(self, tmp_path: Path) -> None:
        """Given empty patch file, When preflight_check, Then False."""
        f = tmp_path / "empty.diff"
        f.write_text("")
        assert preflight_check(f) is False

    def test_apply_patch_local_returns_true_for_valid_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given valid patch file, When apply_patch_local, Then returns True."""
        target = tmp_path / "sample.txt"
        target.write_text("before\n", encoding="utf-8")
        patch_file = tmp_path / "x.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-before
+after
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_local(patch_file, dry_run=False) is True

    def test_apply_patch_local_applies_real_file_change(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given valid unified diff, When apply_patch_local, Then target file content changes."""
        target = tmp_path / "sample.txt"
        target.write_text("hello\n", encoding="utf-8")
        patch_file = tmp_path / "real.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-hello
+hi
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_local(patch_file, dry_run=False) is True
        assert target.read_text(encoding="utf-8") == "hi\n"

    def test_apply_patch_local_returns_false_on_invalid_patch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given invalid patch, When apply_patch_local, Then returns False."""
        target = tmp_path / "sample.txt"
        target.write_text("hello\n", encoding="utf-8")
        patch_file = tmp_path / "invalid.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-does-not-match
+hi
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_local(patch_file, dry_run=False) is False


class TestApplyPatchWrite:
    """Scenario: Write patch upstream with explicit confirmation; idempotent."""

    def test_apply_write_without_yes_skips(self, tmp_path: Path) -> None:
        """Given patch file, When patch apply --write without --yes, Then no write."""
        patch_file = tmp_path / "w.diff"
        patch_file.write_text("+line\n")
        result = runner.invoke(patch_app, [str(patch_file), "--write"])
        assert result.exit_code == 0
        assert "skip" in result.stdout.lower() or "yes" in result.stdout.lower()

    def test_apply_write_with_yes_succeeds(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given patch file, When patch apply --write --yes, Then updates upstream (idempotent)."""
        target = tmp_path / "sample.txt"
        target.write_text("old\n", encoding="utf-8")
        patch_file = tmp_path / "w.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-old
+new
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(patch_app, [str(patch_file), "--write", "--yes"])
        assert result.exit_code == 0
        assert "Wrote" in result.stdout or "write" in result.stdout.lower() or "Applied" in result.stdout

    def test_apply_patch_write_confirmed_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """apply_patch_write with confirmed=True and valid file returns True."""
        target = tmp_path / "sample.txt"
        target.write_text("base\n", encoding="utf-8")
        patch_file = tmp_path / "z.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-base
+updated
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_write(patch_file, confirmed=True) is True
        assert target.read_text(encoding="utf-8") == "updated\n"

    def test_apply_patch_write_returns_false_on_invalid_patch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """apply_patch_write fails when orchestration preflight fails."""
        target = tmp_path / "sample.txt"
        target.write_text("hello\n", encoding="utf-8")
        patch_file = tmp_path / "bad.diff"
        patch_file.write_text(
            """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-wrong
+updated
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert apply_patch_write(patch_file, confirmed=True) is False


class TestIdempotency:
    """Idempotent: no duplicate posted comments/updates."""

    def test_check_idempotent_false_when_not_marked(self, tmp_path: Path) -> None:
        """Given key not marked, When check_idempotent, Then False."""
        assert check_idempotent("unique-key-123", state_dir=tmp_path) is False

    def test_mark_applied_then_check_idempotent_true(self, tmp_path: Path) -> None:
        """Given key marked applied, When check_idempotent, Then True."""
        mark_applied("key-xyz", state_dir=tmp_path)
        assert check_idempotent("key-xyz", state_dir=tmp_path) is True

    def test_idempotency_key_sanitized_under_state_dir(self, tmp_path: Path) -> None:
        """Absolute path key is hashed so marker lives under state_dir, not key path."""
        import hashlib

        key = "/tmp/foo.diff"
        mark_applied(key, state_dir=tmp_path)
        assert check_idempotent(key, state_dir=tmp_path) is True
        markers = list(tmp_path.glob("*.applied"))
        assert len(markers) == 1
        assert markers[0].parent == tmp_path
        expected_name = hashlib.sha256(key.encode()).hexdigest() + ".applied"
        assert markers[0].name == expected_name
