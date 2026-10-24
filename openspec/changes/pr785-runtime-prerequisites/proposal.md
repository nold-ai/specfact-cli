# Observe PR785 Actions prerequisites

## Why

The recovery reader depends on current in-progress job logs and a complete
future-step list. Neither prerequisite has been established by an active-job
observation. A completed job, local fixture, redirect, or uploaded artifact cannot
establish those facts.

The existing `specfact.yml` at main commit
`5262efb0881e4fac7697d629b0530250342bc656` runs normal validation on pull requests,
pushes, and manual events. It grants PR and check writes and installs validation
dependencies. A disposable read-only observation needs a separate auxiliary
branch workflow contract.

## What Changes

- Specify a manual-only four-step diagnostic at the existing `specfact.yml`
  identity on `codex/pr785-runtime-prerequisites`.
- Require job-scoped contents/actions read, immutable action pins, isolated
  platform Python, and a five-minute job bound.
- Retain one attempt-specific jobs response and at most one selected current-job
  logs response, without redirects, proxies, retries, token output, or authority.
- Add two workflow contract tests and an honest requirements mapping before
  observer or workflow implementation.

## Capabilities

### New capabilities

- `pr785-runtime-prerequisites`: bounded prerequisite observations with explicit
  limits on what their results establish.

### Modified capabilities

None. Native required-check behavior remains owned by its existing changes.
The auxiliary workflow is confined to this diagnostic branch.

## Impact

This change serves recovery maintainers. It adds no application command, public
API, package dependency, signed asset, or release behavior. Bridge adapters,
plugin registration, sidecar validation, and multi-repository contracts are
unaffected. The diagnostic deliberately uses GitHub Actions and has no offline
substitute for the service observation. Local workflow checks remain offline.

Affected documentation is this change's maintainer specification and design.
`docs/`, `README.md`, `docs/index.md`, and sidebar navigation describe the product
and need no user-facing change for this isolated diagnostic.

Hosted cost is bounded to one job with a five-minute timeout if separately
dispatched. Actual duration and response sizes remain unmeasured. Rollback is
abandoning the isolated branch or an ordinary reviewed revert. No merge,
publication, protected deployment, signing, access expansion, waiver, or advisory
exception is part of this scope.

## Source tracking

This is a diagnostic unit within the existing owner-authorized recovery of
[PR #785](https://github.com/nold-ai/specfact-cli/pull/785), not a new issue-linked
product change. No issue state or hierarchy claim is made here. No issue or wiki
write is authorized for this unit.

The matching internal wiki source is absent. Follow-up before any wider delivery
is to create or align `wiki/sources/pr785-runtime-prerequisites.md`, including
depends-on, blocks, external-deps, status, and summary, then run
`python3 scripts/wiki_rebuild_graph.py` from the internal repository root under
the coordinator's applicable authority.

## Addendum on 24 October 2026, Europe/Berlin

The paragraphs above describe the original diagnostic unit. The newly agreed
test-first scope adds logs-only explicit storage continuation and a flushed
runtime marker. Automatic redirects and ambient proxies remain disabled. One
jobs API request and one logs API request may be followed by at most three
validated HTTPS storage requests without the GitHub bearer. Each received
response keeps its own bytes and metadata. The initial API 302 is never replaced
by the terminal response.

New offline command tests cover retained responses, credential separation,
destination rejection, bounded failures, exact marker matching, and unchanged
raw step metadata. The existing two workflow tests and four mapping cases remain
unchanged. A complete local test result cannot establish current hosted log
availability. The workflow bytes, permission scope, authority boundary, and
closed delivery actions remain unchanged. This addendum records proposed
behavior before baseline execution or implementation. The existing internal
wiki follow-up remains open under coordinator authority.

## Short-body completeness amendment on 24 October 2026, Europe/Berlin

A bounded response read can return fewer bytes than the advertised
`Content-Length` without raising an exception. The observer must refuse that
incomplete payload for direct API and storage responses, including HTTP errors.
An exact marker inside the partial bytes cannot establish a complete response.

One additive regression covers direct and storage HTTP 200 and 404 responses.
The existing twelve transport tests and two workflow tests remain positive and
negative controls. The new case requires exit 1, `body-read-failed`, actual
status and local completion time, preserved earlier responses, and no incomplete
raw file or terminal summary. This amendment precedes the new failing baseline
and source correction. It grants no hosted proof or authority. The existing
internal wiki follow-up remains open under coordinator authority.
