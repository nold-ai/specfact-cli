"""SpecFact directory structure utilities."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli import runtime
from specfact_cli.models.project import BundleFormat
from specfact_cli.utils.structured_io import StructuredFormat


class SpecFactStructure:
    """
    Manages the canonical .specfact/ directory structure.

    All SpecFact artifacts are stored under `.specfact/` for consistency
    and to support multiple plans in a single repository.
    """

    # Root directory
    ROOT = ".specfact"

    # Versioned directories (committed to git)
    PLANS = f"{ROOT}/plans"
    PROJECTS = f"{ROOT}/projects"  # Modular project bundles
    PROTOCOLS = f"{ROOT}/protocols"
    CONTRACTS = f"{ROOT}/contracts"

    # Ephemeral directories (gitignored)
    REPORTS = f"{ROOT}/reports"
    REPORTS_BROWNFIELD = f"{ROOT}/reports/brownfield"
    REPORTS_COMPARISON = f"{ROOT}/reports/comparison"
    REPORTS_ENFORCEMENT = f"{ROOT}/reports/enforcement"
    REPORTS_ENRICHMENT = f"{ROOT}/reports/enrichment"
    GATES_RESULTS = f"{ROOT}/gates/results"
    CACHE = f"{ROOT}/cache"
    SDD = f"{ROOT}/sdd"  # SDD manifests (one per project bundle)
    TASKS = f"{ROOT}/tasks"  # Task breakdowns (one per project bundle)
    CONFIG = f"{ROOT}/config"  # Global configuration (bridge.yaml, etc.)

    # Configuration files
    CONFIG_YAML = f"{ROOT}/config.yaml"
    GATES_CONFIG = f"{ROOT}/gates/config.yaml"
    ENFORCEMENT_CONFIG = f"{ROOT}/gates/config/enforcement.yaml"

    # Default plan names (legacy, kept for backward compatibility)
    DEFAULT_PLAN_NAME = "main"
    DEFAULT_PLAN = f"{ROOT}/plans/{DEFAULT_PLAN_NAME}.bundle.yaml"  # Legacy, not used
    BROWNFIELD_PLAN = f"{ROOT}/plans/auto-derived.yaml"  # Legacy, not used
    PLANS_CONFIG = f"{ROOT}/plans/config.yaml"  # Legacy, migrated to CONFIG_YAML
    ACTIVE_BUNDLE_CONFIG_KEY = "active_bundle"  # Key in config.yaml for active bundle name
    PLAN_SUFFIX_MAP = {
        StructuredFormat.YAML: ".bundle.yaml",
        StructuredFormat.JSON: ".bundle.json",
    }
    PLAN_SUFFIXES = tuple({".bundle.yaml", ".bundle.yml", ".bundle.json"})

    @classmethod
    def plan_suffix(cls, format: StructuredFormat | None = None) -> str:
        """Return canonical plan suffix for format (defaults to YAML)."""
        fmt = format or StructuredFormat.YAML
        return cls.PLAN_SUFFIX_MAP.get(fmt, ".bundle.yaml")

    @classmethod
    def ensure_plan_filename(cls, plan_name: str, format: StructuredFormat | None = None) -> str:
        """Ensure a plan filename includes the correct suffix."""
        lower = plan_name.lower()
        if any(lower.endswith(suffix) for suffix in cls.PLAN_SUFFIXES):
            return plan_name
        if lower.endswith((".yaml", ".json")):
            return plan_name
        return f"{plan_name}{cls.plan_suffix(format)}"

    @classmethod
    def strip_plan_suffix(cls, plan_name: str) -> str:
        """Remove known plan suffix from filename."""
        for suffix in cls.PLAN_SUFFIXES:
            if plan_name.endswith(suffix):
                return plan_name[: -len(suffix)]
        if plan_name.endswith(".yaml"):
            return plan_name[: -len(".yaml")]
        if plan_name.endswith(".json"):
            return plan_name[: -len(".json")]
        return plan_name

    @classmethod
    def default_plan_filename(cls, format: StructuredFormat | None = None) -> str:
        """Compute default plan filename for requested format."""
        return cls.ensure_plan_filename(cls.DEFAULT_PLAN_NAME, format)

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: result is None, "Must return None")
    def ensure_structure(cls, base_path: Path | None = None) -> None:
        """
        Ensure the .specfact directory structure exists.

        Args:
            base_path: Base directory (default: current directory)
                       Must be repository root, not a subdirectory
        """
        if base_path is None:
            base_path = Path(".")
        else:
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Create global directories only (Phase 8.5: bundle-specific artifacts moved to projects/<bundle-name>/)
        (base_path / cls.PROJECTS).mkdir(parents=True, exist_ok=True)  # Project bundles container
        (base_path / f"{cls.ROOT}/gates/config").mkdir(
            parents=True, exist_ok=True
        )  # Global enforcement gates config (default policy)
        (base_path / cls.CONFIG).mkdir(parents=True, exist_ok=True)  # Global configuration (bridge.yaml, etc.)
        (base_path / cls.CACHE).mkdir(parents=True, exist_ok=True)  # Shared cache

        # Note: The following directories are NO LONGER created at top level (Phase 8.5):
        # - PLANS: Deprecated (no monolithic bundles, active bundle config moved to config.yaml)
        # - PROTOCOLS: Now bundle-specific (.specfact/projects/<bundle-name>/protocols/)
        # - CONTRACTS: Now bundle-specific (.specfact/projects/<bundle-name>/contracts/)
        # - SDD: Now bundle-specific (.specfact/projects/<bundle-name>/sdd.yaml)
        # - REPORTS: Now bundle-specific (.specfact/projects/<bundle-name>/reports/)
        # - TASKS: Now bundle-specific (.specfact/projects/<bundle-name>/tasks.yaml)
        # - GATES_RESULTS: Removed (gate results not used; enforcement reports are bundle-specific in reports/enforcement/)
        # Use ensure_project_structure() to create bundle-specific directories.

    @classmethod
    @beartype
    @require(
        lambda report_type: isinstance(report_type, str) and report_type in ("brownfield", "comparison", "enforcement"),
        "Report type must be brownfield/comparison/enforcement",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda extension: isinstance(extension, str) and len(extension) > 0, "Extension must be non-empty string")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_timestamped_report_path(
        cls, report_type: str, base_path: Path | None = None, extension: str = "md"
    ) -> Path:
        """
        Get a timestamped report path.

        Args:
            report_type: Type of report (brownfield, comparison, enforcement)
            base_path: Base directory (default: current directory)
            extension: File extension (default: md)

        Returns:
            Path to timestamped report file
        """
        if base_path is None:
            base_path = Path(".")

        # Use ISO format timestamp for consistency
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        if report_type == "brownfield":
            directory = base_path / cls.REPORTS_BROWNFIELD
        elif report_type == "comparison":
            directory = base_path / cls.REPORTS_COMPARISON
        elif report_type == "enforcement":
            directory = base_path / cls.REPORTS_ENFORCEMENT
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"report-{timestamp}.{extension}"

    @classmethod
    def get_brownfield_analysis_path(cls, base_path: Path | None = None) -> Path:
        """Get path for brownfield analysis report."""
        return cls.get_timestamped_report_path("brownfield", base_path, "md")

    @classmethod
    def get_brownfield_plan_path(cls, base_path: Path | None = None) -> Path:
        """Get path for auto-derived brownfield plan."""
        return cls.get_timestamped_report_path("brownfield", base_path, "yaml")

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda format: isinstance(format, str) and format in ("md", "json", "yaml"), "Format must be md/json/yaml")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_comparison_report_path(cls, base_path: Path | None = None, format: str = "md") -> Path:
        """Get path for comparison report."""
        return cls.get_timestamped_report_path("comparison", base_path, format)

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_default_plan_path(
        cls, base_path: Path | None = None, preferred_format: StructuredFormat | None = None
    ) -> Path:
        """
        Get path to active plan bundle (from config or fallback to main.bundle.yaml).

        Args:
            base_path: Base directory (default: current directory)
            preferred_format: Preferred structured format (defaults to runtime output format)

        Returns:
            Path to active plan bundle (from config or default)
        """
        if base_path is None:
            base_path = Path(".")
        else:
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Try to read active bundle from global config.yaml (new location)
        config_path = base_path / cls.CONFIG_YAML
        if config_path.exists():
            try:
                import yaml

                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
                active_bundle = config.get(cls.ACTIVE_BUNDLE_CONFIG_KEY)
                if active_bundle:
                    bundle_dir = base_path / cls.PROJECTS / active_bundle
                    if bundle_dir.exists() and (bundle_dir / "bundle.manifest.yaml").exists():
                        return bundle_dir
            except Exception:
                # Fallback if config read fails
                pass

        # Legacy config present: instruct migration instead of fallback
        legacy_config_path = base_path / cls.PLANS_CONFIG
        if legacy_config_path.exists():
            raise FileNotFoundError(
                "Legacy plan configuration detected at .specfact/plans/config.yaml. "
                "Please migrate to the new bundle structure using 'specfact migrate artifacts --repo .'."
            )

        # No active bundle found - return default bundle directory path (may not exist)
        return base_path / cls.PROJECTS / cls.DEFAULT_PLAN_NAME

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return None or string")
    def get_active_bundle_name(cls, base_path: Path | None = None) -> str | None:
        """
        Get active bundle name from config.

        Args:
            base_path: Base directory (default: current directory)

        Returns:
            Active bundle name (e.g., "main", "legacy-api") or None if not set
        """
        if base_path is None:
            base_path = Path(".")
        else:
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Try to read active bundle from global config.yaml (new location)
        config_path = base_path / cls.CONFIG_YAML
        if config_path.exists():
            try:
                import yaml

                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
                active_bundle = config.get(cls.ACTIVE_BUNDLE_CONFIG_KEY)
                if active_bundle:
                    return active_bundle
            except Exception:
                # Fallback if config read fails
                pass

        return None

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda plan_name: isinstance(plan_name, str) and len(plan_name) > 0, "Plan name must be non-empty string")
    @ensure(lambda result: result is None, "Must return None")
    def set_active_plan(cls, plan_name: str, base_path: Path | None = None) -> None:
        """
        Set the active project bundle in the plans config.

        Args:
            plan_name: Name of the project bundle (e.g., "main", "legacy-api", "auth-module")
            base_path: Base directory (default: current directory)

        Examples:
            >>> SpecFactStructure.set_active_plan("legacy-api")
            >>> SpecFactStructure.get_default_plan_path()
            Path('.specfact/projects/legacy-api')
        """
        if base_path is None:
            base_path = Path(".")

        import yaml

        projects_dir = base_path / cls.PROJECTS

        # Ensure projects directory exists
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Verify bundle exists
        bundle_dir = projects_dir / plan_name
        if not bundle_dir.exists() or not (bundle_dir / "bundle.manifest.yaml").exists():
            raise FileNotFoundError(f"Project bundle not found: {bundle_dir}")

        # Write to global config.yaml (new location, only)
        config_path = base_path / cls.CONFIG_YAML

        # Read existing config or create new
        config = {}
        if config_path.exists():
            try:
                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                config = {}

        # Update active bundle (bundle name)
        config[cls.ACTIVE_BUNDLE_CONFIG_KEY] = plan_name

        # Write config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda max_files: max_files is None or max_files > 0, "Max files must be None or positive")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_plans(
        cls, base_path: Path | None = None, max_files: int | None = None
    ) -> list[dict[str, str | int | None]]:
        """
        List all available project bundles with metadata.

        Args:
            base_path: Base directory (default: current directory)
            max_files: Maximum number of bundles to process (for performance with many bundles).
                      If None, processes all bundles. If specified, processes most recent bundles first.

        Returns:
            List of bundle dictionaries with 'name', 'path', 'features', 'stories', 'size', 'modified' keys

        Examples:
            >>> plans = SpecFactStructure.list_plans()
            >>> plans[0]['name']
            'legacy-api'
            >>> plans = SpecFactStructure.list_plans(max_files=5)  # Only process 5 most recent
        """
        if base_path is None:
            base_path = Path(".")

        projects_dir = base_path / cls.PROJECTS
        if not projects_dir.exists():
            return []

        from datetime import datetime

        import yaml

        plans = []
        active_plan = None

        # Get active bundle from config (new location only)
        config_path = base_path / cls.CONFIG_YAML
        active_plan = None
        if config_path.exists():
            try:
                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
                active_plan = config.get(cls.ACTIVE_BUNDLE_CONFIG_KEY)
            except Exception:
                pass

        # Find all project bundle directories
        bundle_dirs = [d for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()]
        bundle_dirs_sorted = sorted(
            bundle_dirs, key=lambda d: (d / "bundle.manifest.yaml").stat().st_mtime, reverse=False
        )

        # If max_files specified, only process the most recent N bundles (for performance)
        if max_files is not None and max_files > 0:
            # Take most recent bundles (reverse sort, take last N, then reverse back)
            bundle_dirs_sorted = sorted(
                bundle_dirs, key=lambda d: (d / "bundle.manifest.yaml").stat().st_mtime, reverse=True
            )[:max_files]
            bundle_dirs_sorted = sorted(
                bundle_dirs_sorted, key=lambda d: (d / "bundle.manifest.yaml").stat().st_mtime, reverse=False
            )

        for bundle_dir in bundle_dirs_sorted:
            bundle_name = bundle_dir.name
            manifest_path = bundle_dir / "bundle.manifest.yaml"

            # Declare plan_info once before try/except
            plan_info: dict[str, str | int | None]

            try:
                # Read only the manifest file (much faster than loading full bundle)
                from specfact_cli.models.project import BundleManifest
                from specfact_cli.utils.structured_io import load_structured_file

                manifest_data = load_structured_file(manifest_path)
                manifest = BundleManifest.model_validate(manifest_data)

                # Get modification time from manifest file
                manifest_mtime = manifest_path.stat().st_mtime

                # Calculate total size of bundle directory
                total_size = sum(f.stat().st_size for f in bundle_dir.rglob("*") if f.is_file())

                # Get features and stories count from manifest.features index
                features_count = len(manifest.features) if manifest.features else 0
                stories_count = sum(f.stories_count for f in manifest.features) if manifest.features else 0

                # Get stage from manifest.bundle dict (if available) or default to "draft"
                stage = manifest.bundle.get("stage", "draft") if manifest.bundle else "draft"

                # Get content hash from manifest versions (use project version as hash identifier)
                content_hash = manifest.versions.project if manifest.versions else None

                plan_info = {
                    "name": bundle_name,
                    "path": str(bundle_dir.relative_to(base_path)),
                    "features": features_count,
                    "stories": stories_count,
                    "size": total_size,
                    "modified": datetime.fromtimestamp(manifest_mtime).isoformat(),
                    "active": bundle_name == active_plan,
                    "content_hash": content_hash,
                    "stage": stage,
                }
            except Exception:
                # Fallback: minimal info if manifest can't be loaded
                manifest_mtime = manifest_path.stat().st_mtime if manifest_path.exists() else 0
                total_size = sum(f.stat().st_size for f in bundle_dir.rglob("*") if f.is_file())

                plan_info = {
                    "name": bundle_name,
                    "path": str(bundle_dir.relative_to(base_path)),
                    "features": 0,
                    "stories": 0,
                    "size": total_size,
                    "modified": datetime.fromtimestamp(manifest_mtime).isoformat()
                    if manifest_mtime > 0
                    else datetime.now().isoformat(),
                    "active": bundle_name == active_plan,
                    "content_hash": None,
                    "stage": "unknown",
                }

            plans.append(plan_info)

        return plans

    @classmethod
    @beartype
    def update_plan_summary(cls, plan_path: Path, base_path: Path | None = None) -> bool:
        """
        Update summary metadata for an existing plan bundle.

        This is a migration helper to add summary metadata to plan bundles
        that were created before the summary feature was added.

        Args:
            plan_path: Path to plan bundle file
            base_path: Base directory (default: current directory)

        Returns:
            True if summary was updated, False otherwise
        """
        if base_path is None:
            base_path = Path(".")

        plan_file = base_path / plan_path if not plan_path.is_absolute() else plan_path

        if not plan_file.exists():
            return False

        try:
            import yaml

            from specfact_cli.generators.plan_generator import PlanGenerator
            from specfact_cli.models.plan import PlanBundle

            # Load plan bundle
            with plan_file.open() as f:
                plan_data = yaml.safe_load(f) or {}

            # Parse as PlanBundle
            bundle = PlanBundle.model_validate(plan_data)

            # Update summary (with hash for integrity)
            bundle.update_summary(include_hash=True)

            # Save updated bundle
            generator = PlanGenerator()
            generator.generate(bundle, plan_file, update_summary=True)

            return True
        except Exception:
            return False

    @classmethod
    def get_enforcement_config_path(cls, base_path: Path | None = None) -> Path:
        """Get path to enforcement configuration file."""
        if base_path is None:
            base_path = Path(".")
        return base_path / cls.ENFORCEMENT_CONFIG

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_sdd_path(cls, base_path: Path | None = None, format: StructuredFormat | None = None) -> Path:
        """
        Get path to SDD manifest file.

        Args:
            base_path: Base directory (default: current directory)
            format: Preferred structured format (defaults to runtime output format)

        Returns:
            Path to SDD manifest (checks for .yaml first, then .json)
        """
        if base_path is None:
            base_path = Path(".")
        else:
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        format_hint = format or runtime.get_output_format()

        # Try preferred format first
        if format_hint == StructuredFormat.YAML:
            sdd_path = base_path / cls.ROOT / "sdd.yaml"
            if sdd_path.exists():
                return sdd_path
            # Fallback to JSON
            sdd_path = base_path / cls.ROOT / "sdd.json"
            if sdd_path.exists():
                return sdd_path
            # Return YAML path as default
            return base_path / cls.ROOT / "sdd.yaml"
        sdd_path = base_path / cls.ROOT / "sdd.json"
        if sdd_path.exists():
            return sdd_path
        # Fallback to YAML
        sdd_path = base_path / cls.ROOT / "sdd.yaml"
        if sdd_path.exists():
            return sdd_path
        # Return JSON path as default
        return base_path / cls.ROOT / "sdd.json"

    @classmethod
    @beartype
    @require(lambda name: name is None or isinstance(name, str), "Name must be None or str")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Sanitized name must be non-empty")
    def sanitize_plan_name(cls, name: str | None) -> str:
        """
        Sanitize plan name for filesystem persistence.

        Converts to lowercase, removes spaces and special characters,
        keeping only alphanumeric, hyphens, and underscores.

        Args:
            name: Plan name to sanitize (e.g., "My Feature Plan", "api-client-v2")

        Returns:
            Sanitized name safe for filesystem (e.g., "my-feature-plan", "api-client-v2")

        Examples:
            >>> SpecFactStructure.sanitize_plan_name("My Feature Plan")
            'my-feature-plan'
            >>> SpecFactStructure.sanitize_plan_name("API Client v2.0")
            'api-client-v20'
            >>> SpecFactStructure.sanitize_plan_name("test_plan_123")
            'test_plan_123'
        """
        if not name:
            return "auto-derived"

        # Convert to lowercase
        sanitized = name.lower()

        # Replace spaces and dots with hyphens
        sanitized = re.sub(r"[.\s]+", "-", sanitized)

        # Remove all characters except alphanumeric, hyphens, and underscores
        sanitized = re.sub(r"[^a-z0-9_-]", "", sanitized)

        # Remove consecutive hyphens and underscores
        sanitized = re.sub(r"[-_]{2,}", "-", sanitized)

        # Remove leading/trailing hyphens and underscores
        sanitized = sanitized.strip("-_")

        # Ensure it's not empty
        if not sanitized:
            return "auto-derived"

        return sanitized

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda name: name is None or isinstance(name, str), "Name must be None or str")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_timestamped_brownfield_report(
        cls, base_path: Path | None = None, name: str | None = None, format: StructuredFormat | None = None
    ) -> Path:
        """
        Get timestamped path for brownfield analysis report (YAML bundle).

        Args:
            base_path: Base directory (default: current directory)
            name: Custom plan name (will be sanitized, default: "auto-derived")

        Returns:
            Path to plan bundle file (e.g., `.specfact/plans/my-feature-plan.2025-11-04T23-19-31.bundle.yaml`)

        Examples:
            >>> SpecFactStructure.get_timestamped_brownfield_report(name="API Client v2")
            Path('.specfact/plans/api-client-v2.2025-11-04T23-19-31.bundle.yaml')
        """
        if base_path is None:
            base_path = Path(".")
        else:
            # Normalize base_path to repository root (avoid recursive .specfact creation)
            base_path = Path(base_path).resolve()
            # If base_path contains .specfact, find the repository root
            parts = base_path.parts
            if ".specfact" in parts:
                # Find the index of .specfact and go up to repository root
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        format_hint = format or runtime.get_output_format()
        sanitized_name = cls.sanitize_plan_name(name)
        directory = base_path / cls.PLANS
        directory.mkdir(parents=True, exist_ok=True)
        suffix = cls.plan_suffix(format_hint)
        return directory / f"{sanitized_name}.{timestamp}{suffix}"

    @classmethod
    @beartype
    @require(lambda plan_bundle_path: isinstance(plan_bundle_path, Path), "Plan bundle path must be Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_enrichment_report_path(cls, plan_bundle_path: Path, base_path: Path | None = None) -> Path:
        """
        Get enrichment report path based on plan bundle path.

        The enrichment report is named to match the plan bundle, replacing
        `.bundle.yaml` with `.enrichment.md` and placing it in the enrichment reports directory.

        Args:
            plan_bundle_path: Path to plan bundle file (e.g., `.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml`)
            base_path: Base directory (default: current directory)

        Returns:
            Path to enrichment report (e.g., `.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md`)

        Examples:
            >>> plan = Path('.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml')
            >>> SpecFactStructure.get_enrichment_report_path(plan)
            Path('.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md')
        """
        if base_path is None:
            base_path = Path(".")
        else:
            # Normalize base_path to repository root (avoid recursive .specfact creation)
            base_path = Path(base_path).resolve()
            # If base_path contains .specfact, find the repository root
            parts = base_path.parts
            if ".specfact" in parts:
                # Find the index of .specfact and go up to repository root
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Extract filename base from plan bundle path (without suffix)
        base_name = cls.strip_plan_suffix(plan_bundle_path.name)

        # Append enrichment marker
        enrichment_filename = f"{base_name}.enrichment.md"

        directory = base_path / cls.REPORTS_ENRICHMENT
        directory.mkdir(parents=True, exist_ok=True)
        return directory / enrichment_filename

    @classmethod
    @beartype
    @require(
        lambda enrichment_report_path: isinstance(enrichment_report_path, Path), "Enrichment report path must be Path"
    )
    @ensure(lambda result: result is None or isinstance(result, Path), "Must return None or Path")
    def get_plan_bundle_from_enrichment(
        cls, enrichment_report_path: Path, base_path: Path | None = None
    ) -> Path | None:
        """
        Get original plan bundle path from enrichment report path.

        Derives the original plan bundle path by reversing the enrichment report naming convention.
        The enrichment report is named to match the plan bundle, so we can reverse this.

        Args:
            enrichment_report_path: Path to enrichment report (e.g., `.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md`)
            base_path: Base directory (default: current directory)

        Returns:
            Path to original plan bundle, or None if not found

        Examples:
            >>> enrichment = Path('.specfact/reports/enrichment/specfact-cli.2025-11-17T09-26-47.enrichment.md')
            >>> SpecFactStructure.get_plan_bundle_from_enrichment(enrichment)
            Path('.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml')
        """
        if base_path is None:
            base_path = Path(".")
        else:
            # Normalize base_path to repository root
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Extract filename from enrichment report path
        enrichment_filename = enrichment_report_path.name

        if enrichment_filename.endswith(".enrichment.md"):
            base_name = enrichment_filename[: -len(".enrichment.md")]
        else:
            base_name = enrichment_report_path.stem

        plans_dir = base_path / cls.PLANS
        # Try all supported suffixes to find matching plan
        for suffix in cls.PLAN_SUFFIXES:
            candidate = plans_dir / f"{base_name}{suffix}"
            if candidate.exists():
                return candidate

        # Fallback to default suffix
        fallback = plans_dir / f"{base_name}{cls.plan_suffix()}"
        return fallback if fallback.exists() else None

    @classmethod
    @beartype
    @require(lambda original_plan_path: isinstance(original_plan_path, Path), "Original plan path must be Path")
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_enriched_plan_path(cls, original_plan_path: Path, base_path: Path | None = None) -> Path:
        """
        Get enriched plan bundle path based on original plan bundle path.

        Creates a path for an enriched plan bundle with a clear "enriched" label and timestamp.
        Format: `<name>.<original-timestamp>.enriched.<enrichment-timestamp>.bundle.yaml`

        Args:
            original_plan_path: Path to original plan bundle (e.g., `.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml`)
            base_path: Base directory (default: current directory)

        Returns:
            Path to enriched plan bundle (e.g., `.specfact/plans/specfact-cli.2025-11-17T09-26-47.enriched.2025-11-17T11-15-29.bundle.yaml`)

        Examples:
            >>> plan = Path('.specfact/plans/specfact-cli.2025-11-17T09-26-47.bundle.yaml')
            >>> SpecFactStructure.get_enriched_plan_path(plan)
            Path('.specfact/plans/specfact-cli.2025-11-17T09-26-47.enriched.2025-11-17T11-15-29.bundle.yaml')
        """
        if base_path is None:
            base_path = Path(".")
        else:
            # Normalize base_path to repository root
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Extract original plan filename
        original_filename = original_plan_path.name

        # Determine current format to preserve suffix
        plan_format = StructuredFormat.from_path(original_plan_path)
        suffix = cls.plan_suffix(plan_format)

        # Extract name and original timestamp from filename
        # Format: <name>.<timestamp>.bundle.<ext>
        if original_filename.endswith(suffix):
            name_with_timestamp = original_filename[: -len(suffix)]
            # Split name and timestamp (timestamp is after last dot before suffix)
            parts_name = name_with_timestamp.rsplit(".", 1)
            if len(parts_name) == 2:
                # Has timestamp: <name>.<timestamp>
                name_part = parts_name[0]
                original_timestamp = parts_name[1]
            else:
                # No timestamp found, use whole name
                name_part = name_with_timestamp
                original_timestamp = None
        else:
            # Fallback: use stem
            name_part = original_plan_path.stem
            original_timestamp = None

        # Generate new timestamp for enrichment
        enrichment_timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        # Build enriched filename
        if original_timestamp:
            enriched_filename = f"{name_part}.{original_timestamp}.enriched.{enrichment_timestamp}{suffix}"
        else:
            enriched_filename = f"{name_part}.enriched.{enrichment_timestamp}{suffix}"

        directory = base_path / cls.PLANS
        directory.mkdir(parents=True, exist_ok=True)
        return directory / enriched_filename

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: result is None or isinstance(result, Path), "Must return None or Path")
    def get_latest_brownfield_report(cls, base_path: Path | None = None) -> Path | None:
        """
        Get the latest brownfield report from bundle-specific directories.

        Args:
            base_path: Base directory (default: current directory)

        Returns:
            Path to latest brownfield report, or None if none exist
        """
        if base_path is None:
            base_path = Path(".")

        projects_dir = base_path / cls.PROJECTS
        if not projects_dir.exists():
            return None

        # Search bundle-specific brownfield reports
        reports: list[Path] = []
        for bundle_dir in projects_dir.glob("*"):
            brownfield_dir = bundle_dir / "reports" / "brownfield"
            if not brownfield_dir.exists():
                continue
            reports.extend(sorted(brownfield_dir.glob("analysis-*.md"), key=lambda p: (p.stat().st_mtime, p.name)))

        reports = sorted(reports, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
        if reports:
            return reports[0]

        # Legacy fallback: .specfact/plans/*.bundle.yaml
        legacy_plans_dir = base_path / cls.PLANS
        if legacy_plans_dir.exists():
            legacy_reports = sorted(
                legacy_plans_dir.glob("*.bundle.yaml"),
                key=lambda p: (p.stat().st_mtime, p.name),
                reverse=True,
            )
            if legacy_reports:
                return legacy_reports[0]

        return None

    @classmethod
    def create_gitignore(cls, base_path: Path | None = None) -> None:
        """
        Create .gitignore for .specfact directory.

        Args:
            base_path: Base directory (default: current directory)
        """
        if base_path is None:
            base_path = Path(".")

        gitignore_path = base_path / cls.ROOT / ".gitignore"
        gitignore_content = """# SpecFact ephemeral artifacts (not versioned)
