"""Unit tests for IDE setup utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specfact_cli.utils.ide_setup import (
    PROMPT_SOURCE_CORE,
    SPECFACT_COMMANDS,
    _flat_export_glob_pattern_for_prune,
    _is_specfact_github_prompt_path,
    copy_templates_to_ide,
    create_vscode_settings,
    detect_ide,
    discover_prompt_template_files,
    expected_ide_prompt_export_paths,
    load_ide_prompt_export_source_ids,
    process_template,
    read_template,
    write_ide_prompt_export_state,
)


class TestDetectIDE:
    """Test IDE detection logic."""

    def test_detect_ide_explicit(self) -> None:
        """Test explicit IDE selection."""
        assert detect_ide("cursor") == "cursor"
        assert detect_ide("vscode") == "vscode"
        assert detect_ide("copilot") == "copilot"

    def test_detect_ide_cursor_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_detect_ide_cursor_priority_over_vscode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Cursor detection takes priority over VS Code."""
        monkeypatch.setenv("CURSOR_AGENT", "1")
        monkeypatch.setenv("VSCODE_PID", "12345")

        assert detect_ide("auto") == "cursor"

    def test_detect_ide_vscode_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test VS Code detection from environment variables."""
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)

        monkeypatch.setenv("VSCODE_PID", "12345")
        assert detect_ide("auto") == "vscode"

        monkeypatch.delenv("VSCODE_PID")
        monkeypatch.setenv("VSCODE_INJECTION", "test")
        assert detect_ide("auto") == "vscode"

    def test_detect_ide_claude_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Claude Code detection from environment variables."""
        monkeypatch.delenv("CURSOR_AGENT", raising=False)
        monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
        monkeypatch.delenv("CURSOR_PID", raising=False)
        monkeypatch.delenv("CURSOR_INJECTION", raising=False)
        monkeypatch.delenv("CHROME_DESKTOP", raising=False)
        monkeypatch.delenv("VSCODE_PID", raising=False)

        monkeypatch.setenv("CLAUDE_PID", "12345")
        assert detect_ide("auto") == "claude"

    def test_detect_ide_defaults_to_vscode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test detection defaults to VS Code when no IDE detected."""
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

    def test_read_template_with_frontmatter(self, tmp_path: Path) -> None:
        """Test reading template with YAML frontmatter."""
        template_file = tmp_path / "test.md"
        template_file.write_text("---\ndescription: Test description\n---\n\n# Template Content\nSome content here.")

        result = read_template(template_file)

        assert result["description"] == "Test description"
        assert "# Template Content" in result["content"]
        assert "Some content here" in result["content"]

    def test_read_template_without_frontmatter(self, tmp_path: Path) -> None:
        """Test reading template without YAML frontmatter."""
        template_file = tmp_path / "test.md"
        template_file.write_text("# Template Content\nSome content here.")

        result = read_template(template_file)

        assert result["description"] == ""
        assert "# Template Content" in result["content"]
        assert "Some content here" in result["content"]


class TestProcessTemplate:
    """Test template processing functionality."""

    def test_process_template_markdown(self) -> None:
        """Test processing template for Markdown format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "md")

        assert "# Title" in result
        assert "$ARGUMENTS" in result
        assert "Some content" in result

    def test_process_template_toml(self) -> None:
        """Test processing template for TOML format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "toml")

        assert 'description = "Test description"' in result
        assert 'prompt = """' in result
        assert "{{args}}" in result
        assert "# Title" in result

    def test_process_template_prompt_md(self) -> None:
        """Test processing template for prompt.md format."""
        content = "# Title\n$ARGUMENTS\nSome content"
        result = process_template(content, "Test description", "prompt.md")

        assert "# Title" in result
        assert "$ARGUMENTS" in result
        assert "Some content" in result


