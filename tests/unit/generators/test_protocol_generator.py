"""Unit tests for ProtocolGenerator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest

from specfact_cli.generators.protocol_generator import ProtocolGenerator
from specfact_cli.models.protocol import Protocol, Transition


class TestProtocolGenerator:
    """Test suite for ProtocolGenerator."""

    @pytest.fixture
    def sample_protocol(self):
        """Create a sample protocol for testing."""
        return Protocol(
            states=["INIT", "RUNNING", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="start", to_state="RUNNING", guard=None),
                Transition(from_state="RUNNING", on_event="complete", to_state="DONE", guard=None),
            ],
            guards={
                "is_ready": "lambda state: state.get('ready', False)",
            },
        )

    @pytest.fixture
    def generator(self):
        """Create a ProtocolGenerator instance."""
        return ProtocolGenerator()

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_generate(self, generator, sample_protocol, output_dir):
        """Test generating protocol YAML file."""
        output_path = output_dir / "protocol.yaml"

        generator.generate(sample_protocol, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "INIT" in content
        assert "RUNNING" in content
        assert "DONE" in content
        assert "start" in content
        assert "complete" in content

    def test_generate_creates_parent_dirs(self, generator, sample_protocol, output_dir):
        """Test that generate creates parent directories if they don't exist."""
        output_path = output_dir / "nested" / "dirs" / "protocol.yaml"

        generator.generate(sample_protocol, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_render_string(self, generator, sample_protocol):
        """Test rendering protocol to string."""
        rendered = generator.render_string(sample_protocol)

        assert isinstance(rendered, str)
        assert "INIT" in rendered
        assert "RUNNING" in rendered
        assert "start" in rendered

    def test_generate_excludes_none_values(self, generator, output_dir):
        """Test that None values are excluded from generated YAML."""
        protocol = Protocol(
            states=["INIT", "DONE"],
            start="INIT",
            transitions=[
                Transition(from_state="INIT", on_event="finish", to_state="DONE", guard=None),
            ],
            # guards is None
        )

        output_path = output_dir / "protocol.yaml"
        generator.generate(protocol, output_path)

        content = output_path.read_text()
        # None values should not appear in output
        assert "null" not in content.lower()
        assert "none" not in content.lower()

    def test_generate_with_guards(self, generator, sample_protocol, output_dir):
        """Test generating protocol with guards."""
        output_path = output_dir / "protocol.yaml"

        generator.generate(sample_protocol, output_path)

        content = output_path.read_text()
        assert "guards:" in content
        assert "is_ready" in content

    def test_generate_from_template(self, generator, output_dir):
        """Test generating file from custom template."""
        # Use the PR template with minimal required context
        context = {
            "purpose": "Test PR",
            "changes": ["Change 1", "Change 2"],
            "validation_passed": True,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
        }

        output_path = output_dir / "pr.md"
        generator.generate_from_template("pr-template.md.j2", context, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test PR" in content
