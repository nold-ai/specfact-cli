"""
Bridge-based watch mode for continuous sync operations.

This module provides watch mode functionality that uses bridge configuration
to resolve watch paths dynamically instead of hardcoded directories.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from beartype import beartype
from icontract import ensure, require


if TYPE_CHECKING:
    from watchdog.observers import Observer
else:
    from watchdog.observers import Observer

from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.sync.bridge_probe import BridgeProbe
from specfact_cli.sync.bridge_sync import BridgeSync
from specfact_cli.sync.watcher import FileChange, SyncEventHandler


class BridgeWatchEventHandler(SyncEventHandler):
    """
    Event handler for bridge-based watch mode.

    Extends SyncEventHandler to use bridge configuration for detecting
    relevant file changes.
    """

    @beartype
    def __init__(
        self,
        repo_path: Path,
        change_queue: deque[FileChange],
        bridge_config: BridgeConfig,
    ) -> None:
        """
        Initialize bridge watch event handler.

        Args:
            repo_path: Path to repository root
            change_queue: Queue to store file change events
            bridge_config: Bridge configuration for path resolution
        """
        super().__init__(repo_path, change_queue)
        self.bridge_config = bridge_config

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: result in ("spec_kit", "specfact", "code"), "Change type must be valid")
    def _detect_change_type(self, file_path: Path) -> str:
        """
        Detect change type based on bridge-resolved paths.

        Args:
            file_path: Path to changed file

        Returns:
            Change type: "spec_kit", "specfact", or "code"
        """
        path_str = str(file_path)

        # Check for SpecFact paths first (more specific)
        if ".specfact" in path_str:
            return "specfact"

        # Check if file matches bridge-resolved artifact paths
        if self.bridge_config is not None:
            # Get relative path from repo root
            try:
                relative_path = file_path.relative_to(self.repo_path)
                file_parts = list(relative_path.parts)
            except ValueError:
                # File not in repo
                return "code"

            for _artifact_key, artifact in self.bridge_config.artifacts.items():
                # Check if file matches artifact pattern
                artifact_pattern = artifact.path_pattern
                # Convert pattern to a simple path check
                # e.g., "specs/{feature_id}/spec.md" -> check if path contains "specs/" and ends with "spec.md"
                pattern_parts = artifact_pattern.split("/")

                # Check if file path structure matches pattern
                matches = True
                for i, pattern_part in enumerate(pattern_parts):
                    if pattern_part in ("{feature_id}", "{contract_name}"):
                        # Skip variable parts
                        continue
                    if i < len(file_parts) and pattern_part == file_parts[i]:
                        continue
                    matches = False
                    break

                if matches:
                    return "spec_kit"

        # Code changes (default)
        return "code"


class BridgeWatch:
    """
    Bridge-based watch mode for continuous sync operations.

    Uses bridge configuration to resolve watch paths dynamically instead of
    hardcoded directories. This allows watching different directory structures
    (e.g., `docs/specs/` vs `specs/`) based on bridge configuration.
    """

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @require(lambda interval: isinstance(interval, (int, float)) and interval >= 1, "Interval must be >= 1")
    @require(
        lambda sync_callback: callable(sync_callback) or sync_callback is None,
        "Sync callback must be callable or None",
    )
    def __init__(
        self,
        repo_path: Path,
        bridge_config: BridgeConfig | None = None,
        bundle_name: str | None = None,
        sync_callback: Callable[[list[FileChange]], None] | None = None,
        interval: int = 5,
    ) -> None:
        """
        Initialize bridge watch mode.

        Args:
            repo_path: Path to repository root
            bridge_config: Bridge configuration (auto-detected if None)
            bundle_name: Project bundle name for sync operations
            sync_callback: Callback function to handle sync operations (optional)
            interval: Watch interval in seconds (default: 5)
        """
        self.repo_path = Path(repo_path).resolve()
        self.bridge_config = bridge_config
        self.bundle_name = bundle_name
        self.sync_callback = sync_callback
        self.interval = interval
        self.observer: Observer | None = None  # type: ignore[assignment]
        self.change_queue: deque[FileChange] = deque()
        self.running = False
        self.bridge_sync: BridgeSync | None = None

        if self.bridge_config is None:
            # Auto-detect and load bridge config
            self.bridge_config = self._load_or_generate_bridge_config()

        if self.bundle_name and self.sync_callback is None:
            # Create default sync callback using BridgeSync
            self.bridge_sync = BridgeSync(self.repo_path, bridge_config=self.bridge_config)
            self.sync_callback = self._create_default_sync_callback()

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _load_or_generate_bridge_config(self) -> BridgeConfig:
        """
        Load bridge config from file or auto-generate if missing.

        Returns:
            BridgeConfig instance
        """
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_path = self.repo_path / SpecFactStructure.CONFIG / "bridge.yaml"

        if bridge_path.exists():
            return BridgeConfig.load_from_file(bridge_path)

        # Auto-generate bridge config
        probe = BridgeProbe(self.repo_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)
        probe.save_bridge_config(bridge_config, overwrite=False)
        return bridge_config

    @beartype
    @require(lambda self: self.bundle_name is not None, "Bundle name must be set for default sync callback")
    @ensure(lambda result: callable(result), "Must return callable")
    def _create_default_sync_callback(self) -> Callable[[list[FileChange]], None]:
        """
        Create default sync callback using BridgeSync.

        Returns:
            Sync callback function
        """
        if self.bridge_sync is None or self.bundle_name is None:
            msg = "Bridge sync and bundle name must be set"
            raise ValueError(msg)

        def sync_callback(changes: list[FileChange]) -> None:
            """Default sync callback that imports changed artifacts."""
            if not changes:
                return

            # Group changes by artifact type
            artifact_changes: dict[str, list[str]] = {}  # artifact_key -> [feature_ids]
            for change in changes:
                if change.change_type == "spec_kit" and change.event_type in ("created", "modified"):
                    # Extract feature_id from path (simplified - could be enhanced)
                    feature_id = self._extract_feature_id_from_path(change.file_path)
                    if feature_id:
                        # Determine artifact key from file path
                        artifact_key = self._determine_artifact_key(change.file_path)
                        if artifact_key:
                            if artifact_key not in artifact_changes:
                                artifact_changes[artifact_key] = []
                            if feature_id not in artifact_changes[artifact_key]:
                                artifact_changes[artifact_key].append(feature_id)

            # Import changed artifacts
            if self.bridge_sync is None or self.bundle_name is None:
                return

            for artifact_key, feature_ids in artifact_changes.items():
                for feature_id in feature_ids:
                    try:
                        result = self.bridge_sync.import_artifact(artifact_key, feature_id, self.bundle_name)
                        if result.success:
                            print(f"✓ Imported {artifact_key} for {feature_id}")
                        else:
                            print(f"✗ Failed to import {artifact_key} for {feature_id}: {', '.join(result.errors)}")
                    except Exception as e:
                        print(f"✗ Error importing {artifact_key} for {feature_id}: {e}")

        return sync_callback

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, str) or result is None, "Must return string or None")
    def _extract_feature_id_from_path(self, file_path: Path) -> str | None:
        """
        Extract feature ID from file path.

        Args:
            file_path: Path to file

        Returns:
            Feature ID if found, None otherwise
        """
        if self.bridge_config is None:
            return None

        # Try to match against bridge artifact patterns
        file_parts = list(file_path.parts)
        # Remove repo_path parts from file_parts for comparison
        try:
            relative_path = file_path.relative_to(self.repo_path)
            file_parts = list(relative_path.parts)
        except ValueError:
            # File not in repo, can't extract
            return None

        for _artifact_key, artifact in self.bridge_config.artifacts.items():
            pattern = artifact.path_pattern
            # Simple extraction (could be enhanced with regex)
            if "{feature_id}" in pattern:
                # Extract feature_id from path (e.g., "specs/001-auth/spec.md" -> "001-auth")
                # Pattern format: "specs/{feature_id}/spec.md" or "docs/specs/{feature_id}/spec.md"
                pattern_parts = pattern.split("/")

                # Find where {feature_id} appears in pattern
                try:
                    feature_id_index = pattern_parts.index("{feature_id}")
                    # Find corresponding part in file path
                    # Match pattern parts before {feature_id} to file path
                    if feature_id_index < len(file_parts):
                        # Check if preceding parts match
                        matches = True
                        for i in range(feature_id_index):
                            if i < len(file_parts) and pattern_parts[i] != file_parts[i]:
                                matches = False
                                break
                        if matches and feature_id_index < len(file_parts):
                            return file_parts[feature_id_index]
                except ValueError:
                    # {feature_id} not in pattern
                    continue
        return None

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, str) or result is None, "Must return string or None")
    def _determine_artifact_key(self, file_path: Path) -> str | None:
        """
        Determine artifact key from file path.

        Args:
            file_path: Path to file

        Returns:
            Artifact key if found, None otherwise
        """
        if self.bridge_config is None:
            return None

        file_name = file_path.name

        # Map common file names to artifact keys
        file_to_artifact = {
            "spec.md": "specification",
            "plan.md": "plan",
            "tasks.md": "tasks",
        }

        if file_name in file_to_artifact:
            artifact_key = file_to_artifact[file_name]
            if artifact_key in self.bridge_config.artifacts:
                return artifact_key

        return None

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _resolve_watch_paths(self) -> list[Path]:
        """
        Resolve watch paths from bridge artifact mappings.

        Returns:
            List of paths to watch
        """
        watch_paths: list[Path] = []

        if self.bridge_config is None:
            return watch_paths

        # Collect base directories from artifact patterns
        base_dirs: set[Path] = set()
        for artifact in self.bridge_config.artifacts.values():
            pattern = artifact.path_pattern
            # Extract base directory from pattern (e.g., "specs/{feature_id}/spec.md" -> "specs")
            # or "docs/specs/{feature_id}/spec.md" -> "docs/specs"
            pattern_parts = pattern.split("/")
            if len(pattern_parts) > 0:
                # Build path up to {feature_id} (or all parts if no {feature_id})
                base_parts: list[str] = []
                for part in pattern_parts:
                    if part == "{feature_id}" or part == "{contract_name}":
                        break
                    base_parts.append(part)
                if base_parts:
                    base_dir = self.repo_path / Path(*base_parts)
                    if base_dir.exists():
                        base_dirs.add(base_dir)

        # Also watch .specfact directory for bundle changes
        specfact_dir = self.repo_path / ".specfact"
        if specfact_dir.exists():
            base_dirs.add(specfact_dir)

        return list(base_dirs)

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def start(self) -> None:
        """Start watching for file system changes."""
        if self.running:
            print("Watcher is already running")
            return

        if self.bridge_config is None:
            print("Bridge config not initialized")
            return

        watch_paths = self._resolve_watch_paths()

        if not watch_paths:
            print("No watch paths found. Check bridge configuration.")
            return

        observer = Observer()
        handler = BridgeWatchEventHandler(self.repo_path, self.change_queue, self.bridge_config)

        # Watch all resolved paths
        for watch_path in watch_paths:
            observer.schedule(handler, str(watch_path), recursive=True)

        observer.start()

        self.observer = observer
        self.running = True
        print(f"Watching for changes in: {', '.join(str(p) for p in watch_paths)}")

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def stop(self) -> None:
        """Stop watching for file system changes."""
        if not self.running:
            return

        self.running = False

        if self.observer is not None:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None

        print("Watch mode stopped")

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def watch(self) -> None:
        """
        Continuously watch and sync changes.

        This method blocks until interrupted (Ctrl+C).
        """
        self.start()

        try:
            while self.running:
                time.sleep(self.interval)
                self._process_pending_changes()
        except KeyboardInterrupt:
            print("\nStopping watch mode...")
        finally:
            self.stop()

    @beartype
    @require(lambda self: isinstance(self.running, bool), "Watcher running state must be bool")
    @ensure(lambda result: result is None, "Must return None")
    def _process_pending_changes(self) -> None:
        """Process pending file changes and trigger sync."""
        if not self.change_queue:
            return

        # Collect all pending changes
        changes: list[FileChange] = []
        while self.change_queue:
            changes.append(self.change_queue.popleft())

        if changes and self.sync_callback:
            print(f"Detected {len(changes)} file change(s), triggering sync...")
            try:
                self.sync_callback(changes)
            except Exception as e:
                print(f"Sync callback failed: {e}")
