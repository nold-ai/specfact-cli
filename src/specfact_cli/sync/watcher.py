"""File system watcher for continuous sync operations."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from beartype import beartype
from icontract import ensure, require


if TYPE_CHECKING:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
else:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

from specfact_cli.utils import print_info, print_warning


@dataclass
class FileChange:
    """Represents a file system change event."""

    file_path: Path
    change_type: str  # "spec_kit", "specfact", "code"
    event_type: str  # "created", "modified", "deleted"
    timestamp: float

    @beartype
    def __post_init__(self) -> None:
        """Validate file change data."""
        if self.change_type not in ("spec_kit", "specfact", "code"):
            msg = f"Invalid change_type: {self.change_type}. Must be spec_kit, specfact, or code"
            raise ValueError(msg)
        if self.event_type not in ("created", "modified", "deleted"):
            msg = f"Invalid event_type: {self.event_type}. Must be created, modified, or deleted"
            raise ValueError(msg)


class SyncEventHandler(FileSystemEventHandler):
    """Event handler for file system changes during sync operations."""

    @beartype
    def __init__(self, repo_path: Path, change_queue: deque[FileChange]) -> None:
        """
        Initialize event handler.

        Args:
            repo_path: Path to repository root
            change_queue: Queue to store file change events
        """
        self.repo_path = Path(repo_path).resolve()
        self.change_queue = change_queue
        self.last_event_time: dict[str, float] = {}
        self.debounce_interval = 0.5  # Debounce rapid file changes (500ms)

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
        """Queue a file change event with debouncing."""
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

        # Determine change type based on file path
        change_type = self._detect_change_type(file_path)

        # Queue change
        change = FileChange(
            file_path=file_path,
            change_type=change_type,
            event_type=event_type,
            timestamp=current_time,
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


class SyncWatcher:
    """Watch mode for continuous sync operations."""

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
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
    ) -> None:
        """
        Initialize sync watcher.

        Args:
            repo_path: Path to repository root
            sync_callback: Callback function to handle sync operations
            interval: Watch interval in seconds (default: 5)
        """
        self.repo_path = Path(repo_path).resolve()
        self.sync_callback = sync_callback
        self.interval = interval
        self.observer: Observer | None = None  # type: ignore[assignment]
        self.change_queue: deque[FileChange] = deque()
        self.running = False

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def start(self) -> None:
        """Start watching for file system changes."""
        if self.running:
            print_warning("Watcher is already running")
            return

        observer = Observer()
        handler = SyncEventHandler(self.repo_path, self.change_queue)
        observer.schedule(handler, str(self.repo_path), recursive=True)
        observer.start()

        self.observer = observer
        self.running = True
        print_info(f"Watching for changes in: {self.repo_path}")
        print_info(f"Sync interval: {self.interval} seconds")
        print_info("Press Ctrl+C to stop")

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

        if changes:
            print_info(f"Detected {len(changes)} file change(s), triggering sync...")
            try:
                self.sync_callback(changes)
            except Exception as e:
                print_warning(f"Sync callback failed: {e}")
