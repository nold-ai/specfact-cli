"""Tests for official-tier display in module registry CLI output."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.modules.module_registry.src.commands import app


runner = CliRunner()


def test_module_list_shows_official_marker_for_official_entries(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [
            {
                "id": "specfact-project",
                "version": "0.39.0",
                "enabled": True,
                "source": "marketplace",
                "official": True,
                "publisher": "nold-ai",
            }
        ],
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "[official]" in result.stdout


def test_module_install_reports_verified_official_tier(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("specfact_cli.modules.module_registry.src.commands.discover_all_modules", list)
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        lambda *_, **__: tmp_path / ".specfact" / "modules" / "specfact-project",
    )

    result = runner.invoke(
        app,
        [
            "install",
            "nold-ai/specfact-project",
            "--source",
            "marketplace",
            "--scope",
            "project",
            "--repo",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Verified: official (nold-ai)" in result.stdout
