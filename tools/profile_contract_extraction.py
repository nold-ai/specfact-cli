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

from specfact_cli.generators.openapi_extractor import OpenAPIExtractor
from specfact_cli.models.plan import Feature


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
    ps.print_stats(20)

    print(f"\n=== Extraction Profile for {feature.key} ===")
    print(f"Total time: {elapsed:.3f}s")
    print(f"Paths extracted: {len(result.get('paths', {}))}")
    print("\nTop 20 time consumers:")
    print(s.getvalue())


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: profile_contract_extraction.py <repo_path> <feature_yaml>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    feature_yaml = Path(sys.argv[2])

    # Load feature (simplified - you'd use actual loader)
    print(f"Profiling extraction for feature in {feature_yaml}")
    print("Note: This is a diagnostic tool - implement feature loading as needed")
