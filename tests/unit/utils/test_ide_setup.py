"""Unit tests for IDE setup utilities."""

from specfact_cli.utils.ide_setup import (
    copy_templates_to_ide,
    detect_ide,
    process_template,
    read_template,
)


class TestDetectIDE:
    """Test IDE detection logic."""

    def test_detect_ide_explicit(self):
        """Test explicit IDE selection."""
        assert detect_ide("cursor") == "cursor"
        assert detect_ide("vscode") == "vscode"
        assert detect_ide("copilot") == "copilot"

    def test_detect_ide_cursor_from_env(self, monkeypatch):
        """Test Cursor detection from environment variables."""
        monkeypatch.setenv("CURSOR_AGENT", "1")
        assert detect_ide("auto") == "cursor"

        monkeypatch.delenv("CURSOR_AGENT")
        monkeypatch.setenv("CURSOR_TRACE_ID", "test-id")
        assert detect_ide("auto") == "cursor"

        monkeypatch.delenv("CURSOR_TRACE_ID")
        monkeypatch.setenv("CURSOR_PID", "12345")
        assert detect_ide("auto") == "cursor"

        monkeypatch.delenv("CURSOR_PID")
        monkeypatch.setenv("CHROME_DESKTOP", "cursor.desktop")
        assert detect_ide("auto") == "cursor"

    def test_detect_ide_cursor_priority_over_vscode(self, monkeypatch):
        """Test Cursor detection takes priority over VS Code."""
        # Set both Cursor and VS Code variables
        monkeypatch.setenv("CURSOR_AGENT", "1")
        monkeypatch.setenv("VSCODE_PID", "12345")

        assert detect_ide("auto") == "cursor"

    def test_detect_ide_vscode_from_env(self, monkeypatch):
        """Test VS Code detection from environment variables."""
        # Ensure Cursor variables are not set
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)

        monkeypatch.setenv("VSCODE_PID", "12345")
        assert detect_ide("auto") == "vscode"

        monkeypatch.delenv("VSCODE_PID")
        monkeypatch.setenv("VSCODE_INJECTION", "test")
        assert detect_ide("auto") == "vscode"

    def test_detect_ide_claude_from_env(self, monkeypatch):
        """Test Claude Code detection from environment variables."""
        # Ensure other IDE variables are not set
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CURSOR_INJECTION", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)
        monkeypatch.delenv("VSCODE_PID", raising=False)

        monkeypatch.setenv("CLAUDE_PID", "12345")
        assert detect_ide("auto") == "claude"

    def test_detect_ide_defaults_to_vscode(self, monkeypatch):
        """Test detection defaults to VS Code when no IDE detected."""
        # Remove all IDE variables
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CURSOR_INJECTION", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)
        monkeypatch.delenv("VSCODE_PID", raising=False)
        monkeypatch.delenv("VSCODE_INJECTION", raising=False)
        monkeypatch.delenv("CLAUDE_PID", raising=False)

        assert detect_ide("auto") == "vscode"


class TestReadTemplate:
    """Test template reading functionality."""

    def test_read_template_with_frontmatter(self, tmp_path):
        """Test reading template with YAML frontmatter."""
        template_file = tmp_path / "test.md"
        template_file.write_text("---\ndescription: Test description\n---\n\n# Template Content\nSome content here.")

        result = read_template(template_file)

        assert result["description"] == "Test description"
        assert "# Template Content" in result["content"]
        assert "Some content here" in result["content"]

    def test_read_template_without_frontmatter(self, tmp_path):
        """Test reading template without YAML frontmatter."""
        template_file = tmp_path / "test.md"
        template_file.write_text("# Template Content\nSome content here.")

        result = read_template(template_file)

        assert result["description"] == ""
        assert "# Template Content" in result["content"]
        assert "Some content here" in result["content"]


class TestProcessTemplate:
    """Test template processing functionality."""

    def test_process_template_markdown(self):
        """Test processing template for Markdown format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "md")

        assert "# Title" in result
        assert "$ARGUMENTS" in result
        assert "Some content" in result

    def test_process_template_toml(self):
        """Test processing template for TOML format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "toml")

        assert 'description = "Test description"' in result
        assert 'prompt = """' in result
        assert "{{args}}" in result  # $ARGUMENTS replaced with {{args}}
        assert "# Title" in result

    def test_process_template_prompt_md(self):
        """Test processing template for prompt.md format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "prompt.md")

        assert "# Title" in result
        assert "$ARGUMENTS" in result
        assert "Some content" in result


class TestCopyTemplatesToIDE:
    """Test template copying functionality."""

    def test_copy_templates_to_cursor(self, tmp_path):
        """Test copying templates to Cursor directory."""
        # Create templates directory
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text(
            "---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS"
        )

        # Copy templates
        copied_files, settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=True)

        # Verify files were copied
        assert len(copied_files) == 1
        assert settings_path is None  # Cursor doesn't use settings file

        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact-import-from-code.md").exists()

        # Verify content
        content = (cursor_dir / "specfact-import-from-code.md").read_text()
        assert "# Analyze" in content
        assert "$ARGUMENTS" in content

    def test_copy_templates_to_vscode(self, tmp_path):
        """Test copying templates to VS Code directory with settings."""
        # Create templates directory
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text(
            "---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS"
        )

        # Copy templates
        copied_files, settings_path = copy_templates_to_ide(tmp_path, "vscode", templates_dir, force=True)

        # Verify files were copied
        assert len(copied_files) == 1
        assert settings_path is not None
        assert settings_path.exists()

        # Verify template copied with .prompt.md extension
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact-import-from-code.prompt.md").exists()

        # Verify VS Code settings created
        assert (tmp_path / ".vscode" / "settings.json").exists()

    def test_copy_templates_skips_existing_without_force(self, tmp_path):
        """Test copying templates skips existing files without force."""
        # Create templates directory
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text(
            "---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS"
        )

        # Pre-create file
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact-import-from-code.md").write_text("existing")

        # Try to copy without force
        copied_files, settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=False)

        # Should skip existing file
        assert len(copied_files) == 0

        # Verify existing file was not overwritten
        assert (cursor_dir / "specfact-import-from-code.md").read_text() == "existing"

    def test_copy_templates_overwrites_with_force(self, tmp_path):
        """Test copying templates overwrites existing files with force."""
        # Create templates directory
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact-import-from-code.md").write_text(
            "---\ndescription: Analyze\n---\n# New Content\n$ARGUMENTS"
        )

        # Pre-create file
        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact-import-from-code.md").write_text("existing")

        # Copy with force
        copied_files, settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=True)

        # Should have copied file
        assert len(copied_files) == 1

        # Verify file was overwritten
        content = (cursor_dir / "specfact-import-from-code.md").read_text()
        assert "New Content" in content or "# New Content" in content
