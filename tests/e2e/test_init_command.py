"""End-to-end tests for specfact init command (IDE integration)."""

import os

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestInitCommandE2E:
    """End-to-end tests for specfact init command."""

    def test_init_auto_detect_cursor(self, tmp_path, monkeypatch):
        """Test init command with auto-detection (simulating Cursor)."""
        # Mock Cursor environment variables
        monkeypatch.setenv("CURSOR_AGENT", "1")
        monkeypatch.setenv("CURSOR_TRACE_ID", "test-trace-id")
        # Remove VS Code variables if present
        monkeypatch.delenv("VSCODE_PID", raising=False)
        monkeypatch.delenv("VSCODE_INJECTION", raising=False)

        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")
        (templates_dir / "specfact-plan-init.md").write_text("---\ndescription: Plan Init\n---\nContent")

        # Change to temp directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Cursor" in result.stdout
        assert ".cursor/commands/" in result.stdout

        # Verify templates were copied
        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact-import-from-code.md").exists()
        assert (cursor_dir / "specfact-plan-init.md").exists()

    def test_init_explicit_cursor(self, tmp_path):
        """Test init command with explicit Cursor selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Cursor" in result.stdout
        assert ".cursor/commands/" in result.stdout

        # Verify template was copied
        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact-import-from-code.md").exists()

    def test_init_explicit_vscode(self, tmp_path):
        """Test init command with explicit VS Code selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "vscode", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "VS Code" in result.stdout
        assert ".github/prompts/" in result.stdout

        # Verify template was copied
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact-import-from-code.prompt.md").exists()

        # Verify VS Code settings were updated
        vscode_settings = tmp_path / ".vscode" / "settings.json"
        assert vscode_settings.exists()

    def test_init_explicit_copilot(self, tmp_path):
        """Test init command with explicit Copilot selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "copilot", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "GitHub Copilot" in result.stdout
        assert ".github/prompts/" in result.stdout

        # Verify template was copied
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact-import-from-code.prompt.md").exists()

    def test_init_skips_existing_files_without_force(self, tmp_path):
        """Test init command skips existing files without --force."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")
        (templates_dir / "specfact-plan-init.md").write_text("---\ndescription: Plan Init\n---\nContent")

        # Pre-create one file (but not all)
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact-import-from-code.md").write_text("existing content")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "cursor", "--repo", str(tmp_path)])
        finally:
            os.chdir(old_cwd)

        # Should succeed (may exit 0 or 1 depending on if any files were copied)
        assert result.exit_code in (0, 1)  # May exit 1 if no files copied, or 0 if some files copied
        assert (
            "Skipping" in result.stdout
            or "already exists" in result.stdout.lower()
            or "No templates copied" in result.stdout
        )
        # Verify existing file was not overwritten
        assert (cursor_dir / "specfact-import-from-code.md").read_text() == "existing content"

    def test_init_overwrites_with_force(self, tmp_path):
        """Test init command overwrites existing files with --force."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nNew content")

        # Pre-create one file
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact-import-from-code.md").write_text("existing content")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Verify file was overwritten (content should contain "New content" from template)
        content = (cursor_dir / "specfact-import-from-code.md").read_text()
        assert "New content" in content or "Analyze" in content

    def test_init_handles_missing_templates(self, tmp_path, monkeypatch):
        """Test init command handles missing templates directory gracefully."""
        # Mock importlib.util.find_spec to return None to simulate missing package
        import importlib.util

        original_find_spec = importlib.util.find_spec

        def mock_find_spec(name):
            if name == "specfact_cli":
                return None  # Simulate package not installed
            return original_find_spec(name)

        monkeypatch.setattr(importlib.util, "find_spec", mock_find_spec)

        # Mock get_package_installation_locations to return empty list to avoid slow search
        def mock_get_locations(package_name: str) -> list:
            return []  # Return empty to simulate no package found

        monkeypatch.setattr(
            "specfact_cli.utils.ide_setup.get_package_installation_locations",
            mock_get_locations,
        )

        # Mock find_package_resources_path to return None to avoid slow search
        def mock_find_resources(package_name: str, resource_subpath: str):
            return None  # Return None to simulate no resources found

        monkeypatch.setattr(
            "specfact_cli.utils.ide_setup.find_package_resources_path",
            mock_find_resources,
        )

        # Don't create templates directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--ide", "cursor", "--repo", str(tmp_path)])
        finally:
            os.chdir(old_cwd)

        # May find templates from installed package or fail - both are valid
        # If templates are found from package, it succeeds (exit 0)
        # If templates are not found at all, it fails (exit 1)
        if result.exit_code == 1:
            assert "Templates directory not found" in result.stdout or "Error" in result.stdout
        else:
            # If it succeeds, templates were found from installed package
            assert result.exit_code == 0

    def test_init_all_supported_ides(self, tmp_path):
        """Test init command works with all supported IDE types."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        supported_ides = ["cursor", "vscode", "copilot", "claude", "gemini", "qwen"]

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            for ide in supported_ides:
                # Clean up between tests
                for folder in [".cursor", ".github", ".claude", ".gemini", ".qwen"]:
                    ide_dir = tmp_path / folder
                    if ide_dir.exists():
                        import shutil

                        shutil.rmtree(ide_dir)

                result = runner.invoke(app, ["init", "--ide", ide, "--repo", str(tmp_path), "--force"])
                assert result.exit_code == 0, f"Failed for IDE: {ide}\n{result.stdout}\n{result.stderr}"
                assert "Initialization Complete" in result.stdout or "Copied" in result.stdout
        finally:
            os.chdir(old_cwd)

    def test_init_auto_detect_vscode(self, tmp_path, monkeypatch):
        """Test init command with auto-detection (simulating VS Code)."""
        # Mock VS Code environment variables
        monkeypatch.setenv("VSCODE_PID", "12345")
        # Remove Cursor variables if present
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CURSOR_INJECTION", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)

        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "VS Code" in result.stdout or "vscode" in result.stdout.lower()
        assert ".github/prompts/" in result.stdout

        # Verify templates were copied
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact-import-from-code.prompt.md").exists()

    def test_init_auto_detect_claude(self, tmp_path, monkeypatch):
        """Test init command with auto-detection (simulating Claude Code)."""
        # Mock Claude Code environment variables
        monkeypatch.setenv("CLAUDE_PID", "12345")
        # Remove other IDE variables
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CURSOR_INJECTION", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)
        monkeypatch.delenv("VSCODE_PID", raising=False)
        monkeypatch.delenv("VSCODE_INJECTION", raising=False)

        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Claude Code" in result.stdout or "claude" in result.stdout.lower()

        # Verify templates were copied
        claude_dir = tmp_path / ".claude" / "commands"
        assert claude_dir.exists()
        assert (claude_dir / "specfact-import-from-code.md").exists()