class TestCopyTemplatesToIDE:
    """Test template copying functionality."""

    def test_copy_templates_to_cursor(self, tmp_path: Path) -> None:
        """Test copying templates to Cursor directory."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS")

        copied_files, settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=True)

        assert len(copied_files) == 1
        assert settings_path is None

        cursor_dir = tmp_path / ".cursor" / "commands"
        assert cursor_dir.exists()
        assert (cursor_dir / "specfact.01-import.md").exists()

        content = (cursor_dir / "specfact.01-import.md").read_text()
        assert "# Analyze" in content
        assert "$ARGUMENTS" in content

    def test_copy_templates_to_vscode(self, tmp_path: Path) -> None:
        """Test copying templates to VS Code directory with settings."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS")

        copied_files, settings_path = copy_templates_to_ide(tmp_path, "vscode", templates_dir, force=True)

        assert len(copied_files) == 1
        assert settings_path is not None
        assert settings_path.exists()

        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "specfact.01-import.prompt.md").exists()
        assert (tmp_path / ".vscode" / "settings.json").exists()

    def test_copy_templates_skips_existing_without_force(self, tmp_path: Path) -> None:
        """Test copying templates skips existing files without force."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text("---\ndescription: Analyze\n---\n# Analyze\n$ARGUMENTS")

        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact.01-import.md").write_text("existing")

        copied_files, _settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=False)

        assert len(copied_files) == 0
        assert (cursor_dir / "specfact.01-import.md").read_text() == "existing"

    def test_copy_templates_overwrites_with_force(self, tmp_path: Path) -> None:
        """Test copying templates overwrites existing files with force."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.01-import.md").write_text(
            "---\ndescription: Analyze\n---\n# New Content\n$ARGUMENTS"
        )

        cursor_dir = tmp_path / ".cursor" / "commands"
        cursor_dir.mkdir(parents=True)
        (cursor_dir / "specfact.01-import.md").write_text("existing")

        copied_files, _settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=True)

        assert len(copied_files) == 1
        content = (cursor_dir / "specfact.01-import.md").read_text()
        assert "New Content" in content or "# New Content" in content

    def test_copy_templates_copies_non_core_prompt_ids_when_discovered(self, tmp_path: Path) -> None:
        """Discovered module prompt files are copied even when they are not in the legacy core list."""
        templates_dir = tmp_path / "resources" / "prompts"
        templates_dir.mkdir(parents=True)
        (templates_dir / "specfact.backlog-add.md").write_text(
            "---\ndescription: Add backlog item\n---\n# Backlog Add\n$ARGUMENTS"
        )

        copied_files, _settings_path = copy_templates_to_ide(tmp_path, "cursor", templates_dir, force=True)

        assert any(path.name == "specfact.backlog-add.md" for path in copied_files)
        assert (tmp_path / ".cursor" / "commands" / "specfact.backlog-add.md").exists()


def test_discover_prompt_template_files_falls_back_to_repo_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prompt discovery falls back to repo-local resources when no installed module resources exist."""
    import specfact_cli.utils.ide_setup as ide_setup_module

    monkeypatch.setattr(ide_setup_module, "_module_prompt_sources_catalog", lambda _rp: {})

    templates_dir = tmp_path / "resources" / "prompts"
    templates_dir.mkdir(parents=True)
    prompt_file = templates_dir / "specfact.01-import.md"
    prompt_file.write_text("---\ndescription: Analyze\n---\n# Analyze\n", encoding="utf-8")

    discovered = discover_prompt_template_files(tmp_path)

    assert discovered == [prompt_file]


def test_discover_prompt_template_files_prefers_target_repo_workspace_modules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Module discovery should follow the requested repo path, not the caller's current working directory."""
    repo_path = tmp_path / "target-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    package_dir = repo_path / ".specfact" / "modules" / "specfact-backlog"
    prompt_dir = package_dir / "resources" / "prompts"
    prompt_dir.mkdir(parents=True)
    (package_dir / "module-package.yaml").write_text(
        "name: nold-ai/specfact-backlog\nversion: '0.1.0'\ncommands: [backlog]\ncategory: backlog\nbundle_group_command: backlog\n",
        encoding="utf-8",
    )
    prompt_file = prompt_dir / "specfact.backlog-add.md"
    prompt_file.write_text("---\ndescription: Backlog add\n---\n# Backlog Add\n", encoding="utf-8")

    unrelated_cwd = tmp_path / "other-cwd"
    unrelated_cwd.mkdir()
    monkeypatch.chdir(unrelated_cwd)

    discovered = discover_prompt_template_files(repo_path)

    assert prompt_file in discovered
    assert str(prompt_file).startswith(str(repo_path))


