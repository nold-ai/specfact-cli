# Retained proof promotion review

The protected Requirements consumer for core PR #771 at `f7b761bb`
reproduced four blocking findings on 25 November 2026. The report contained
one complexity finding in the upload receipt verifier, one nesting finding
in the mutation test, and two direct execution findings in the inline
workflow test.

[Protected Code Review artifact](https://github.com/nold-ai/specfact-cli/actions/runs/45563784409/artifacts/14998694413)

The updated parity test failed against the original script and workflow
because the paired validation helpers were absent. With the repair it passed
alongside 66 other retained-proof and promotion-security tests. The same
Semgrep rule reported two findings before and zero after. Ruff, BasedPyright,
and actionlint passed. The focused reviewer reported zero errors and zero
warnings.

A local full review of 119 Python files against main, using the main
SpecFact CLI 0.55.4 source and the pinned modules fixture, reported zero
blocking findings. The full review still failed because its cumulative score
was 0, below its existing pass floor of 50. Verification context from the
hosted promotion was not attached to the local review.

The follow-up candidate also addresses verified warning findings in the
documentation tests, signature verification, module installation, CLI help,
and runtime test setup. It passes the same full protected-main reviewer locally
at 53 points against its pass floor of 50, with zero blocking findings.
Hosted Requirements and release review still require a protected rollout.

GitHub Actions run `45895033041` recorded the expected parity failure
on the signed test-only checkpoint. Run `45895418236` accepted that
artifact and passed Requirements on the signed implementation.

A separate regression test executes the checked-in inline upload receipt
validator with fixture data. It accepts the recorded upload and rejects
changes to the job attempt, receipt, archive, and retained member.
