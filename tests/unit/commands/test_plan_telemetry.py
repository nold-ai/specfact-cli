"""Unit tests for plan command telemetry tracking."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestPlanCommandTelemetry:
    """Test that plan commands track telemetry correctly."""

    @patch("specfact_cli.commands.plan.telemetry")
    def test_plan_init_tracks_telemetry(self, mock_telemetry: MagicMock, tmp_path, monkeypatch):
        """Test that plan init command tracks telemetry."""
        monkeypatch.chdir(tmp_path)

        # Mock the track_command context manager
        mock_record = MagicMock()
        mock_telemetry.track_command.return_value.__enter__.return_value = mock_record
        mock_telemetry.track_command.return_value.__exit__.return_value = None

        result = runner.invoke(app, ["plan", "init", "main", "--no-interactive"])

        assert result.exit_code == 0
        # Verify telemetry was called
        mock_telemetry.track_command.assert_called_once()
        call_args = mock_telemetry.track_command.call_args
        assert call_args[0][0] == "plan.init"
        assert "interactive" in call_args[0][1]
        assert "scaffold" in call_args[0][1]

    @patch("specfact_cli.commands.plan.telemetry")
    def test_plan_add_feature_tracks_telemetry(self, mock_telemetry: MagicMock, tmp_path, monkeypatch):
        """Test that plan add-feature command tracks telemetry."""
        monkeypatch.chdir(tmp_path)

        from specfact_cli.models.plan import PlanBundle, Product

        bundle = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[],
            metadata=None,
            clarifications=None,
        )

        # Mock the track_command context manager
        mock_record = MagicMock()
        mock_telemetry.track_command.return_value.__enter__.return_value = mock_record
        mock_telemetry.track_command.return_value.__exit__.return_value = None

        # Create modular bundle instead of single file
        from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
        from specfact_cli.utils.bundle_loader import save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=tmp_path, bundle_name="test-bundle")
        bundle_dir.mkdir(parents=True)
        project_bundle = _convert_plan_bundle_to_project_bundle(bundle, "test-bundle")
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        result = runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--bundle",
                "test-bundle",
            ],
        )

        assert result.exit_code == 0
        # Verify telemetry was called
        mock_telemetry.track_command.assert_called_once()
        call_args = mock_telemetry.track_command.call_args
        assert call_args[0][0] == "plan.add_feature"
        assert call_args[0][1]["feature_key"] == "FEATURE-001"
        # Verify record was called with additional metadata
        mock_record.assert_called()

    @patch("specfact_cli.commands.plan.telemetry")
    def test_plan_add_story_tracks_telemetry(self, mock_telemetry: MagicMock, tmp_path, monkeypatch):
        """Test that plan add-story command tracks telemetry."""
        monkeypatch.chdir(tmp_path)

        from specfact_cli.models.plan import Feature, PlanBundle, Product

        bundle = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[Feature(key="FEATURE-001", title="Test Feature", outcomes=[], acceptance=[], stories=[])],
            metadata=None,
            clarifications=None,
        )
        # Create modular bundle instead of single file
        from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
        from specfact_cli.utils.bundle_loader import save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=tmp_path, bundle_name="test-bundle")
        bundle_dir.mkdir(parents=True)
        project_bundle = _convert_plan_bundle_to_project_bundle(bundle, "test-bundle")
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock the track_command context manager
        mock_record = MagicMock()
        mock_telemetry.track_command.return_value.__enter__.return_value = mock_record
        mock_telemetry.track_command.return_value.__exit__.return_value = None

        result = runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                "test-bundle",
            ],
        )

        assert result.exit_code == 0
        # Verify telemetry was called
        mock_telemetry.track_command.assert_called_once()
        call_args = mock_telemetry.track_command.call_args
        assert call_args[0][0] == "plan.add_story"
        assert call_args[0][1]["feature_key"] == "FEATURE-001"
        assert call_args[0][1]["story_key"] == "STORY-001"
        # Verify record was called with additional metadata
        mock_record.assert_called()

    @patch("specfact_cli.commands.plan.telemetry")
    def test_plan_compare_tracks_telemetry(self, mock_telemetry: MagicMock, tmp_path):
        """Test that plan compare command tracks telemetry."""
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.models.plan import Feature, PlanBundle, Product

        # Create two plans
        manual_path = tmp_path / "manual.yaml"
        auto_path = tmp_path / "auto.yaml"

        manual_plan = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[Feature(key="FEATURE-001", title="Manual Feature", outcomes=[], acceptance=[], stories=[])],
            metadata=None,
            clarifications=None,
        )
        auto_plan = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[
                Feature(key="FEATURE-001", title="Manual Feature", outcomes=[], acceptance=[], stories=[]),
                Feature(key="FEATURE-002", title="Auto Feature", outcomes=[], acceptance=[], stories=[]),
            ],
            metadata=None,
            clarifications=None,
        )

        generator = PlanGenerator()
        generator.generate(manual_plan, manual_path)
        generator.generate(auto_plan, auto_path)

        # Mock the track_command context manager
        mock_record = MagicMock()
        mock_telemetry.track_command.return_value.__enter__.return_value = mock_record
        mock_telemetry.track_command.return_value.__exit__.return_value = None

        result = runner.invoke(
            app,
            [
                "plan",
                "compare",
                "--manual",
                str(manual_path),
                "--auto",
                str(auto_path),
            ],
        )

        assert result.exit_code == 0
        # Verify telemetry was called
        mock_telemetry.track_command.assert_called_once()
        call_args = mock_telemetry.track_command.call_args
        assert call_args[0][0] == "plan.compare"
        assert "code_vs_plan" in call_args[0][1]
        assert "output_format" in call_args[0][1]
        # Verify record was called with comparison results
        mock_record.assert_called()
        # Check that record was called with deviation counts
        record_calls = [call[0][0] for call in mock_record.call_args_list]
        assert any("total_deviations" in call for call in record_calls if isinstance(call, dict))

    @patch("specfact_cli.commands.plan.telemetry")
    def test_plan_promote_tracks_telemetry(self, mock_telemetry: MagicMock, tmp_path, monkeypatch):
        """Test that plan promote command tracks telemetry."""
        monkeypatch.chdir(tmp_path)

        from specfact_cli.models.plan import Metadata, PlanBundle, Product

        # Create a plan
        bundle = PlanBundle(
            idea=None,
            business=None,
            product=Product(themes=["Testing"]),
            features=[],
            metadata=Metadata(
                stage="draft", promoted_at=None, promoted_by=None, analysis_scope=None, entry_point=None, summary=None
            ),
            clarifications=None,
        )
        # Create modular bundle instead of single file
        from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
        from specfact_cli.utils.bundle_loader import save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=tmp_path, bundle_name="test-bundle")
        bundle_dir.mkdir(parents=True)
        project_bundle = _convert_plan_bundle_to_project_bundle(bundle, "test-bundle")
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock the track_command context manager
        mock_record = MagicMock()
        mock_telemetry.track_command.return_value.__enter__.return_value = mock_record
        mock_telemetry.track_command.return_value.__exit__.return_value = None

        result = runner.invoke(
            app,
            [
                "plan",
                "promote",
                "test-bundle",
                "--stage",
                "review",
                "--force",
            ],
        )

        assert result.exit_code == 0
        # Verify telemetry was called
        mock_telemetry.track_command.assert_called_once()
        call_args = mock_telemetry.track_command.call_args
        assert call_args[0][0] == "plan.promote"
        assert call_args[0][1]["target_stage"] == "review"
        assert call_args[0][1]["force"] is True
        # Verify record was called with promotion results
        mock_record.assert_called()
        # Check that record was called with stage information
        record_calls = [call[0][0] for call in mock_record.call_args_list]
        assert any("current_stage" in call for call in record_calls if isinstance(call, dict))
        assert any("target_stage" in call for call in record_calls if isinstance(call, dict))