def test_discover_prompt_template_files_deduplicates_prompt_ids_by_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Duplicate prompt ids from multiple module roots should keep the first discovered prompt."""
    first_dir = tmp_path / "module-a" / "resources" / "prompts"
    second_dir = tmp_path / "module-b" / "resources" / "prompts"
    first_dir.mkdir(parents=True)
    second_dir.mkdir(parents=True)

    first_prompt = first_dir / "specfact.backlog-add.md"
    second_prompt = second_dir / "specfact.backlog-add.md"
    first_prompt.write_text("---\ndescription: First\n---\n# First\n", encoding="utf-8")
    second_prompt.write_text("---\ndescription: Second\n---\n# Second\n", encoding="utf-8")

    import specfact_cli.utils.ide_setup as ide_setup_module

    monkeypatch.setattr(
        ide_setup_module,
        "discover_prompt_sources_catalog",
        lambda repo_path, include_package_fallback=True: {
            "nold-ai/mod-a": [first_prompt],
            "nold-ai/mod-b": [second_prompt],
        },
    )

    discovered = discover_prompt_template_files(tmp_path)

    assert discovered == [first_prompt]


def test_flat_export_glob_pattern_for_prune_matches_output_formats() -> None:
    """Prune globs must align with ``_output_filename_for_template`` (including Gemini/Qwen ``*.toml``)."""
    assert _flat_export_glob_pattern_for_prune("prompt.md") == "specfact*.prompt.md"
    assert _flat_export_glob_pattern_for_prune("toml") == "specfact*.toml"
    assert _flat_export_glob_pattern_for_prune("md") == "specfact*.md"


def test_is_specfact_github_prompt_path_only_specfact_named_prompts() -> None:
    """Strip targets only ``specfact*.prompt.md`` under ``.github/prompts/`` (after path normalization)."""
    assert _is_specfact_github_prompt_path(".github/prompts/core/specfact.01-import.prompt.md")
    assert _is_specfact_github_prompt_path(".\\github\\prompts\\nold-ai__x\\specfact.extra.prompt.md")
    assert not _is_specfact_github_prompt_path(".github/prompts/custom/team-owned.prompt.md")
    assert not _is_specfact_github_prompt_path(".other/specfact.01-import.prompt.md")
    assert not _is_specfact_github_prompt_path(".github/prompts/notes/readme.md")


def test_create_vscode_settings_selective_export_replaces_stale_github_prompt_paths(tmp_path: Path) -> None:
    """When ``prompts_by_source`` is set, drop SpecFact-managed ``.github/prompts/`` entries; keep team paths."""
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "chat": {
                    "promptFilesRecommendations": [
                        ".github/prompts/nold-ai__mod/specfact.extra.prompt.md",
                        ".github/prompts/custom/team-owned.prompt.md",
                        ".other/custom.prompt.md",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    prompt = tmp_path / "specfact.01-import.md"
    prompt.write_text("---\n---\n", encoding="utf-8")

    create_vscode_settings(
        tmp_path,
        ".vscode/settings.json",
        prompts_by_source={PROMPT_SOURCE_CORE: [prompt]},
    )

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    recs = list(data["chat"]["promptFilesRecommendations"])
    assert ".github/prompts/nold-ai__mod/specfact.extra.prompt.md" not in recs
    assert ".github/prompts/custom/team-owned.prompt.md" in recs
    assert ".other/custom.prompt.md" in recs
    assert ".github/prompts/specfact.01-import.prompt.md" in recs


def test_specfact_commands_excludes_backlog_prompt_ids() -> None:
    """Core IDE setup command list excludes backlog-owned prompt ids."""
    assert "specfact.backlog-add" not in SPECFACT_COMMANDS
    assert "specfact.backlog-daily" not in SPECFACT_COMMANDS
    assert "specfact.backlog-refine" not in SPECFACT_COMMANDS
    assert "specfact.sync-backlog" not in SPECFACT_COMMANDS


def test_write_and_load_ide_prompt_export_state_roundtrip(tmp_path: Path) -> None:
    """Persisted source ids round-trip for init audit when IDE matches."""
    write_ide_prompt_export_state(tmp_path, "cursor", ["core", "nold-ai/specfact-backlog"])
    loaded = load_ide_prompt_export_source_ids(tmp_path, "cursor")
    assert loaded == frozenset({"core", "nold-ai/specfact-backlog"})


def test_load_ide_prompt_export_source_ids_mismatched_ide_returns_none(tmp_path: Path) -> None:
    """State written for one IDE must not apply to audit for another IDE."""
    write_ide_prompt_export_state(tmp_path, "cursor", ["core"])
    assert load_ide_prompt_export_source_ids(tmp_path, "cursor") == frozenset({"core"})
    assert load_ide_prompt_export_source_ids(tmp_path, "vscode") is None


def test_expected_ide_prompt_export_paths_respects_prompt_source_subset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Audit expectations follow last export subset, not the full discovered catalog."""
    p_core = tmp_path / "c.md"
    p_mod = tmp_path / "m.md"
    monkeypatch.setattr(
        "specfact_cli.utils.ide_setup.discover_prompt_sources_catalog",
        lambda _rp, include_package_fallback=True: {
            PROMPT_SOURCE_CORE: [p_core],
            "nold-ai/mod": [p_mod],
        },
    )
    full_paths = expected_ide_prompt_export_paths(tmp_path, "cursor")
    subset_paths = expected_ide_prompt_export_paths(
        tmp_path, "cursor", prompt_source_ids=frozenset({PROMPT_SOURCE_CORE})
    )
    assert len(full_paths) == 2
    assert len(subset_paths) == 1
    assert subset_paths[0].name == "c.md"
    assert "core" not in subset_paths[0].parts
