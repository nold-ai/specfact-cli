"""End-to-end tests for specfact init command (IDE integration)."""

import os

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_user_prompt_modules_for_init_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not pick up ~/.specfact/modules prompt bundles; tests use repo ``resources/prompts`` only."""
    import specfact_cli.utils.ide_setup as ide_setup_module

    monkeypatch.setattr(ide_setup_module, "_module_prompt_sources_catalog", lambda _rp: {})


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
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")
        (templates_dir / "specfact.02-plan.md").write_text("---\ndescription: Plan Init\n---\nContent")

        # Change to temp directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Cursor" in result.stdout
        assert ".cursor/commands/" in result.stdout

        # Verify templates were copied (flat layout under the IDE export root)
        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact.01-import.md").exists()
        assert (cursor_dir / "specfact.02-plan.md").exists()

    def test_init_explicit_cursor(self, tmp_path):
        """Test init command with explicit Cursor selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Cursor" in result.stdout
        assert ".cursor/commands/" in result.stdout

        # Verify template was copied (flat layout)
        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact.01-import.md").exists()

    def test_init_explicit_vscode(self, tmp_path):
        """Test init command with explicit VS Code selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "vscode", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "VS Code" in result.stdout
        assert ".github/prompts/" in result.stdout

        # Verify template was copied (flat layout)
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact.01-import.prompt.md").exists()

        # Verify VS Code settings were updated
        vscode_settings = tmp_path / ".vscode" / "settings.json"
        assert vscode_settings.exists()

    def test_init_explicit_copilot(self, tmp_path):
        """Test init command with explicit Copilot selection."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "copilot", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "GitHub Copilot" in result.stdout
        assert ".github/prompts/" in result.stdout

        # Verify template was copied (flat layout)
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact.01-import.prompt.md").exists()

    def test_init_skips_existing_files_without_force(self, tmp_path):
        """Test init command skips existing files without --force."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")
        (templates_dir / "specfact.02-plan.md").write_text("---\ndescription: Plan Init\n---\nContent")

        # Pre-create one exported file (flat path) but not all
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact.01-import.md").write_text("existing content")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path)])
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
        assert (cursor_dir / "specfact.01-import.md").read_text() == "existing content"

    def test_init_overwrites_with_force(self, tmp_path):
        """Test init command overwrites existing files with --force."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nNew content")

        # Pre-create one file under the flat export path
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact.01-import.md").write_text("existing content")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Verify file was overwritten (content should contain "New content" from template)
        content = (cursor_dir / "specfact.01-import.md").read_text()
        assert "New content" in content or "Analyze" in content

    def test_init_handles_missing_templates(self, tmp_path, monkeypatch):
        """Empty prompt catalog yields deterministic ``init ide`` failure messages."""
        monkeypatch.setattr(
            "specfact_cli.modules.init.src.commands.discover_prompt_sources_catalog",
            lambda _repo_path, include_package_fallback=True: {},
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path)])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        out = result.stdout
        assert "No prompt templates found" in out, out
        assert "Seed or install modules first" in out, out

    def test_init_all_supported_ides(self, tmp_path):
        """Test init command works with all supported IDE types."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

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

                result = runner.invoke(app, ["init", "ide", "--ide", ide, "--repo", str(tmp_path), "--force"])
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
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "VS Code" in result.stdout or "vscode" in result.stdout.lower()
        assert ".github/prompts/" in result.stdout

        # Verify templates were copied (flat layout)
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact.01-import.prompt.md").exists()

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
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Claude Code" in result.stdout or "claude" in result.stdout.lower()

        # Verify templates were copied (flat layout)
        claude_dir = tmp_path / ".claude" / "commands"
        assert claude_dir.exists()
        assert (claude_dir / "specfact.01-import.md").exists()

    def test_init_warns_when_no_environment_manager(self, tmp_path, monkeypatch):
        """Test init command shows warning when no environment manager is detected."""
        monkeypatch.setattr("shutil.which", lambda _name: None)

        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create empty directory (no pyproject.toml, no requirements.txt, no setup.py)
        # This should trigger the warning

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Should show warning about no environment manager
        assert "No Compatible Environment Manager Detected" in result.stdout
        assert "Supported tools:" in result.stdout
        assert "hatch" in result.stdout.lower()
        assert "poetry" in result.stdout.lower()
        assert "uv" in result.stdout.lower()
        assert "pip" in result.stdout.lower()

    def test_init_no_warning_with_hatch_project(self, tmp_path, monkeypatch):
        """Test init command does not show warning when hatch is detected."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create hatch project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"
version = "0.1.0"

