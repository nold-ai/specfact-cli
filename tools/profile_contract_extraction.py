#!/usr/bin/env python3
"""
Profile contract extraction to identify bottlenecks.

This script helps diagnose performance issues in contract extraction.
"""

import cProfile
import pstats
import time
from io import StringIO
from pathlib import Path

import yaml

from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


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

    print(f"\n=== Extraction Profile for {feature.key} ===")
    print(f"Total time: {elapsed:.3f}s")
    print(f"Files processed: {len(feature.source_tracking.implementation_files) if feature.source_tracking else 0}")
    print(f"Paths extracted: {len(result.get('paths', {}))}")
    print(f"Schemas extracted: {len(result.get('components', {}).get('schemas', {}))}")
    print("\nTop 30 time consumers:")
    print(s.getvalue())


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: profile_contract_extraction.py <repo_path> <feature_yaml>")
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

    print(f"Profiling extraction for {feature.key}")
    profile_extraction(repo_path, feature)
