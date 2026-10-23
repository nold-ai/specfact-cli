# Independent runtime acceptance

ACCEPT for the frozen local runtime correction only. No blockers found in the reviewed delta. Confidence is high because the independent checker verifies the final bytes and conservation, and the one permitted focused run passes all 93 cases. Reviewed on 23 October 2026, Europe/Berlin, by `/root/probe_diagnostic_runtime_acceptance`. The writer was stopped before review.

The only changed indexed file is `scripts/pr785_signing_recovery.py`. Its `main` catches the existing policy exception separately, writes its safe reason to stderr, and retains refused status. The `OSError` handler writes exactly `Probe refused: Local I/O failure\n` without inspecting the exception. Receipt fields, persistence, signatures, context, identity, refs, HTTP transport and allowed routes are conserved. No fallback or new API behavior appears in the diff.

I inspected every program-authored `ProbeRefusalError` producer. All 44 `_check` call reasons are constant strings. The direct raises are constants, the `_check` reason passthrough, or the existing status-only `API refused HTTP {error.code}`. The actual Python 3.12.13 transport parses that status as an integer from 100 through 999 before constructing `HTTPError`. Its reason, headers and body are excluded. Chained JSON and transport exceptions remain attached internally, but this handler prints only `str(error)` and never formats a chain or traceback. The producer inventory and installed stdlib source are retained privately.

The independent suite exits 0 with 93 passes and zero failures, errors or skips. Its 93 case identities equal both recorded RED and GREEN in order. The frozen RED has three intended stderr assertion failures and 90 passes. The new controls reject HTTP body and credential markers, HTTP reason text, tracebacks and arbitrary local exception text while checking truthful receipts and retained responses. The exact generic local message passes.

The checker verifies all 36 implementation evidence hashes. Restoring only the original `main` handler list makes the complete AST identical to HEAD. The other 2,444 indexed files and the index are unchanged. The accepted test and mapping bytes remain frozen. The mapping binding is preserved against the accepted native report, which I did not rerun. `git diff --check` passes.

I inspected final quality commands and results bound to the reviewed runtime digest. Scoped lint and types, actual SpecFact CodeReview, configured six-rule Semgrep, Bandit, selected YAML and strict OpenSpec all exit 0. Final CodeReview has zero findings. Earlier print warnings are intermediate evidence only. The bundled-module refresh notice and inherited 1,449 type warnings and 30 YAML errors remain unresolved.

The saved run 39923021078 remains refused with one baseline and both anchor flags false. Its exact external tree-request refusal remains UNKNOWN. Synthetic HTTP 403 does not diagnose it. This review accepts no complete live probe, anchors, native 33-case release RED, or release readiness.

Changed frozen bytes, a future unsanitized policy producer, or adoption of partial live evidence would invalidate the relevant conclusion. Hash checks, producer review, and root authentication of a fresh complete probe constrain those risks. No cost estimate follows. Root owns rollback of the unstaged delta, normal hooks and commit, separate comment acceptance and any new live probe. Prove It Works changed this review from trusting the handoff to checking actual bytes and executing the focused suite. No source, tests, spec, receipt, index, refs or external state were changed by this reviewer. No network, broad suite, scan, installation, signing, dispatch, comments, merge or subagent occurred.

Exact accepted identities and evidence follow.

| Input | Value |
| --- | --- |
| HEAD | `26764ce44b305d4edb1810769341fcd38c0b3c57` |
| Runtime SHA-256 | `77c290d1a7326f89df49980ef217f66f99d84fd84cb1146331d55945b42f24f7` |
| Test SHA-256 | `879533ee4ff8762f1575313d99bc3267ea20eea15b1a4cd82e676f68a5c1b4af` |
| Mapping digest | `sha256:8998713988ae1df90f45940f48527a12e6196a5b0ace58e8d3f55f8fbc9fc4e4` |
| Index SHA-256 | `f0d2730c6748104f8d35992437bb558e248ae4168f6d2d7627af5f124235857e` |

The reproducible checker is [independent-runtime-check.py](independent-runtime-check.py). Exact argv, exits, inventories and conservation are in [independent-runtime-check.json](independent-runtime-check.json). The runtime run is in [independent-runtime-green.log](independent-runtime-green.log) and [independent-runtime-green.xml](independent-runtime-green.xml). The HTTP status path is in [independent-runtime-transport-source.txt](independent-runtime-transport-source.txt).
