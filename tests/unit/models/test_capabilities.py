"""Unit tests for ToolCapabilities model — v0.4.x alignment fields."""

from specfact_cli.models.capabilities import ToolCapabilities


class TestToolCapabilitiesV04Fields:
    """Test v0.4.x alignment fields on ToolCapabilities."""

    def test_default_new_fields_are_none(self) -> None:
        """All v0.4.x fields default to None for backward compatibility."""
        caps = ToolCapabilities(tool="speckit")
        assert caps.extensions is None
        assert caps.extension_commands is None
        assert caps.presets is None
        assert caps.hook_events is None
        assert caps.detected_version_source is None

    def test_construct_with_extensions(self) -> None:
        """Extensions list is stored correctly."""
        caps = ToolCapabilities(tool="speckit", extensions=["reconcile", "sync"])
        assert caps.extensions == ["reconcile", "sync"]

    def test_construct_with_extension_commands(self) -> None:
        """Extension commands dict is stored correctly."""
        cmds = {"reconcile": ["reconcile", "diff"], "sync": ["push", "pull"]}
        caps = ToolCapabilities(tool="speckit", extension_commands=cmds)
        assert caps.extension_commands == cmds

    def test_construct_with_presets(self) -> None:
        """Presets list is stored correctly."""
        caps = ToolCapabilities(tool="speckit", presets=["minimal", "full"])
        assert caps.presets == ["minimal", "full"]

    def test_construct_with_hook_events(self) -> None:
        """Hook events list is stored correctly."""
        caps = ToolCapabilities(tool="speckit", hook_events=["before_task", "after_task"])
        assert caps.hook_events == ["before_task", "after_task"]

    def test_construct_with_detected_version_source(self) -> None:
        """Detected version source is stored correctly."""
        caps = ToolCapabilities(tool="speckit", version="0.4.3", detected_version_source="cli")
        assert caps.detected_version_source == "cli"
        assert caps.version == "0.4.3"

    def test_construct_with_all_v04_fields(self) -> None:
        """All v0.4.x fields can be set together."""
        caps = ToolCapabilities(
            tool="speckit",
            version="0.4.3",
            layout="modern",
            extensions=["reconcile"],
            extension_commands={"reconcile": ["reconcile"]},
            presets=["minimal"],
            hook_events=["before_task"],
            detected_version_source="cli",
        )
        assert caps.extensions == ["reconcile"]
        assert caps.presets == ["minimal"]
        assert caps.hook_events == ["before_task"]
        assert caps.detected_version_source == "cli"

    def test_backward_compat_no_new_fields(self) -> None:
        """Pre-v0.4.x construction still works without new fields."""
        caps = ToolCapabilities(
            tool="speckit",
            version=None,
            layout="classic",
            specs_dir="specs",
            has_external_config=False,
            has_custom_hooks=False,
            supported_sync_modes=["bidirectional"],
        )
        assert caps.tool == "speckit"
        assert caps.extensions is None
