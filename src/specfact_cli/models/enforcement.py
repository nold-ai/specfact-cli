"""Enforcement configuration models for quality gates."""

from enum import StrEnum

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class EnforcementAction(StrEnum):
    """Actions that can be taken when a deviation is detected."""

    BLOCK = "BLOCK"  # Fail the validation (exit code 1)
    WARN = "WARN"  # Show warning but continue (exit code 0)
    LOG = "LOG"  # Only log, no warning (exit code 0)


class EnforcementPreset(StrEnum):
    """Predefined enforcement presets."""

    MINIMAL = "minimal"  # Log everything, never block
    BALANCED = "balanced"  # Block HIGH, warn MEDIUM, log LOW
    STRICT = "strict"  # Block HIGH+MEDIUM, warn LOW


def _preset_is_valid(preset: EnforcementPreset) -> bool:
    return preset in EnforcementPreset


def _severity_is_hml(severity: str) -> bool:
    return severity.upper() in ("HIGH", "MEDIUM", "LOW")


def _to_summary_dict_valid(result: dict[str, str]) -> bool:
    if not isinstance(result, dict):
        return False
    if set(result.keys()) != {"HIGH", "MEDIUM", "LOW"}:
        return False
    return all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())


def _enforcement_config_is_enabled(result: "EnforcementConfig") -> bool:
    return result.enabled is True


class EnforcementConfig(BaseModel):
    """Configuration for contract enforcement and quality gates."""

    preset: EnforcementPreset = Field(default=EnforcementPreset.BALANCED, description="Enforcement preset mode")
    high_action: EnforcementAction = Field(
        default=EnforcementAction.BLOCK, description="Action for HIGH severity deviations"
    )
    medium_action: EnforcementAction = Field(
        default=EnforcementAction.WARN, description="Action for MEDIUM severity deviations"
    )
    low_action: EnforcementAction = Field(
        default=EnforcementAction.LOG, description="Action for LOW severity deviations"
    )
    enabled: bool = Field(default=True, description="Whether enforcement is enabled")

    @classmethod
    @require(_preset_is_valid, "Preset must be valid EnforcementPreset")
    @ensure(lambda result: isinstance(result, EnforcementConfig), "Must return EnforcementConfig")
    @ensure(_enforcement_config_is_enabled, "Config must be enabled")
    def from_preset(cls, preset: EnforcementPreset) -> "EnforcementConfig":
        """
        Create an enforcement config from a preset.

        Args:
            preset: The preset to use

        Returns:
            EnforcementConfig with preset values
        """
        if preset == EnforcementPreset.MINIMAL:
            return cls(
                preset=preset,
                high_action=EnforcementAction.WARN,
                medium_action=EnforcementAction.WARN,
                low_action=EnforcementAction.LOG,
                enabled=True,
            )
        if preset == EnforcementPreset.BALANCED:
            return cls(
                preset=preset,
                high_action=EnforcementAction.BLOCK,
                medium_action=EnforcementAction.WARN,
                low_action=EnforcementAction.LOG,
                enabled=True,
            )
        if preset == EnforcementPreset.STRICT:
            return cls(
                preset=preset,
                high_action=EnforcementAction.BLOCK,
                medium_action=EnforcementAction.BLOCK,
                low_action=EnforcementAction.WARN,
                enabled=True,
            )
        # Default to balanced
        return cls.from_preset(EnforcementPreset.BALANCED)

    @beartype
    @require(lambda severity: isinstance(severity, str) and len(severity) > 0, "Severity must be non-empty string")
    @require(_severity_is_hml, "Severity must be HIGH/MEDIUM/LOW")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def should_block_deviation(self, severity: str) -> bool:
        """
        Determine if a deviation should block execution.

        Args:
            severity: Deviation severity (HIGH, MEDIUM, LOW)

        Returns:
            True if this deviation should cause a failure (exit 1)
        """
        if not self.enabled:
            return False

        severity_upper = severity.upper()
        if severity_upper == "HIGH":
            return self.high_action == EnforcementAction.BLOCK
        if severity_upper == "MEDIUM":
            return self.medium_action == EnforcementAction.BLOCK
        if severity_upper == "LOW":
            return self.low_action == EnforcementAction.BLOCK
        return False

    @beartype
    @require(lambda severity: isinstance(severity, str) and len(severity) > 0, "Severity must be non-empty string")
    @require(_severity_is_hml, "Severity must be HIGH/MEDIUM/LOW")
    @ensure(lambda result: isinstance(result, EnforcementAction), "Must return EnforcementAction")
    def get_action(self, severity: str) -> EnforcementAction:
        """
        Get the action for a given severity level.

        Args:
            severity: Deviation severity (HIGH, MEDIUM, LOW)

        Returns:
            The enforcement action to take
        """
        severity_upper = severity.upper()
        if severity_upper == "HIGH":
            return self.high_action
        if severity_upper == "MEDIUM":
            return self.medium_action
        if severity_upper == "LOW":
            return self.low_action
        return EnforcementAction.LOG

    @beartype
    @ensure(_to_summary_dict_valid, "Summary dict must map HIGH/MEDIUM/LOW to string actions")
    def to_summary_dict(self) -> dict[str, str]:
        """
        Convert config to a summary dictionary for display.

        Returns:
            Dictionary mapping severity to action
        """
        return {
            "HIGH": str(self.high_action.value),
            "MEDIUM": str(self.medium_action.value),
            "LOW": str(self.low_action.value),
        }
