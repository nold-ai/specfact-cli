# Planned local report consumption

## Existing paths and ownership

Inspected on 2026-10-16: `scripts/pre_commit_code_review.py` shells out to the CLI, writes `.specfact/code-review.json`, and defines a minimal `CodeReviewReport`. `src/specfact_cli/registry/module_installer.py` installs verified modules and invokes `install_resolved_pip_requirements`. `src/specfact_cli/registry/module_discovery.py` and `module_packages.py` own discovery and compatibility. These are implementation touchpoints to verify again before changing behavior, not evidence of schema 2.0 support.

Reuse ordinary invocation and existing module verification first. Adapt their narrow report and installation boundaries. Custom runtime or registry infrastructure is unnecessary for this approved outcome. Modules own project runtime and standards resolution, analyzer execution, and serialized reports. Core owns ordinary hooks, workflow invocation, installation compatibility, loading, and discovery.

## Report boundary

Use a small validated, version-discriminated report input at existing consumers. Schema 2.0 dispatch selects the modules #515 contract. Historical 1.6 dispatch is restricted to consumers with supported 1.6 semantics. Reject unknown major versions and malformed required fields before summarizing success. Any current or future helper using a numeric `>=1.6` test must not classify 2.0 as 1.6.

Read the producer's authoritative assurance status and completeness, preserving failure and uncertainty in the summary and machine output. Score, fixability, and missing findings cannot replace assurance. Shadow mode changes blocking policy only. It retains adverse evidence and does not print a successful assurance claim for an incomplete report. Reconcile process exit and report according to the released producer contract; contradictory evidence cannot become success.

No consumer promotes local evidence to protected `pr_range` or capsule attestation. The protected #680 contract remains separate. Preserve C15 #679 and modules #417 ownership and acceptance rather than folding those contracts into local schema 2.0.

## Installation boundary

The customer CLI may run in pipx, uv tool, or uvx while project Python differs. Preserve this separation. Do not inject analyzer or module dependencies into the customer project environment. A uvx tool environment may have no pip. Use supported external tooling or declared tool dependencies for the installed CLI environment instead of unmanaged mutation or an assumption that `python -m pip` exists. Verify the actual installer path against each supported installation before claiming compatibility.

`--project-runtime` denotes a descriptor contract. Do not reinterpret it as an interpreter path. Modules resolve project execution using their descriptor and project discovery contracts. Core forwards only supported declared inputs.

## Rollout and risks

First prove one real installed local review workflow. Then cover pipx, uv tool, and uvx with exact signed module/core identities and project interpreters recorded in acceptance evidence. Apply schema dispatch before replacing ordinary invocation. Retain security and signature gates, including independent modules #511 and core #719/#718 work.

Schema confusion can falsely report success. Mitigate with unsupported-major and contradictory-report cases. Installation drift can hide dependency mistakes. Mitigate with clean external environments, including uvx without pip. Trusted project tools can execute repository code. Document that trust boundary and keep protected credentials and attestation claims outside this workflow.

Rollback pins the previous immutable compatible released CLI/module pair and retains actual adverse results. Do not reduce acceptance requirements to hide an incompatible consumer or resurrect a second capsule backend in the replacement. Optional downstream consumers remain future work.

## Planning and later implementation

All acceptance remains planned. Follow spec, tests, observed failing evidence, production code, then passing evidence during implementation. The internal wiki source and C14/C15 compatibility notes were aligned through the owning checkout on 2026-10-16, and the native graph was rebuilt. Its strict health check reports 59 pre-existing errors, down from 62, with no new errors. Unrelated source pages were preserved. This records planning alignment only; all implementation tasks remain unchecked.