reports/
cache/

# Keep these versioned
!projects/
!config.yaml
!gates/config.yaml
"""
        gitignore_path.write_text(gitignore_content)

    @classmethod
    def create_readme(cls, base_path: Path | None = None) -> None:
        """
        Create README for .specfact directory.

        Args:
            base_path: Base directory (default: current directory)
        """
        if base_path is None:
            base_path = Path(".")

        readme_path = base_path / cls.ROOT / "README.md"
        readme_content = """# SpecFact Directory

This directory contains SpecFact CLI artifacts for contract-driven development.

## Structure

- `plans/` - Plan bundles (versioned in git)
- `protocols/` - FSM protocol definitions (versioned)
- `reports/` - Analysis reports (gitignored)
  - `brownfield/` - Brownfield import analysis reports
  - `comparison/` - Plan comparison reports
  - `enforcement/` - Enforcement validation reports
  - `enrichment/` - LLM enrichment reports (matched to plan bundles by name/timestamp)
- `gates/` - Enforcement configuration and results
- `cache/` - Tool caches (gitignored)

## Documentation

See `docs/directory-structure.md` for complete documentation.

## Getting Started

```bash
# Create a new plan
specfact plan init --interactive

# Analyze existing code
specfact import from-code --repo .

# Compare plans
        specfact plan compare --manual .specfact/plans/main.bundle.yaml --auto .specfact/plans/auto-derived-<timestamp>.bundle.yaml
```
"""
        readme_path.write_text(readme_content)

    @classmethod
    def scaffold_project(cls, base_path: Path | None = None) -> None:
        """
        Create complete .specfact directory structure.

        Args:
            base_path: Base directory (default: current directory)
        """
        cls.ensure_structure(base_path)
        cls.create_gitignore(base_path)
        cls.create_readme(base_path)

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def project_dir(cls, base_path: Path | None = None, bundle_name: str = "") -> Path:
        """
        Get path to project bundle directory.

        Args:
            base_path: Base directory (default: current directory)
            bundle_name: Project bundle name (e.g., 'legacy-api', 'auth-module')

        Returns:
            Path to project bundle directory (e.g., .specfact/projects/legacy-api/)

        Examples:
            >>> SpecFactStructure.project_dir(bundle_name="legacy-api")
            Path('.specfact/projects/legacy-api')
        """
        if base_path is None:
            base_path = Path(".")
        else:
            base_path = Path(base_path).resolve()
            parts = base_path.parts
            if ".specfact" in parts:
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        return base_path / cls.PROJECTS / bundle_name

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @ensure(lambda result: result is None, "Must return None")
    def ensure_project_structure(cls, base_path: Path | None = None, bundle_name: str = "") -> None:
        """
        Ensure project bundle directory structure exists.

        Creates the project bundle directory and required subdirectories:
        - .specfact/projects/<bundle-name>/
        - .specfact/projects/<bundle-name>/features/
        - .specfact/projects/<bundle-name>/protocols/
        - .specfact/projects/<bundle-name>/contracts/
        - .specfact/projects/<bundle-name>/reports/ (bundle-specific reports)
        - .specfact/projects/<bundle-name>/logs/ (bundle-specific logs)

        Args:
            base_path: Base directory (default: current directory)
            bundle_name: Project bundle name (e.g., 'legacy-api', 'auth-module')

        Examples:
            >>> SpecFactStructure.ensure_project_structure(bundle_name="legacy-api")
        """
        project_dir = cls.project_dir(base_path, bundle_name)
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "features").mkdir(parents=True, exist_ok=True)
        (project_dir / "protocols").mkdir(parents=True, exist_ok=True)
        (project_dir / "contracts").mkdir(parents=True, exist_ok=True)
        # Bundle-specific reports directories
        (project_dir / "reports" / "brownfield").mkdir(parents=True, exist_ok=True)
        (project_dir / "reports" / "comparison").mkdir(parents=True, exist_ok=True)
        (project_dir / "reports" / "enrichment").mkdir(parents=True, exist_ok=True)
        (project_dir / "reports" / "enforcement").mkdir(parents=True, exist_ok=True)
        # Bundle-specific logs directory
        (project_dir / "logs").mkdir(parents=True, exist_ok=True)

    @classmethod
    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(
        lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (BundleFormat, Optional[str]) tuple"
    )
    def detect_bundle_format(cls, path: Path) -> tuple[BundleFormat, str | None]:
        """
        Detect if bundle is monolithic or modular.

        Args:
            path: Path to bundle (file or directory)

        Returns:
            Tuple of (format, error_message)
            - format: Detected format type
            - error_message: None if successful, error message if detection failed

        Examples:
            >>> format, error = SpecFactStructure.detect_bundle_format(Path('.specfact/plans/main.bundle.yaml'))
            >>> format
            <BundleFormat.MONOLITHIC: 'monolithic'>
        """
        from specfact_cli.utils.structured_io import load_structured_file

        if path.is_file() and path.suffix in [".yaml", ".yml", ".json"]:
            # Check if it's a monolithic bundle
            try:
                data = load_structured_file(path)
                if isinstance(data, dict):
                    # Monolithic bundle has all aspects in one file
                    if "idea" in data and "product" in data and "features" in data:
                        return BundleFormat.MONOLITHIC, None
                    # Could be a bundle manifest (modular) - check for dual versioning
                    if "versions" in data and "schema" in data.get("versions", {}) and "bundle" in data:
                        return BundleFormat.MODULAR, None
            except Exception as e:
                return BundleFormat.UNKNOWN, f"Failed to parse file: {e}"
        elif path.is_dir():
            # Check for modular project bundle structure
            manifest_path = path / "bundle.manifest.yaml"
            if manifest_path.exists():
                return BundleFormat.MODULAR, None
            # Check for legacy plans directory
            if path.name == "plans" and any(f.suffix in [".yaml", ".yml", ".json"] for f in path.glob("*.bundle.*")):
                return BundleFormat.MONOLITHIC, None

        return BundleFormat.UNKNOWN, "Could not determine bundle format"

    # Phase 8.5: Bundle-Specific Artifact Organization
    # New methods for bundle-specific artifact paths

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_reports_dir(cls, bundle_name: str, base_path: Path | None = None) -> Path:
        """
        Get bundle-specific reports directory.

        Args:
            bundle_name: Project bundle name (e.g., 'legacy-api', 'auth-module')
            base_path: Base directory (default: current directory)

        Returns:
            Path to bundle reports directory (e.g., `.specfact/projects/legacy-api/reports/`)

        Examples:
            >>> SpecFactStructure.get_bundle_reports_dir("legacy-api")
            Path('.specfact/projects/legacy-api/reports')
        """
        project_dir = cls.project_dir(base_path, bundle_name)
        return project_dir / "reports"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda extension: isinstance(extension, str) and len(extension) > 0, "Extension must be non-empty string")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_brownfield_report_path(
        cls, bundle_name: str, base_path: Path | None = None, extension: str = "md"
    ) -> Path:
        """
        Get bundle-specific brownfield report path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)
            extension: File extension (default: md)

        Returns:
            Path to timestamped brownfield report in bundle folder
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        reports_dir = cls.get_bundle_reports_dir(bundle_name, base_path) / "brownfield"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"analysis-{timestamp}.{extension}"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda format: isinstance(format, str) and format in ("md", "json", "yaml"), "Format must be md/json/yaml")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_comparison_report_path(
        cls, bundle_name: str, base_path: Path | None = None, format: str = "md"
    ) -> Path:
        """
        Get bundle-specific comparison report path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)
            format: Report format (default: md)

        Returns:
            Path to timestamped comparison report in bundle folder
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        reports_dir = cls.get_bundle_reports_dir(bundle_name, base_path) / "comparison"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"report-{timestamp}.{format}"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_enrichment_report_path(cls, bundle_name: str, base_path: Path | None = None) -> Path:
        """
        Get bundle-specific enrichment report path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)

        Returns:
            Path to timestamped enrichment report in bundle folder
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        reports_dir = cls.get_bundle_reports_dir(bundle_name, base_path) / "enrichment"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"{bundle_name}-{timestamp}.enrichment.md"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_enforcement_report_path(cls, bundle_name: str, base_path: Path | None = None) -> Path:
        """
        Get bundle-specific enforcement report path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)

        Returns:
            Path to timestamped enforcement report in bundle folder
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        reports_dir = cls.get_bundle_reports_dir(bundle_name, base_path) / "enforcement"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"report-{timestamp}.yaml"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(
        lambda format: format is None or isinstance(format, StructuredFormat), "Format must be None or StructuredFormat"
    )
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_sdd_path(
        cls, bundle_name: str, base_path: Path | None = None, format: StructuredFormat | None = None
    ) -> Path:
        """
        Get bundle-specific SDD manifest path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)
            format: Preferred structured format (defaults to runtime output format)

        Returns:
            Path to SDD manifest in bundle folder (e.g., `.specfact/projects/legacy-api/sdd.yaml`)

        Examples:
            >>> SpecFactStructure.get_bundle_sdd_path("legacy-api")
            Path('.specfact/projects/legacy-api/sdd.yaml')
        """
        project_dir = cls.project_dir(base_path, bundle_name)
        format_hint = format or runtime.get_output_format()
        suffix = ".yaml" if format_hint == StructuredFormat.YAML else ".json"
        return project_dir / f"sdd{suffix}"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_tasks_path(cls, bundle_name: str, base_path: Path | None = None) -> Path:
        """
        Get bundle-specific tasks file path.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)

        Returns:
            Path to tasks file in bundle folder (e.g., `.specfact/projects/legacy-api/tasks.yaml`)

        Examples:
            >>> SpecFactStructure.get_bundle_tasks_path("legacy-api")
            Path('.specfact/projects/legacy-api/tasks.yaml')
        """
        project_dir = cls.project_dir(base_path, bundle_name)
        return project_dir / "tasks.yaml"

    @classmethod
    @beartype
    @require(
        lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0,
        "Bundle name must be non-empty string",
    )
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def get_bundle_logs_dir(cls, bundle_name: str, base_path: Path | None = None) -> Path:
        """
        Get bundle-specific logs directory.

        Args:
            bundle_name: Project bundle name
            base_path: Base directory (default: current directory)

        Returns:
            Path to logs directory in bundle folder (e.g., `.specfact/projects/legacy-api/logs/`)

        Examples:
            >>> SpecFactStructure.get_bundle_logs_dir("legacy-api")
            Path('.specfact/projects/legacy-api/logs')
        """
        project_dir = cls.project_dir(base_path, bundle_name)
        logs_dir = project_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
