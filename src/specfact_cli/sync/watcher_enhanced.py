"""
Enhanced file system watcher with hash-based change detection, dependency tracking, and LZ4 cache.

This module provides enhanced watch mode capabilities including:
- Hash-based change detection (only process files that actually changed)
- Dependency tracking (track file dependencies for incremental processing)
- LZ4 compression for cache (optional, faster cache I/O)
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from beartype import beartype
from icontract import ensure, require


# Optional LZ4 support
try:
    import lz4.frame  # type: ignore[import-untyped]

    LZ4_AVAILABLE = True
    LZ4_FRAME = lz4.frame  # type: ignore[possibly-unbound]
except ImportError:
    LZ4_AVAILABLE = False
    LZ4_FRAME = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
else:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

from specfact_cli.utils import print_info, print_warning


@dataclass
class FileChange:
    """Represents a file system change event with hash information."""

    file_path: Path
    change_type: str  # "spec_kit", "specfact", "code"
    event_type: str  # "created", "modified", "deleted"
    timestamp: float
    file_hash: str | None = None  # SHA256 hash of file content
    dependencies: list[Path] = field(default_factory=list)  # Dependent files

    @beartype
    def __post_init__(self) -> None:
        """Validate file change data."""
        if self.change_type not in ("spec_kit", "specfact", "code"):
            msg = f"Invalid change_type: {self.change_type}. Must be spec_kit, specfact, or code"
            raise ValueError(msg)
        if self.event_type not in ("created", "modified", "deleted"):
            msg = f"Invalid event_type: {self.event_type}. Must be created, modified, or deleted"
            raise ValueError(msg)


@dataclass
class FileHashCache:
    """Cache for file hashes to detect actual changes."""

    cache_file: Path
    hashes: dict[str, str] = field(default_factory=dict)  # file_path -> hash
    dependencies: dict[str, list[str]] = field(default_factory=dict)  # file_path -> [dependencies]

    @beartype
    def load(self) -> None:
        """Load hash cache from disk."""
        if not self.cache_file.exists():
            return

        try:
            if LZ4_AVAILABLE and LZ4_FRAME is not None:
                # Try LZ4-compressed cache first
                lz4_file = self.cache_file.with_suffix(".lz4")
                if lz4_file.exists():
                    with lz4_file.open("rb") as f:
                        compressed = f.read()
                        data = json.loads(LZ4_FRAME.decompress(compressed).decode("utf-8"))  # type: ignore[union-attr]
                        self.hashes = data.get("hashes", {})
                        self.dependencies = data.get("dependencies", {})
                        return

            # Fallback to uncompressed JSON
            with self.cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                self.hashes = data.get("hashes", {})
                self.dependencies = data.get("dependencies", {})
        except Exception as e:
            print_warning(f"Failed to load hash cache: {e}")

    @beartype
    def save(self) -> None:
        """Save hash cache to disk."""
        try:
            data = {"hashes": self.hashes, "dependencies": self.dependencies}
            json_str = json.dumps(data, indent=2)

            if LZ4_AVAILABLE and LZ4_FRAME is not None:
                # Save as LZ4-compressed
                lz4_file = self.cache_file.with_suffix(".lz4")
                compressed = LZ4_FRAME.compress(json_str.encode("utf-8"))  # type: ignore[union-attr]
                with lz4_file.open("wb") as f:
                    f.write(compressed)
                # Also save uncompressed for compatibility
                with self.cache_file.open("w", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                # Save as uncompressed JSON
                with self.cache_file.open("w", encoding="utf-8") as f:
                    f.write(json_str)
        except Exception as e:
            print_warning(f"Failed to save hash cache: {e}")

    @beartype
    def get_hash(self, file_path: Path) -> str | None:
        """Get cached hash for a file."""
        return self.hashes.get(str(file_path))

    @beartype
    def set_hash(self, file_path: Path, file_hash: str) -> None:
        """Set hash for a file."""
        self.hashes[str(file_path)] = file_hash

    @beartype
    def get_dependencies(self, file_path: Path) -> list[Path]:
        """Get dependencies for a file."""
        deps = self.dependencies.get(str(file_path), [])
        return [Path(d) for d in deps]

    @beartype
    def set_dependencies(self, file_path: Path, dependencies: list[Path]) -> None:
        """Set dependencies for a file."""
        self.dependencies[str(file_path)] = [str(d) for d in dependencies]

    @beartype
    def has_changed(self, file_path: Path, current_hash: str) -> bool:
        """Check if file has changed based on hash."""
        cached_hash = self.get_hash(file_path)
        return cached_hash is None or cached_hash != current_hash


@beartype
def compute_file_hash(file_path: Path) -> str | None:
    """
    Compute SHA256 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash as hex string, or None if file doesn't exist or can't be read
    """
    if not file_path.exists() or not file_path.is_file():
        return None

    try:
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            # Read in chunks to handle large files
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


class EnhancedSyncEventHandler(FileSystemEventHandler):
    """Enhanced event handler with hash-based change detection and dependency tracking."""

    @beartype
    def __init__(
        self,
        repo_path: Path,
        change_queue: deque[FileChange],
        hash_cache: FileHashCache,
        debounce_interval: float = 0.5,
    ) -> None:
        """
        Initialize enhanced event handler.

        Args:
            repo_path: Path to repository root
            change_queue: Queue to store file change events
            hash_cache: Hash cache for change detection
            debounce_interval: Debounce interval in seconds (default: 0.5)
        """
        self.repo_path = Path(repo_path).resolve()
        self.change_queue = change_queue
        self.hash_cache = hash_cache
        self.debounce_interval = debounce_interval
        self.last_event_time: dict[str, float] = {}

    @beartype
    @require(lambda self, event: event is not None, "Event must not be None")
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if hasattr(event, "is_directory") and event.is_directory:
            return

        self._queue_change(event, "modified")

    @beartype
    @require(lambda self, event: event is not None, "Event must not be None")
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if hasattr(event, "is_directory") and event.is_directory:
            return

        self._queue_change(event, "created")

    @beartype
    @require(lambda self, event: event is not None, "Event must not be None")
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if hasattr(event, "is_directory") and event.is_directory:
            return

        self._queue_change(event, "deleted")

    @beartype
    @require(
        lambda self, event, event_type: event is not None,
        "Event must not be None",
    )
    @require(
        lambda self, event, event_type: event_type in ("created", "modified", "deleted"),
        "Event type must be created, modified, or deleted",
    )
    @ensure(lambda result: result is None, "Must return None")
    def _queue_change(self, event: FileSystemEvent, event_type: str) -> None:
        """Queue a file change event with debouncing and hash-based detection."""
        if not hasattr(event, "src_path"):
            return

        file_path = Path(str(event.src_path))

        # Skip if not in repository
        try:
            file_path.resolve().relative_to(self.repo_path)
        except ValueError:
            return

        # Debounce rapid changes to same file
        file_key = str(file_path)
        current_time = time.time()
        last_time = self.last_event_time.get(file_key, 0)

        if current_time - last_time < self.debounce_interval:
            return

        self.last_event_time[file_key] = current_time

        # For deleted files, we can't compute hash
        if event_type == "deleted":
            change = FileChange(
                file_path=file_path,
                change_type=self._detect_change_type(file_path),
                event_type=event_type,
                timestamp=current_time,
                file_hash=None,
            )
            self.change_queue.append(change)
            return

        # Compute hash for created/modified files
        file_hash = compute_file_hash(file_path)

        # Only queue if file actually changed (hash-based detection)
        if file_hash and self.hash_cache.has_changed(file_path, file_hash):
            # Update cache
            self.hash_cache.set_hash(file_path, file_hash)

            # Get dependencies (simplified - could be enhanced with AST analysis)
            dependencies = self._detect_dependencies(file_path)

            change = FileChange(
                file_path=file_path,
                change_type=self._detect_change_type(file_path),
                event_type=event_type,
                timestamp=current_time,
                file_hash=file_hash,
                dependencies=dependencies,
            )

            self.change_queue.append(change)

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: result in ("spec_kit", "specfact", "code"), "Change type must be valid")
    def _detect_change_type(self, file_path: Path) -> str:
        """
        Detect change type based on file path.

        Args:
            file_path: Path to changed file

        Returns:
            Change type: "spec_kit", "specfact", or "code"
        """
        path_str = str(file_path)

        # Spec-Kit artifacts
        if ".specify" in path_str or "/specs/" in path_str:
            return "spec_kit"

        # SpecFact artifacts
        if ".specfact" in path_str:
            return "specfact"

        # Code changes (default)
        return "code"

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _detect_dependencies(self, file_path: Path) -> list[Path]:
        """
        Detect file dependencies (simplified implementation).

        This is a basic implementation. For Python files, could use AST analysis.
        For now, we return cached dependencies or empty list.

        Args:
            file_path: Path to file

        Returns:
            List of dependent file paths
        """
        # Return cached dependencies if available
        cached_deps = self.hash_cache.get_dependencies(file_path)
        if cached_deps:
            return cached_deps

        # Basic dependency detection for Python files
        if file_path.suffix == ".py":
            # Could enhance with AST analysis here
            # For now, return empty list
            return []

        return []


class EnhancedSyncWatcher:
    """Enhanced watch mode with hash-based change detection, dependency tracking, and LZ4 cache."""

    @beartype
    @require(
        lambda repo_path: isinstance(repo_path, Path) and bool(repo_path.exists()),
        "Repository path must exist",
    )
    @require(
        lambda repo_path: isinstance(repo_path, Path) and bool(repo_path.is_dir()),
        "Repository path must be a directory",
    )
    @require(lambda interval: isinstance(interval, (int, float)) and interval >= 1, "Interval must be >= 1")
    @require(
        lambda sync_callback: callable(sync_callback),
        "Sync callback must be callable",
    )
    @ensure(lambda result: result is None, "Must return None")
    def __init__(
        self,
        repo_path: Path,
        sync_callback: Callable[[list[FileChange]], None],
        interval: int = 5,
        debounce_interval: float = 0.5,
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize enhanced sync watcher.

        Args:
            repo_path: Path to repository root
            sync_callback: Callback function to handle sync operations
            interval: Watch interval in seconds (default: 5)
            debounce_interval: Debounce interval in seconds (default: 0.5)
            cache_dir: Directory for hash cache (default: .specfact/.cache)
        """
        self.repo_path = Path(repo_path).resolve()
        self.sync_callback = sync_callback
        self.interval = interval
        self.debounce_interval = debounce_interval
        self.observer: Observer | None = None  # type: ignore[assignment]
        self.change_queue: deque[FileChange] = deque()
        self.running = False

        # Initialize hash cache
        if cache_dir is None:
            cache_dir = self.repo_path / ".specfact" / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "file_hashes.json"
        self.hash_cache = FileHashCache(cache_file=cache_file)
        self.hash_cache.load()

        if LZ4_AVAILABLE:
            print_info("LZ4 compression available for cache (faster I/O)")

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def start(self) -> None:
        """Start watching for file system changes."""
        if self.running:
            print_warning("Watcher is already running")
            return

        observer = Observer()
        handler = EnhancedSyncEventHandler(self.repo_path, self.change_queue, self.hash_cache, self.debounce_interval)
        observer.schedule(handler, str(self.repo_path), recursive=True)
        observer.start()

        self.observer = observer
        self.running = True
        print_info(f"Watching for changes in: {self.repo_path}")
        print_info(f"Sync interval: {self.interval} seconds")
        print_info(f"Debounce interval: {self.debounce_interval} seconds")
        print_info("Press Ctrl+C to stop")

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def stop(self) -> None:
        """Stop watching for file system changes."""
        if not self.running:
            return

        self.running = False

        observer: Observer | None = self.observer  # type: ignore[assignment]
        if observer is not None:
            observer.stop()  # type: ignore[unknown-member-type]
            observer.join(timeout=5)  # type: ignore[unknown-member-type]
            self.observer = None

        # Save hash cache
        self.hash_cache.save()

        print_info("Watch mode stopped")

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
            print_info("\nStopping watch mode...")
        finally:
            self.stop()

    @beartype
    @require(
        lambda self: hasattr(self, "running") and isinstance(getattr(self, "running", False), bool),
        "Watcher running state must be bool",
    )
    @ensure(lambda result: result is None, "Must return None")
    def _process_pending_changes(self) -> None:
        """Process pending file changes and trigger sync (incremental processing)."""
        if not self.change_queue:
            return

        # Collect all pending changes (incremental - only changed files)
        changes: list[FileChange] = []
        while self.change_queue:
            changes.append(self.change_queue.popleft())

        if changes:
            # Filter to only files that actually changed (hash-based)
            actual_changes = [c for c in changes if c.file_hash is not None or c.event_type == "deleted"]
            if actual_changes:
                print_info(f"Detected {len(actual_changes)} file change(s) (hash-verified), triggering sync...")
                try:
                    self.sync_callback(actual_changes)
                    # Save cache after processing
                    self.hash_cache.save()
                except Exception as e:
                    print_warning(f"Sync callback failed: {e}")
