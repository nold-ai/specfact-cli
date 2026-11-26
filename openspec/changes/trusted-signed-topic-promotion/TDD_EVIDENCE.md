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
