"""Unit tests for enforcement configuration models.

Focus: Business logic and edge cases only (Pydantic handles type/field validation, enums are self-validating).
"""

import pytest

from specfact_cli.models.enforcement import EnforcementAction, EnforcementConfig, EnforcementPreset


class TestEnforcementConfig:
    """Test enforcement configuration model - business logic only."""

    def test_should_block_deviation_balanced(self):
        """Test should_block_deviation with balanced preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.BALANCED)

        assert config.should_block_deviation("HIGH") is True
        assert config.should_block_deviation("MEDIUM") is False
        assert config.should_block_deviation("LOW") is False

    def test_should_block_deviation_strict(self):
        """Test should_block_deviation with strict preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.STRICT)

        assert config.should_block_deviation("HIGH") is True
        assert config.should_block_deviation("MEDIUM") is True
        assert config.should_block_deviation("LOW") is False

    def test_should_block_deviation_minimal(self):
        """Test should_block_deviation with minimal preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.MINIMAL)

        assert config.should_block_deviation("HIGH") is False
        assert config.should_block_deviation("MEDIUM") is False
        assert config.should_block_deviation("LOW") is False

    def test_should_block_deviation_disabled(self):
        """Test should_block_deviation when enforcement is disabled."""
        config = EnforcementConfig(enabled=False)

        assert config.should_block_deviation("HIGH") is False
        assert config.should_block_deviation("MEDIUM") is False
        assert config.should_block_deviation("LOW") is False

    def test_should_block_deviation_case_insensitive(self):
        """Test should_block_deviation is case insensitive (edge case)."""
        config = EnforcementConfig.from_preset(EnforcementPreset.BALANCED)

        assert config.should_block_deviation("high") is True
        assert config.should_block_deviation("High") is True
        assert config.should_block_deviation("HiGh") is True

    def test_get_action_balanced(self):
        """Test get_action with balanced preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.BALANCED)

        assert config.get_action("HIGH") == EnforcementAction.BLOCK
        assert config.get_action("MEDIUM") == EnforcementAction.WARN
        assert config.get_action("LOW") == EnforcementAction.LOG

    def test_get_action_strict(self):
        """Test get_action with strict preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.STRICT)

        assert config.get_action("HIGH") == EnforcementAction.BLOCK
        assert config.get_action("MEDIUM") == EnforcementAction.BLOCK
        assert config.get_action("LOW") == EnforcementAction.WARN

    def test_get_action_minimal(self):
        """Test get_action with minimal preset."""
        config = EnforcementConfig.from_preset(EnforcementPreset.MINIMAL)

        assert config.get_action("HIGH") == EnforcementAction.WARN
        assert config.get_action("MEDIUM") == EnforcementAction.WARN
        assert config.get_action("LOW") == EnforcementAction.LOG

    def test_get_action_unknown_severity(self):
        """Test get_action with unknown severity is caught by @require contract (edge case)."""
        from icontract.errors import ViolationError

        config = EnforcementConfig.from_preset(EnforcementPreset.BALANCED)

        # Contract-first: @require catches invalid severity before default logic
        with pytest.raises(ViolationError):
            config.get_action("UNKNOWN")

        with pytest.raises(ViolationError):
            config.get_action("")
