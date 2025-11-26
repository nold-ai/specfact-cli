"""
Sync operations for SpecFact CLI.

This module provides bidirectional synchronization between Spec-Kit artifacts,
repository changes, and SpecFact plans.
"""

from specfact_cli.sync.bridge_probe import BridgeProbe, ToolCapabilities
from specfact_cli.sync.bridge_sync import BridgeSync, SyncOperation, SyncResult as BridgeSyncResult
from specfact_cli.sync.bridge_watch import BridgeWatch, BridgeWatchEventHandler
from specfact_cli.sync.repository_sync import RepositorySync, RepositorySyncResult
from specfact_cli.sync.speckit_sync import SpecKitSync, SyncResult
from specfact_cli.sync.watcher import FileChange, SyncEventHandler, SyncWatcher


__all__ = [
    "BridgeProbe",
    "BridgeSync",
    "BridgeSyncResult",
    "BridgeWatch",
    "BridgeWatchEventHandler",
    "FileChange",
    "RepositorySync",
    "RepositorySyncResult",
    "SpecKitSync",
    "SyncEventHandler",
    "SyncOperation",
    "SyncResult",
    "SyncWatcher",
    "ToolCapabilities",
]
