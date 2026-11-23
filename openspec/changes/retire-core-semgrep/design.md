# Core scanner ownership and replacement

The user selected the trusted-local module reset as the first landing point on 21 November 2026 (Europe/Berlin). This work removes the active core dependency while keeping the independent CI control and tested consumer behavior.

| Surface | Owner and candidate |
| --- | --- |
| Feature/quality analysis | Keep the existing core analyzer entry points where still supported. Extend existing Python AST analysis or reuse Ruff where parser behavior, extraction, paths and normalized output match. Coordinate overlapping module-owned paths through modules #523. |
| Repository SAST and async rules | Keep the independent job as the owner of security policy, baseline and status. Map all effective rule IDs and scopes to Ruff/Bandit or reviewed structural rules. Use the existing baseline gate with a versioned migration when identities or fingerprint semantics change. |
| Go/JavaScript/TypeScript patterns | Inventory effective patterns and callers separately. A pinned ast-grep distribution is a candidate if it proves platform, provenance, exact input and unsuppressed coverage. Select tooling after executable evidence. |
| Delivered artifacts | Existing packaging and CI own declarations, locks, extras, commands and audit evidence. No runtime scanner discovery/download path exists for the retired integration. |

Keep configuration authority, normalized finding identity and execution completion distinct. Each scanner receives explicit source inputs and policy. Incomplete or invalid output remains nonaccepting for required CI controls. Baselines bind rule semantics and compatible identities. Review any behavior differences with positive and negative fixtures. Keep scanner-independent requirements, trust and release gates in force.

## Runtime paths to migrate

| Current owner | Inputs and output to preserve |
| --- | --- |
| `src/specfact_cli/analyzers/code_analyzer.py` and the Project module counterpart | The feature pack has 39 rules across Python, Go, JavaScript, and TypeScript. The quality pack has 16 Python rules. The analyzer uses findings in feature evidence, categorization, and confidence. |
| `src/specfact_cli/validators/repro_checker.py` and the Codebase module counterpart | The async pack has 13 Python rules. The repro checker parses findings and can apply fixes. Verify both the report and resulting source when fixes are requested. |
| `src/specfact_cli/generators/test_to_openapi.py` and the Project module counterpart | The Python test-pattern pack has six rules. Findings contribute examples to the generated OpenAPI document. |
| `src/specfact_cli/generators/workflow_generator.py` and `src/specfact_cli/importers/speckit_converter.py` | These write Semgrep rule files. Trace generated configuration and callers as part of the consumer cutover. |
| Independent Static Analysis workflow | The local candidate replaces the six Python SAST rules and keeps Bandit. The frozen setup removes the Semgrep graph and retains the independent Bandit tool. |

The previous wheel bundled feature, quality, and async packs under `src/specfact_cli/resources/semgrep/`. The candidate removes those shipped copies and the development packs. Brownfield discovery parses only Python. The JavaScript, TypeScript, and Go declarations had no active caller in that analyzer.

The async migration reports rule IDs and source locations. It narrows timeout detection to asyncio waits and missing-await findings to known local coroutine calls. Custom policies require migration. Replacing a blocking call depends on its surrounding control flow and imports, so an explicit fix request reports the manual migration and preserves the source.

First milestone is an isolated independent static-analysis fixture on the current core baseline. Seed existing SAST findings and safe controls, prove full input coverage and the block for an introduced finding, and induce a missing-tool or skipped-input failure. Record genuine RED before implementation and compare the replacement under the normal CI entry point before migrating the full baseline. Measure the complete shipped graph, build tools and CI paths before claiming removal. Compare the graph's actual origin and advisory evidence rather than package name alone.

Rollback withholds the candidate or restores a prior compatible signed pair where organizational policy permits. Historical rules, immutable evidence and release snapshots retain their original meaning.
