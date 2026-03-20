#!/usr/bin/env python3
"""
Profile contract extraction to identify bottlenecks.

This script helps diagnose performance issues in contract extraction.
"""

import cProfile
import logging
import pstats
import time
from io import StringIO
from pathlib import Path

import yaml
from beartype import beartype
from icontract import require

from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


logger = logging.getLogger(__name__)


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "repo_path must be a Path")
def profile_extraction(repo_path: Path, feature: Feature) -> None:
    """Profile a single feature extraction."""
    extractor = OpenAPIExtractor(repo_path)

    profiler = cProfile.Profile()
    profiler.enable()

    start = time.time()
    result = extractor.extract_openapi_from_code(repo_path, feature)
    elapsed = time.time() - start

    profiler.disable()

    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)

    logger.info("=== Extraction Profile for %s ===", feature.key)
    logger.info("Total time: %.3fs", elapsed)
    logger.info(
        "Files processed: %d", len(feature.source_tracking.implementation_files) if feature.source_tracking else 0
    )
    logger.info("Paths extracted: %d", len(result.get("paths", {})))
    logger.info("Schemas extracted: %d", len(result.get("components", {}).get("schemas", {})))
    logger.info("Top 30 time consumers:")
    logger.info("%s", s.getvalue())


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if len(sys.argv) < 3:
        logger.error("Usage: profile_contract_extraction.py <repo_path> <feature_yaml>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    feature_yaml = Path(sys.argv[2])

    # Load feature from YAML
    with feature_yaml.open() as f:
        feature_data = yaml.safe_load(f)

    feature = Feature(
        key=feature_data["key"],
        title=feature_data["title"],
        stories=[],
        source_tracking=SourceTracking(**feature_data.get("source_tracking", {}))
        if feature_data.get("source_tracking")
        else None,
        contract=feature_data.get("contract"),
        protocol=feature_data.get("protocol"),
    )

    logger.info("Profiling extraction for %s", feature.key)
    profile_extraction(repo_path, feature)