[tool.hatch.build.targets.wheel]
packages = ["src/test_package"]
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Should NOT show warning
        assert "No Compatible Environment Manager Detected" not in result.stdout

    def test_init_copies_backlog_field_mapping_templates(self, tmp_path, monkeypatch):
        """Test that init command copies backlog field mapping templates."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create backlog field mapping templates in resources
        backlog_templates_dir = tmp_path / "resources" / "templates" / "backlog" / "field_mappings"
        backlog_templates_dir.mkdir(parents=True)
        (backlog_templates_dir / "ado_default.yaml").write_text(
            "framework: default\nfield_mappings:\n  System.Description: description\n"
        )
        (backlog_templates_dir / "ado_scrum.yaml").write_text(
            "framework: scrum\nfield_mappings:\n  System.Description: description\n"
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify templates were copied
        specfact_templates_dir = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings"
        assert specfact_templates_dir.exists()
        assert (specfact_templates_dir / "ado_default.yaml").exists()
        assert (specfact_templates_dir / "ado_scrum.yaml").exists()

    def test_init_skips_existing_backlog_templates(self, tmp_path, monkeypatch):
        """Test that init command skips copying if backlog templates already exist."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create backlog field mapping templates in resources
        backlog_templates_dir = tmp_path / "resources" / "templates" / "backlog" / "field_mappings"
        backlog_templates_dir.mkdir(parents=True)
        (backlog_templates_dir / "ado_default.yaml").write_text(
            "framework: default\nfield_mappings:\n  System.Description: description\n"
        )

        # Pre-create target directory with existing file
        specfact_templates_dir = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings"
        specfact_templates_dir.mkdir(parents=True)
        (specfact_templates_dir / "ado_default.yaml").write_text(
            "framework: custom\nfield_mappings:\n  Custom.Field: description\n"
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path)])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify existing file was NOT overwritten (should still have custom content)
        existing_file = specfact_templates_dir / "ado_default.yaml"
        assert existing_file.exists()
        content = existing_file.read_text()
        assert "Custom.Field" in content  # Original content preserved

    def test_init_force_overwrites_backlog_templates(self, tmp_path, monkeypatch):
        """Test that init command with --force overwrites existing backlog templates."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create backlog field mapping templates in resources
        backlog_templates_dir = tmp_path / "resources" / "templates" / "backlog" / "field_mappings"
        backlog_templates_dir.mkdir(parents=True)
        (backlog_templates_dir / "ado_default.yaml").write_text(
            "framework: default\nfield_mappings:\n  System.Description: description\n"
        )

        # Pre-create target directory with existing file
        specfact_templates_dir = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings"
        specfact_templates_dir.mkdir(parents=True)
        (specfact_templates_dir / "ado_default.yaml").write_text(
            "framework: custom\nfield_mappings:\n  Custom.Field: description\n"
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify file was overwritten with default content
        existing_file = specfact_templates_dir / "ado_default.yaml"
        assert existing_file.exists()
        content = existing_file.read_text()
        assert "System.Description" in content  # Default content
        assert "Custom.Field" not in content  # Original content replaced

    def test_init_no_warning_with_poetry_project(self, tmp_path, monkeypatch):
        """Test init command does not show warning when poetry is detected."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create poetry project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[tool.poetry]
name = "test-package"
version = "0.1.0"
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Should NOT show warning
        assert "No Compatible Environment Manager Detected" not in result.stdout

    def test_init_no_warning_with_pip_project(self, tmp_path, monkeypatch):
        """Test init command does not show warning when pip (requirements.txt) is detected."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create requirements.txt (pip project)
        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("requests>=2.0.0\n")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Should NOT show warning
        assert "No Compatible Environment Manager Detected" not in result.stdout

    def test_init_no_warning_with_uv_project(self, tmp_path, monkeypatch):
        """Test init command does not show warning when uv is detected."""
        # Create templates directory structure
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")

        # Create uv project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"
version = "0.1.0"

[tool.uv]
dev-dependencies = []
"""
        )

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Should NOT show warning
        assert "No Compatible Environment Manager Detected" not in result.stdout

    def test_init_no_warning_with_explicit_uv_env_manager(self, tmp_path, monkeypatch):
        """Explicit env manager selection should bypass unknown auto-detection warnings."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "init",
                    "ide",
                    "--ide",
                    "cursor",
                    "--repo",
                    str(tmp_path),
                    "--env-manager",
                    "uv",
                    "--force",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "No Compatible Environment Manager Detected" not in result.stdout
        assert "Environment manager:" in result.stdout
        assert "uv" in result.stdout

    def test_init_no_warning_with_rootless_monorepo_uv(self, tmp_path, monkeypatch):
        """Rootless monorepo package markers plus uv on PATH should avoid the unknown warning."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\nContent")
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text("[project]\nname = 'backend'\n", encoding="utf-8")
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["init", "ide", "--ide", "cursor", "--repo", str(tmp_path), "--force"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "No Compatible Environment Manager Detected" not in result.stdout
        assert "Environment manager:" in result.stdout
        assert "uv" in result.stdout
