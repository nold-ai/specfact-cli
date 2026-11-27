# Retire the SpecFact core Semgrep integration

## Why

Semgrep's dependency graph has repeatedly blocked enterprise installation or required temporary exceptions. Core #796 isolates that graph as an immediate recovery measure. The permanent change removes it from SpecFact-owned core distribution, tooling, and CI while preserving the scanner use cases and independent security outcomes.

## What changes

- Replace Semgrep-backed feature detection, code-quality analysis and async scanning where the owning code is still shipped by core. Verify owners and all checked-in rules, their languages, CLI/JSON consumers, and built artifacts first.
- Preserve blocking independent static-analysis coverage and finding continuity with the standalone Python AST scanner and the existing Bandit check. The active brownfield path discovers Python sources. Its unused JavaScript, TypeScript, and Go patterns require separate consumer evidence before integration.
- Remove Semgrep from packaging, development environments, scripts, rule resources, and the frozen graph. Keep the existing extra name for install compatibility. Upgrade retained telemetry and retire the obsolete advisory exceptions.
- Bind frozen dependency delivery to the exact Socket-reviewed PyPI wheel for pycparser 3.12. The published package keeps its registry dependency range.
- Coordinate the exact Semgrep-free pair with the trusted-local modules reset. Core #769 owns ordinary local report consumption. Core #780 remains the historical/temporary dependency fix and #796 retains its separate exact-head checks.

## Dependencies and relationships

Parent Feature #375 under Epic #285. Related dependency maintenance #747, temporary recovery #780 and #796, and module rollout nold-ai/specfact-cli-modules#514, #515, #516 and #523. Core-owned rule inventory and replacement tests can run independently. Joint installed acceptance depends on both repositories' compatible candidates.

## Impact

The change affects core analyst inputs and outputs, independent CI, packaging, docs and frozen delivery graphs. Preserve Bandit, independent security audit, provenance, signatures, protected C14 and C15 contracts, and normal release authority. This change covers the core candidate. Hosted checks and the compatible signed module installation remain release acceptance gates.

## Source tracking

<!-- source_repo: nold-ai/specfact-cli -->
- GitHub Issue: #797
- Issue URL: <https://github.com/nold-ai/specfact-cli/issues/797>
- Parent: #375
