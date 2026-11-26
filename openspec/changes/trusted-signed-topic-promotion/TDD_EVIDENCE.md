# Signed topic provenance

The signed test-only checkpoint `b64ff8858bab31bfdb2166a7c3e51f26357ee9af`
fails the acceptance test locally with `TypeError` because `PromotionInputs`
has no `topic_commits` field. GitHub Actions run `45895179684` stops at the
expired `pycparser==2.22` trust record during bootstrap, before pytest, and
produces no before-fix artifact.

After implementation, local tests accept the exact signed, merge-ready
source and reject stale refs, unsigned commits, wrong trees, lookalike
topics, fork sources and extra parents. Local workflow tests exercise the
existing direct promotion path and check all three validation stages.

The review follow-up adds four regression cases that fail before the
producer workflow comparison and pass after it. The signed topic now
requires the source to retain the exact protected development workflow.
The final workflow re-reads the protected development ref immediately
before returning success for a topic.

The backport uses the already reviewed #799 dependency graph and scanner
implementation. The replacement before-fix checkpoint starts from the exact
protected main base and contains the unchanged mapped test selection. The
independent proof job runs that signed tests-only source with #799's
audited dependencies. A local replay failed the expected promotion test
and produced a native bound report. Hosted jobs consume the same-run
artifact and keep the existing passing-after and Code Review checks.
