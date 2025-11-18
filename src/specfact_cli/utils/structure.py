"""SpecFact directory structure utilities."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from beartype import beartype
from icontract import ensure, require


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
    PROTOCOLS = f"{ROOT}/protocols"

    # Ephemeral directories (gitignored)
    REPORTS = f"{ROOT}/reports"
    REPORTS_BROWNFIELD = f"{ROOT}/reports/brownfield"
    REPORTS_COMPARISON = f"{ROOT}/reports/comparison"
    REPORTS_ENFORCEMENT = f"{ROOT}/reports/enforcement"
    REPORTS_ENRICHMENT = f"{ROOT}/reports/enrichment"
    GATES_RESULTS = f"{ROOT}/gates/results"
    CACHE = f"{ROOT}/cache"

    # Configuration files
    CONFIG = f"{ROOT}/config.yaml"
    GATES_CONFIG = f"{ROOT}/gates/config.yaml"
    ENFORCEMENT_CONFIG = f"{ROOT}/gates/config/enforcement.yaml"

    # Default plan names
    DEFAULT_PLAN = f"{ROOT}/plans/main.bundle.yaml"
    BROWNFIELD_PLAN = f"{ROOT}/plans/auto-derived.yaml"
    PLANS_CONFIG = f"{ROOT}/plans/config.yaml"

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
            # Normalize to absolute path and ensure we're not inside .specfact
            base_path = Path(base_path).resolve()
            # If base_path contains .specfact, find the repository root
            parts = base_path.parts
            if ".specfact" in parts:
                # Find the index of .specfact and go up to repository root
                specfact_idx = parts.index(".specfact")
                base_path = Path(*parts[:specfact_idx])

        # Create versioned directories
        (base_path / cls.PLANS).mkdir(parents=True, exist_ok=True)
        (base_path / cls.PROTOCOLS).mkdir(parents=True, exist_ok=True)
        (base_path / f"{cls.ROOT}/gates/config").mkdir(parents=True, exist_ok=True)

        # Create ephemeral directories
        (base_path / cls.REPORTS_BROWNFIELD).mkdir(parents=True, exist_ok=True)
        (base_path / cls.REPORTS_COMPARISON).mkdir(parents=True, exist_ok=True)
        (base_path / cls.REPORTS_ENFORCEMENT).mkdir(parents=True, exist_ok=True)
        (base_path / cls.REPORTS_ENRICHMENT).mkdir(parents=True, exist_ok=True)
        (base_path / cls.GATES_RESULTS).mkdir(parents=True, exist_ok=True)
        (base_path / cls.CACHE).mkdir(parents=True, exist_ok=True)

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
    def get_default_plan_path(cls, base_path: Path | None = None) -> Path:
        """
        Get path to active plan bundle (from config or fallback to main.bundle.yaml).

        Args:
            base_path: Base directory (default: current directory)

        Returns:
            Path to active plan bundle (from config or default)
        """
        if base_path is None:
            base_path = Path(".")

        # Try to read active plan from config
        config_path = base_path / cls.PLANS_CONFIG
        if config_path.exists():
            try:
                import yaml

                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
                active_plan = config.get("active_plan")
                if active_plan:
                    plan_path = base_path / cls.PLANS / active_plan
                    if plan_path.exists():
                        return plan_path
            except Exception:
                # Fallback to default if config read fails
                pass

        # Fallback to default plan
        return base_path / cls.DEFAULT_PLAN

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @require(lambda plan_name: isinstance(plan_name, str) and len(plan_name) > 0, "Plan name must be non-empty string")
    @ensure(lambda result: result is None, "Must return None")
    def set_active_plan(cls, plan_name: str, base_path: Path | None = None) -> None:
        """
        Set the active plan in the plans config.

        Args:
            plan_name: Name of the plan file (e.g., "main.bundle.yaml", "specfact-cli.2025-11-04T23-35-00.bundle.yaml")
            base_path: Base directory (default: current directory)

        Examples:
            >>> SpecFactStructure.set_active_plan("specfact-cli.2025-11-04T23-35-00.bundle.yaml")
            >>> SpecFactStructure.get_default_plan_path()
            Path('.specfact/plans/specfact-cli.2025-11-04T23-35-00.bundle.yaml')
        """
        if base_path is None:
            base_path = Path(".")

        import yaml

        config_path = base_path / cls.PLANS_CONFIG
        plans_dir = base_path / cls.PLANS

        # Ensure plans directory exists
        plans_dir.mkdir(parents=True, exist_ok=True)

        # Read existing config or create new
        config = {}
        if config_path.exists():
            try:
                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                config = {}

        # Update active plan
        config["active_plan"] = plan_name

        # Write config
        with config_path.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_plans(cls, base_path: Path | None = None) -> list[dict[str, str | int]]:
        """
        List all available plan bundles with metadata.

        Args:
            base_path: Base directory (default: current directory)

        Returns:
            List of plan dictionaries with 'name', 'path', 'features', 'stories', 'size', 'modified' keys

        Examples:
            >>> plans = SpecFactStructure.list_plans()
            >>> plans[0]['name']
            'specfact-cli.2025-11-04T23-35-00.bundle.yaml'
        """
        if base_path is None:
            base_path = Path(".")

        plans_dir = base_path / cls.PLANS
        if not plans_dir.exists():
            return []

        from datetime import datetime

        import yaml

        plans = []
        active_plan = None

        # Get active plan from config
        config_path = base_path / cls.PLANS_CONFIG
        if config_path.exists():
            try:
                with config_path.open() as f:
                    config = yaml.safe_load(f) or {}
                active_plan = config.get("active_plan")
            except Exception:
                pass

        # Find all plan bundles, sorted by modification date (oldest first, newest last)
        plan_files = list(plans_dir.glob("*.bundle.yaml"))
        plan_files_sorted = sorted(plan_files, key=lambda p: p.stat().st_mtime, reverse=False)
        for plan_file in plan_files_sorted:
            if plan_file.name == "config.yaml":
                continue

            plan_info: dict[str, str | int] = {
                "name": plan_file.name,
                "path": str(plan_file.relative_to(base_path)),
                "features": 0,
                "stories": 0,
                "size": plan_file.stat().st_size,
                "modified": datetime.fromtimestamp(plan_file.stat().st_mtime).isoformat(),
                "active": plan_file.name == active_plan,
            }

            # Try to load plan metadata
            try:
                with plan_file.open() as f:
                    plan_data = yaml.safe_load(f) or {}
                    features = plan_data.get("features", [])
                    plan_info["features"] = len(features)
                    plan_info["stories"] = sum(len(f.get("stories", [])) for f in features)
                    if plan_data.get("metadata"):
                        plan_info["stage"] = plan_data["metadata"].get("stage", "draft")
                    else:
                        plan_info["stage"] = "draft"
            except Exception:
                plan_info["stage"] = "unknown"

            plans.append(plan_info)

        return plans

    @classmethod
    def get_enforcement_config_path(cls, base_path: Path | None = None) -> Path:
        """Get path to enforcement configuration file."""
        if base_path is None:
            base_path = Path(".")
        return base_path / cls.ENFORCEMENT_CONFIG

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
    def get_timestamped_brownfield_report(cls, base_path: Path | None = None, name: str | None = None) -> Path:
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
        sanitized_name = cls.sanitize_plan_name(name)
        directory = base_path / cls.PLANS
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{sanitized_name}.{timestamp}.bundle.yaml"

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

        # Extract filename from plan bundle path
        plan_filename = plan_bundle_path.name

        # Replace .bundle.yaml with .enrichment.md
        if plan_filename.endswith(".bundle.yaml"):
            enrichment_filename = plan_filename.replace(".bundle.yaml", ".enrichment.md")
        else:
            # Fallback: append .enrichment.md if pattern doesn't match
            enrichment_filename = f"{plan_bundle_path.stem}.enrichment.md"

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

        # Replace .enrichment.md with .bundle.yaml
        if enrichment_filename.endswith(".enrichment.md"):
            plan_filename = enrichment_filename.replace(".enrichment.md", ".bundle.yaml")
        else:
            # Fallback: try to construct from stem
            plan_filename = f"{enrichment_report_path.stem}.bundle.yaml"

        plan_path = base_path / cls.PLANS / plan_filename
        return plan_path if plan_path.exists() else None

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

        # Extract name and original timestamp from filename
        # Format: <name>.<timestamp>.bundle.yaml
        if original_filename.endswith(".bundle.yaml"):
            name_with_timestamp = original_filename.replace(".bundle.yaml", "")
            # Split name and timestamp (timestamp is after last dot before .bundle.yaml)
            # Pattern: <name>.<timestamp> -> we want to insert .enriched.<new-timestamp>
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
            enriched_filename = f"{name_part}.{original_timestamp}.enriched.{enrichment_timestamp}.bundle.yaml"
        else:
            enriched_filename = f"{name_part}.enriched.{enrichment_timestamp}.bundle.yaml"

        directory = base_path / cls.PLANS
        directory.mkdir(parents=True, exist_ok=True)
        return directory / enriched_filename

    @classmethod
    @beartype
    @require(lambda base_path: base_path is None or isinstance(base_path, Path), "Base path must be None or Path")
    @ensure(lambda result: result is None or isinstance(result, Path), "Must return None or Path")
    def get_latest_brownfield_report(cls, base_path: Path | None = None) -> Path | None:
        """
        Get the latest brownfield report from the plans directory.

        Args:
            base_path: Base directory (default: current directory)

        Returns:
            Path to latest brownfield report, or None if none exist
        """
        if base_path is None:
            base_path = Path(".")

        plans_dir = base_path / cls.PLANS
        if not plans_dir.exists():
            return None

        # Find all auto-derived reports
        reports = sorted(plans_dir.glob("auto-derived.*.bundle.yaml"), reverse=True)
        return reports[0] if reports else None

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
gates/results/
cache/

# Keep these versioned
!plans/
!protocols/
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
