#!/usr/bin/env python3
"""Export OpenSpec change proposals to GitHub issues via specfact project sync bridge.

This wrapper standardizes the common OpenSpec->GitHub export command and adds a
friendly `--inplace-update` option that maps to `--update-existing`.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ViolationError, ensure, require


logger = logging.getLogger(__name__)


@beartype
@require(lambda change_ids: len(change_ids) > 0, "At least one change id is required")
def build_export_command(
    *,
    repo: Path,
    change_ids: list[str],
    repo_owner: str | None,
    repo_name: str | None,
    inplace_update: bool,
) -> list[str]:
    """Build `specfact project sync bridge` command for GitHub export."""
    cleaned_ids = [item.strip() for item in change_ids if item.strip()]
    if not cleaned_ids:
        raise ViolationError("At least one non-empty change id is required")

    command = [
        "specfact",
        "project",
        "sync",
        "bridge",
        "--adapter",
        "github",
        "--mode",
        "export-only",
        "--change-ids",
        ",".join(cleaned_ids),
        "--repo",
        str(repo),
    ]

    if repo_owner:
        command.extend(["--repo-owner", repo_owner])
    if repo_name:
        command.extend(["--repo-name", repo_name])
    if inplace_update:
        command.append("--update-existing")

    return command


@beartype
def _parse_change_ids(args: argparse.Namespace) -> list[str]:
    values: list[str] = []
    if args.change_id:
        values.append(args.change_id.strip())
    if args.change_ids:
        values.extend(part.strip() for part in args.change_ids.split(","))
    return [item for item in values if item]


@beartype
@require(lambda argv: argv is None or isinstance(argv, list), "argv must be a list or None")
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description=(
            "Export OpenSpec change proposal(s) to GitHub via `specfact project sync bridge` "
            "with optional in-place issue update."
        )
    )
    parser.add_argument("--change-id", help="Single OpenSpec change id to export")
    parser.add_argument("--change-ids", help="Comma-separated OpenSpec change ids to export")
    parser.add_argument("--repo", default=".", help="OpenSpec repository path (default: current directory)")
    parser.add_argument("--repo-owner", help="GitHub repository owner (optional; auto-detected when possible)")
    parser.add_argument("--repo-name", help="GitHub repository name (optional; auto-detected when possible)")
    parser.add_argument(
        "--inplace-update",
        action="store_true",
        help="Update existing linked GitHub issue(s) in place (maps to --update-existing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command without executing",
    )

    args = parser.parse_args(argv)
    change_ids = _parse_change_ids(args)
    if not change_ids:
        parser.error("Provide --change-id or --change-ids")

    command = build_export_command(
        repo=Path(args.repo).expanduser().resolve(),
        change_ids=change_ids,
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        inplace_update=args.inplace_update,
    )

    logger.info("Resolved command:")
    logger.info("%s", " ".join(command))

    if args.dry_run:
        return 0

    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
