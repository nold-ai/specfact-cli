# Dependency audit — 2026-09-21

## Result and limits

**Planning assessment only. No candidate package was installed, imported, or approved.** The primary graph has 52 package-name update candidates and two removed transitives. The complete inventory covers 187 distinct Python package names across primary and isolated Code Review graphs. The baseline primary lock has 183 external package records; the bounded candidate has 181. Multiple marker-specific versions are separate records.

All four repository vulnerability-gate runs passed: baseline primary, baseline Code Review, candidate primary, and candidate Code Review. OSV queries for all 241 distinct baseline/candidate package-version pairs returned no advisories and no unavailable responses. These results are dated negative advisory observations, not a guarantee against vulnerabilities or malware. The host-evaluated pip-audit gate is supplemented by explicit all-pair OSV queries so marker branches are not silently omitted.

**Promotion remains blocked** pending complete intervening-release review, exact-artifact Socket/upstream malware and provenance review, binary/platform artifact coverage, and compatibility tests. Existing Socket success on PR #744 is insufficient: its alert check explicitly says it was skipped because there were no detected dependency changes.

## Reproducible source snapshot

- Repository baseline: `5db1f213f1cd6dca283b86c6710379deb61bad94` on origin/dev.
- Dependency declarations and delivery versions are unchanged in this proposal. File SHA-256 identities, UTC assessment timestamp, candidate graph/export digests, source distribution identities, scope declarations, representative paths, and per-version results are in [dependency-inventory.json](dependency-inventory.json).
- Discovery: uv 0.11.28; the resolver selected CPython 3.13.14. Universal resolution covers the project's declared Python range; it is not evidence of executing Python 3.11–3.13 compatibility tests.
- Sources accessed on 2026-09-21: [PyPI JSON API](https://docs.pypi.org/api/json/), [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/), [uv resolution documentation](https://docs.astral.sh/uv/concepts/resolution/), and [RubyGems JSON versions](https://rubygems.org/api/v1/versions/json.json).
- Runtime requirements in setup.py were compared structurally with pyproject.toml and match. All four local module manifests have empty `pip_dependencies`; no extra local manifest dependency was omitted. External companion manifests remain a separately versioned integration surface.

### Discovery procedure

Copy pyproject.toml and uv.lock into a disposable directory, preserving the baseline identities. Query registry metadata for every declared/locked package and inspect exact pins separately. The repository's scheduled compatibility lane uses `uv lock --upgrade` and `uv lock --resolution lowest-direct`; only metadata discovery ran here.

An initial global `--no-build` attempt failed because commentjson 0.9.0 and lark-parser 0.7.8 have no wheels. Their existing source archives were downloaded as data, their SHA-256 values checked against the baseline lock, and setup.py inspected without execution. Static metadata was supplied in the disposable project: commentjson requires `lark-parser>=0.7.1,<0.8.0`; lark-parser has no runtime requirements. These source identities are retained in the JSON evidence. No such override enters tracked delivery inputs.

The broad metadata resolver used `--no-build-isolation`, prohibited builds for every baseline wheel package, and supplied those inspected source-only records. It resolved without a build or install. The policy-bounded rerun used the same static metadata, changed the disposable Hatchling pins to 1.32.4, and constrained `isort<9`, `readme-renderer<46`, and `pycparser==2.22`. A frozen all-extras requirements export was produced outside the repository.

The isolated assessment compiled Pylint 4.0.8 with Python 3.12 targeting, `--no-build`, generated hashes, and `isort<9`. This graph retains Astroid 4.0.4 and Isort 8.0.1, and advances Platformdirs 4.11.4 to 4.11.11. Generated requirements inputs/exports remain disposable analysis artifacts, not authoritative delivery locks.

Before implementation, repeat screening against the actual generated final graph and every selected artifact. A future resolver introducing different versions, sources, or transitives invalidates the relevant candidate review.

## Source PR dispositions and important candidates

| Item | Verified observation | Disposition |
|---|---|---|
| [PR #744](https://github.com/nold-ai/specfact-cli/pull/744), head `57c6a76e7eb174680970a9c08fdf03ab6643e411` | Both Hatchling declarations change from 1.32.0 to 1.32.3; primary lock/export and hard-coded regression expectation are omitted | Consolidate with candidate 1.32.4, subject to complete screening and build/plugin proof |
| Hatchling 1.32.4 | [Upstream release](https://github.com/pypa/hatch/releases/tag/hatchling-v1.32.4) fixes the plugin type-interface regression introduced by 1.32.3 and version whitespace handling; registry also records yanked intermediates | Prefer assessing 1.32.4 over stopping at the bot target; no security clearance implied |
| [PR #727](https://github.com/nold-ai/specfact-cli/pull/727), head `f4807f1ea6692296f5a71eef0f3d0d557d18d317` | JSON 2.21.2 to 3.0.2 also changes Jekyll 4.4.1 to 4.3.4 | Defer migration/downgrade; retain JSON 2.21.2, currently latest stable 2.x |
| Ruby JSON 2.21.2 | RubyGems version enumeration found no newer stable 2.x; OSV returned no advisory for the checked version | No Ruby change proposed; full Ruby graph audit/build remains required if implementation changes it |
| Pylint 4.0.7 to 4.0.8 | [Release notes](https://github.com/pylint-dev/pylint/releases/tag/v4.0.8) include diagnostic/crash fixes and permit Isort 9 | Candidate for isolated tooling; retain Isort 8 and verify report/runner compatibility |
| Cryptography 50.0.0 to 50.0.1; CFFI 2.1.0 to 2.1.1 | Resolve within supported constraints | Candidate; crypto/native artifact and supported-platform checks remain pending |
| GitPython 3.1.61 to 3.1.62; Typer 0.27.0 to 0.27.2 | Resolve within supported constraints | Candidate; Git and CLI behavior smoke tests remain pending |
| Semgrep 1.175.0 to 1.177.0 | Resolves with existing floor and frozen MCP pair | Candidate; independent scanner behavior, license and provenance checks remain pending |
| Isort 8.0.1 to 9.0.1; readme-renderer 45.0 to 46.0 | Broad resolver selects new major lines | Deferred migrations; bounded graph retains existing majors |
| pycparser 2.22 to 2.23 | Broad resolver selects 2.23; repository exception identifies an exact 2.22 wheel and expires 2026-10-22 | Retain 2.22 until substantive renewed artifact review; never select blocked 3.0 merely because PyPI lists it as latest |
| importlib-resources; uc-micro-py | Disappear from the updated primary graph | Removal candidates; verify affected import/runtime paths and platform markers |

## Security evidence

### Vulnerability checks actually run

Existing installed contributor tooling ran `scripts/security_audit_gate.py` for each baseline and disposable candidate export. The gate invokes pip-audit with `--strict --disable-pip`; no dependency installation or dynamic resolver fallback was used. Exact successful summaries are retained in the JSON evidence.

Explicit OSV API queries cover the union of baseline/candidate primary versions and baseline/candidate isolated versions: 241 package-version pairs. No advisory IDs or query errors were returned. GitHub's open Dependabot alert endpoint separately returned zero alerts; that observation covers the repository snapshot and cannot approve new candidate artifacts. There are therefore no affected/fixed CVE ranges to report from these successful queries. Any later positive result must include identifiers, affected/fixed ranges, upstream references, path, disposition, and expiry/mitigation where policy allows.

### Malicious-package and provenance status

[Socket PR #744 check 106213327240](https://github.com/nold-ai/specfact-cli/pull/744/checks) concluded success but titled the result **Pull Request #744 Alerts: Skipped**; the summary says no net dependency changes. The [project report](https://socket.dev/dashboard/org/noldai/sbom/84f4f082-33c1-44b1-9085-39c119a34c56) is linked to that source commit, not the new bounded candidate graph. Full per-artifact malware findings for the candidates were not obtained. Public Socket package-page lookup did not yield usable report contents.

All candidate records therefore retain `malware_review: unverified`. Registry metadata, successful CVE checks, matching hashes, or upstream release notes do not clear obfuscation, ownership compromise, executable payloads, or malicious transitives. Required follow-up is an exact-version/artifact Socket assessment plus relevant upstream/registry security notices and provenance inspection, with unresolved signals deferred before any candidate execution. Platform-specific wheels require their own identity/coverage; the source artifact in this planning inventory is not a substitute.

## Pending review and implementation gates

- Review all enumerated intervening releases against upstream notes; the inventory deliberately marks reviews pending except the explicitly described targeted checks above. Review yanked releases/reasons and newly introduced or removed transitives.
- Obtain exact-artifact malware/provenance and license evidence before candidate installation. Retain denied releases, reviewed floors, and version-bound exceptions; do not add blanket waivers.
- Run latest and lowest-direct tests on Python 3.11–3.13 in the environments actually synchronized by uv. Run frozen wheel/install/profile checks independently.
- Refresh authoritative locks/exports, synchronized declarations, build-backend regression expectations, and isolated input digests only during implementation; repeat audits on that exact result.
- Verify patch release/module compatibility and strict signatures, quality gates, and applicable docs/Ruby checks. Recheck security information before release if it changes.

## Complete package inventory

Every row is a planning disposition. `upgrade-candidate` and `isolated upgrade-candidate` require the pending security and compatibility gates; `retain` is not a new security approval. Latest versions outside the selected graph may be blocked by constraints, exact pins, Python support, or policy. Detailed declarations, dependency paths, marker versions, source identities, and intervening releases are in the JSON companion.

| Package | Baseline | Candidate | Latest stable | Disposition |
|---|---|---|---|---|
| `annotated-doc` | 0.0.4 | 0.0.5 | 0.0.5 | upgrade-candidate; security and compatibility approval pending |
| `annotated-types` | 0.8.0 | 0.8.0 | 0.8.0 | retain |
| `anyio` | 4.14.2 | 4.15.1 | 4.15.1 | upgrade-candidate; security and compatibility approval pending |
| `argcomplete` | 3.7.0 | 3.7.2 | 3.7.2 | upgrade-candidate; security and compatibility approval pending |
| `astroid` | isolated: 4.0.4 | isolated: 4.0.4 | 4.3.1 | retain isolated version; isolated Code Review graph requires separate compatible refresh |
| `asttokens` | 2.4.1 | 2.4.1 | 3.0.2 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `attrs` | 26.1.0 | 26.1.0 | 26.1.0 | retain |
| `azure-core` | 1.41.0 | 1.41.0 | 1.41.0 | retain |
| `azure-identity` | 1.25.3 | 1.25.3 | 1.25.3 | retain |
| `backports-tarfile` | 1.2.0 | 1.2.0 | 1.2.0 | retain |
| `bandit` | 1.9.4 | 1.9.4 | 1.9.4 | retain |
| `beartype` | 0.22.9 | 0.22.9 | 0.22.9 | retain |
| `boltons` | 21.0.0 | 21.0.0 | 26.2.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `boolean-py` | 5.0 | 5.0 | 5.0 | retain |
| `bracex` | 3.0.1 | 3.0.1 | 3.0.1 | retain |
| `build` | 1.5.0 | 1.6.1 | 1.6.1 | upgrade-candidate; security and compatibility approval pending |
| `cachecontrol` | 0.14.4 | 0.14.4 | 0.14.4 | retain |
| `cattrs` | 26.1.0 | 26.2.0 | 26.2.0 | upgrade-candidate; security and compatibility approval pending |
| `certifi` | 2026.7.22 | 2026.7.22 | 2026.7.22 | retain |
| `cffi` | 2.1.0 | 2.1.1 | 2.1.1 | upgrade-candidate; security and compatibility approval pending |
| `cfgv` | 3.5.0 | 3.5.0 | 3.5.0 | retain |
| `charset-normalizer` | 3.4.9 | 3.5.1 | 3.5.1 | upgrade-candidate; security and compatibility approval pending |
| `click` | 8.4.2 | 8.4.2 | 8.5.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `click-option-group` | 0.5.9 | 0.5.9 | 0.5.9 | retain |
| `colorama` | 0.4.6 | 0.4.6 | 0.4.6 | retain |
| `commentjson` | 0.9.0 | 0.9.0 | 0.9.0 | retain |
| `coverage` | 7.15.2 | 7.16.1 | 7.16.1 | upgrade-candidate; security and compatibility approval pending |
| `crosshair-tool` | 0.0.109 | 0.0.110 | 0.0.110 | upgrade-candidate; security and compatibility approval pending |
| `cryptography` | 50.0.0 | 50.0.1 | 50.0.1 | upgrade-candidate; security and compatibility approval pending |
| `cyclonedx-python-lib` | 11.11.0 | 11.12.0 | 11.12.0 | upgrade-candidate; security and compatibility approval pending |
| `defusedxml` | 0.7.1 | 0.7.1 | 0.7.1 | retain |
| `dill` | isolated: 0.4.1 | isolated: 0.4.1 | 0.4.1 | retain isolated version; isolated Code Review graph requires separate compatible refresh |
| `distlib` | 0.4.3 | 0.4.3 | 0.4.3 | retain |
| `docutils` | 0.23 | 0.23 | 0.23 | retain |
| `exceptiongroup` | 1.2.2 | 1.2.2 | 1.3.1 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `execnet` | 2.1.2 | 2.1.2 | 2.1.2 | retain |
| `face` | 26.0.1 | 26.0.1 | 26.0.1 | retain |
| `filelock` | 3.32.0 | 3.32.7 | 4.0.1 | upgrade-candidate; security and compatibility approval pending; newer release not selected; preserve resolver constraints or exact pin pending review |
| `gitdb` | 4.0.12 | 4.0.12 | 4.0.12 | retain |
| `gitpython` | 3.1.61 | 3.1.62 | 3.1.62 | upgrade-candidate; security and compatibility approval pending |
| `glom` | 25.12.0 | 25.12.0 | 25.12.0 | retain |
| `googleapis-common-protos` | 1.75.0 | 1.75.3 | 1.75.3 | upgrade-candidate; security and compatibility approval pending |
| `graphviz` | 0.21 | 0.21 | 0.21 | retain |
| `h11` | 0.16.0 | 0.16.0 | 0.16.0 | retain |
| `hatchling` | 1.32.0 | 1.32.4 | 1.32.4 | upgrade-candidate; security and compatibility approval pending |
| `httpcore` | 1.0.9 | 1.0.9 | 1.0.9 | retain |
| `httpx` | 0.28.1 | 0.28.1 | 0.28.1 | retain |
| `httpx-sse` | 0.4.3 | 0.4.3 | 0.4.3 | retain |
| `hypothesis` | 6.161.1 | 6.168.0 | 6.168.0 | upgrade-candidate; security and compatibility approval pending |
| `icontract` | 2.7.3 | 2.7.3 | 2.7.3 | retain |
| `id` | 1.6.1 | 1.6.1 | 1.6.1 | retain |
| `identify` | 2.6.19 | 2.6.19 | 2.6.19 | retain |
| `idna` | 3.18 | 3.20 | 3.20 | upgrade-candidate; security and compatibility approval pending |
| `importlib-metadata` | 8.7.1 | 8.7.1 | 9.0.1 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `importlib-resources` | 7.1.0 | removed | 7.1.0 | remove-candidate; verify obsolete transitive path |
| `iniconfig` | 2.3.0 | 2.3.0 | 2.3.0 | retain |
| `isort` | 8.0.1 | 8.0.1 | 9.0.1 | retain; defer unconstrained candidate 9.0.1; major migration or provenance review; isolated Code Review graph requires separate compatible refresh; newer release not selected; preserve resolver constraints or exact pin pending review |
| `jaraco-classes` | 3.4.0 | 3.4.0 | 3.4.0 | retain |
| `jaraco-context` | 6.1.2 | 6.1.2 | 6.1.2 | retain |
| `jaraco-functools` | 4.6.0 | 4.6.0 | 4.6.0 | retain |
| `jeepney` | 0.9.0 | 0.9.0 | 0.9.0 | retain |
| `jinja2` | 3.1.6 | 3.1.6 | 3.1.6 | retain |
| `jsonschema` | 4.25.1 | 4.25.1 | 4.26.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `jsonschema-specifications` | 2025.9.1 | 2025.9.1 | 2025.9.1 | retain |
| `keyring` | 25.7.0 | 25.7.0 | 25.7.0 | retain |
| `lark-parser` | 0.7.8 | 0.7.8 | 0.12.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `libcst` | 1.8.6 | 1.9.0 | 1.9.0 | upgrade-candidate; security and compatibility approval pending |
| `license-expression` | 30.4.4 | 30.4.4 | 30.4.4 | retain |
| `linkify-it-py` | 2.1.0 | 2.2.0 | 2.2.0 | upgrade-candidate; security and compatibility approval pending |
| `lsprotocol` | 2025.0.0 | 2025.0.0 | 2025.0.0 | retain |
| `mando` | 0.7.1 | 0.7.1 | 0.8.2 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `markdown-it-py` | 4.2.0 | 4.2.0 | 4.2.0 | retain |
| `markupsafe` | 3.0.3 | 3.0.3 | 3.0.3 | retain |
| `mccabe` | isolated: 0.7.0 | isolated: 0.7.0 | 0.7.0 | retain isolated version; isolated Code Review graph requires separate compatible refresh |
| `mcp` | 1.29.0 | 1.29.0 | 2.2.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `mdit-py-plugins` | 0.6.1 | 0.6.1 | 0.6.1 | retain |
| `mdurl` | 0.1.2 | 0.1.2 | 0.1.2 | retain |
| `more-itertools` | 11.1.0 | 11.1.0 | 11.1.0 | retain |
| `msal` | 1.37.0 | 1.39.0 | 1.39.0 | upgrade-candidate; security and compatibility approval pending |
| `msal-extensions` | 1.3.1 | 1.3.1 | 1.3.1 | retain |
| `msgpack` | 1.2.1 | 1.2.2 | 1.2.2 | upgrade-candidate; security and compatibility approval pending |
| `mutmut` | 3.6.0 | 3.8.0 | 3.8.0 | upgrade-candidate; security and compatibility approval pending |
| `mypy-extensions` | 1.1.0 | 1.1.0 | 1.1.0 | retain |
| `networkx` | 3.6.1 | 3.6.1 | 3.6.1 | retain |
| `nh3` | 0.3.6 | 0.3.7 | 0.3.7 | upgrade-candidate; security and compatibility approval pending |
| `nodeenv` | 1.10.0 | 1.10.0 | 1.10.0 | retain |
| `opentelemetry-api` | 1.37.0 | 1.37.0 | 1.44.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `opentelemetry-exporter-otlp-proto-common` | 1.37.0 | 1.37.0 | 1.44.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `opentelemetry-exporter-otlp-proto-http` | 1.37.0 | 1.37.0 | 1.44.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `opentelemetry-instrumentation` | 0.58b0 | 0.58b0 | No stable release | retain |
| `opentelemetry-instrumentation-requests` | 0.58b0 | 0.58b0 | No stable release | retain |
| `opentelemetry-instrumentation-threading` | 0.58b0 | 0.58b0 | No stable release | retain |
| `opentelemetry-proto` | 1.37.0 | 1.37.0 | 1.44.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `opentelemetry-sdk` | 1.37.0 | 1.37.0 | 1.44.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `opentelemetry-semantic-conventions` | 0.58b0 | 0.58b0 | No stable release | retain |
| `opentelemetry-util-http` | 0.58b0 | 0.58b0 | No stable release | retain |
| `packageurl-python` | 0.17.6 | 0.17.6 | 0.17.6 | retain |
| `packaging` | 26.2 | 26.3 | 26.3 | upgrade-candidate; security and compatibility approval pending |
| `pathspec` | 1.1.1 | 1.1.1 | 1.1.1 | retain |
| `peewee` | 3.19.0 | 3.19.0 | 4.5.1 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `pip` | 26.2.1 | 26.2.1 | 26.2.1 | retain |
| `pip-api` | 0.0.34 | 0.0.35 | 0.0.35 | upgrade-candidate; security and compatibility approval pending |
| `pip-audit` | 2.10.1 | 2.10.1 | 2.10.1 | retain |
| `pip-licenses` | 5.5.5 | 5.5.5 | 5.5.5 | retain |
| `pip-requirements-parser` | 32.0.1 | 32.0.1 | 32.0.1 | retain |
| `pip-tools` | 7.6.1 | 7.6.1 | 7.6.1 | retain |
| `pipx` | 1.16.2 | 1.17.5 | 1.17.5 | upgrade-candidate; security and compatibility approval pending |
| `platformdirs` | 4.11.0 | 4.11.11 | 4.11.11 | upgrade-candidate; security and compatibility approval pending; isolated Code Review graph requires separate compatible refresh |
| `pluggy` | 1.6.0 | 1.6.0 | 1.6.0 | retain |
| `pre-commit` | 4.6.1 | 4.6.2 | 4.6.2 | upgrade-candidate; security and compatibility approval pending |
| `prettytable` | 3.18.0 | 3.18.0 | 3.18.0 | retain |
| `prompt-toolkit` | 3.0.52 | 3.0.53 | 3.0.53 | upgrade-candidate; security and compatibility approval pending |
| `protobuf` | 6.33.6 | 6.33.6 | 7.36.2 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `py-serializable` | 2.1.0 | 2.1.0 | 2.1.0 | retain |
| `pycg` | 0.0.8 | 0.0.8 | 0.0.8 | retain |
| `pycparser` | 2.22 | 2.22 | 3.0 | retain; defer unconstrained candidate 2.23; major migration or provenance review; newer release not selected; preserve resolver constraints or exact pin pending review |
| `pydantic` | 2.13.4 | 2.13.5 | 2.13.5 | upgrade-candidate; security and compatibility approval pending |
| `pydantic-core` | 2.46.4 | 2.46.5 | 2.49.0 | upgrade-candidate; security and compatibility approval pending; newer release not selected; preserve resolver constraints or exact pin pending review |
| `pydantic-settings` | 2.14.2 | 2.15.0 | 2.15.0 | upgrade-candidate; security and compatibility approval pending |
| `pygls` | 2.1.1 | 2.1.1 | 2.1.1 | retain |
| `pygments` | 2.20.0 | 2.21.0 | 2.21.0 | upgrade-candidate; security and compatibility approval pending |
| `pyjwt` | 2.13.0 | 2.13.0 | 2.14.0 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `pylint` | isolated: 4.0.7 | isolated: 4.0.8 | 4.0.8 | isolated upgrade-candidate; isolated Code Review graph requires separate compatible refresh |
| `pyparsing` | 3.3.2 | 3.3.3 | 3.3.3 | upgrade-candidate; security and compatibility approval pending |
| `pyproject-hooks` | 1.2.0 | 1.3.3 | 1.3.3 | upgrade-candidate; security and compatibility approval pending |
| `pytest` | 9.1.1 | 9.1.1 | 9.1.1 | retain |
| `pytest-asyncio` | 1.4.0 | 1.4.0 | 1.4.0 | retain |
| `pytest-cov` | 7.1.0 | 7.1.0 | 7.1.0 | retain |
| `pytest-mock` | 3.15.1 | 3.15.1 | 3.15.1 | retain |
| `pytest-timeout` | 2.4.0 | 2.4.0 | 2.4.0 | retain |
| `pytest-xdist` | 3.8.0 | 3.8.0 | 3.8.0 | retain |
| `python-discovery` | 1.5.0 | 1.6.1 | 1.6.1 | upgrade-candidate; security and compatibility approval pending |
| `python-dotenv` | 1.2.2 | 1.2.3 | 1.2.3 | upgrade-candidate; security and compatibility approval pending |
| `python-multipart` | 0.0.32 | 0.0.32 | 0.0.32 | retain |
| `pywin32` | 311 | 311 | 312 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `pywin32-ctypes` | 0.2.3 | 0.2.3 | 0.2.3 | retain |
| `pyyaml` | 6.0.3 | 6.0.3 | 6.0.3 | retain |
| `pyyaml-ft` | 8.0.0 | 8.0.0 | 8.0.0 | retain |
| `questionary` | 2.1.1 | 2.1.1 | 2.1.1 | retain |
| `radon` | 6.0.1 | 6.0.1 | 6.0.1 | retain |
| `readme-renderer` | 45.0 | 45.0 | 46.0 | retain; defer unconstrained candidate 46.0; major migration or provenance review; newer release not selected; preserve resolver constraints or exact pin pending review |
| `referencing` | 0.37.0 | 0.37.0 | 0.37.0 | retain |
| `requests` | 2.34.2 | 2.34.2 | 2.34.2 | retain |
| `requests-toolbelt` | 1.0.0 | 1.0.0 | 1.0.0 | retain |
| `rfc3986` | 2.0.0 | 2.0.0 | 2.0.0 | retain |
| `rich` | 15.0.0 | 15.0.0 | 15.0.0 | retain |
| `rpds-py` | 2026.6.3 | 2026.6.3 | 2026.6.3 | retain |
| `ruamel-yaml` | 0.19.1 | 0.19.1 | 0.19.1 | retain |
| `ruamel-yaml-clib` | 0.2.15 | 0.2.15 | 0.2.15 | retain |
| `ruff` | 0.16.0 | 0.16.8 | 0.16.8 | upgrade-candidate; security and compatibility approval pending |
| `secretstorage` | 3.5.0 | 3.5.0 | 3.5.0 | retain |
| `semantic-version` | 2.10.0 | 2.10.0 | 2.10.0 | retain |
| `semgrep` | 1.175.0 | 1.177.0 | 1.177.0 | upgrade-candidate; security and compatibility approval pending |
| `setproctitle` | 1.3.7 | 1.3.7 | 1.3.7 | retain |
| `setuptools` | 84.0.0 | 84.0.0 | 84.0.0 | retain |
| `shellingham` | 1.5.4 | 1.5.4 | 1.5.4 | retain |
| `six` | 1.17.0 | 1.17.0 | 1.17.0 | retain |
| `smmap` | 5.0.3 | 5.0.3 | 5.0.3 | retain |
| `sortedcontainers` | 2.4.0 | 2.4.0 | 2.4.0 | retain |
| `sse-starlette` | 3.4.6 | 3.4.11 | 3.4.11 | upgrade-candidate; security and compatibility approval pending |
| `starlette` | 1.3.1 | 1.6.0 | 1.6.0 | upgrade-candidate; security and compatibility approval pending |
| `stevedore` | 5.9.0 | 5.9.1 | 5.9.1 | upgrade-candidate; security and compatibility approval pending |
| `textual` | 8.2.8 | 8.2.8 | 8.2.8 | retain |
| `tomli` | 2.4.1 | 2.4.1 | 2.4.1 | retain |
| `tomli-w` | 1.2.0 | 1.2.0 | 1.2.0 | retain |
| `tomlkit` | 0.15.1 | 0.15.1 | 0.15.1 | retain; isolated Code Review graph requires separate compatible refresh |
| `trove-classifiers` | 2026.6.1.19 | 2026.6.1.19 | 2026.6.1.19 | retain |
| `twine` | 7.0.0 | 7.0.0 | 7.0.0 | retain |
| `typer` | 0.27.0 | 0.27.2 | 0.27.2 | upgrade-candidate; security and compatibility approval pending |
| `types-pyyaml` | 6.0.12.20260518 | 6.0.12.20260906 | 6.0.12.20260906 | upgrade-candidate; security and compatibility approval pending |
| `typeshed-client` | 2.12.0 | 2.13.0 | 2.13.0 | upgrade-candidate; security and compatibility approval pending |
| `typing-extensions` | 4.16.0 | 4.16.0 | 4.16.0 | retain |
| `typing-inspect` | 0.9.0 | 0.9.0 | 0.9.0 | retain |
| `typing-inspection` | 0.4.2 | 0.4.4 | 0.4.4 | upgrade-candidate; security and compatibility approval pending |
| `uc-micro-py` | 2.0.0 | removed | 2.0.0 | remove-candidate; verify obsolete transitive path |
| `urllib3` | 2.7.0 | 2.8.0 | 2.8.0 | upgrade-candidate; security and compatibility approval pending |
| `userpath` | 1.9.2 | 1.9.2 | 1.9.2 | retain |
| `uvicorn` | 0.51.0 | 0.53.0 | 0.53.0 | upgrade-candidate; security and compatibility approval pending |
| `virtualenv` | 21.7.0 | 21.9.0 | 21.9.0 | upgrade-candidate; security and compatibility approval pending |
| `watchdog` | 6.0.0 | 6.0.0 | 6.0.0 | retain |
| `wcmatch` | 8.5.2 | 8.5.2 | 11.0.1 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `wcwidth` | 0.8.2 | 0.8.4 | 0.8.4 | upgrade-candidate; security and compatibility approval pending |
| `wheel` | 0.47.0 | 0.48.0 | 0.48.0 | upgrade-candidate; security and compatibility approval pending |
| `wrapt` | 1.17.3 | 1.17.3 | 2.4.1 | retain; newer release not selected; preserve resolver constraints or exact pin pending review |
| `yamllint` | 1.38.0 | 1.38.0 | 1.38.0 | retain |
| `z3-solver` | 5.0.0.0 | 5.1.0.0 | 5.1.0.0 | upgrade-candidate; security and compatibility approval pending |
| `zipp` | 4.1.0 | 4.1.0 | 4.1.0 | retain |
