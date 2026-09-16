# Documentation fixture behavioral proof

The test reads `ci/docs-module-fixture.lock.json`, validates the fixed public repository and immutable commit/tree,
and authenticates every bundle with the unchanged core verifier and publisher public key. A matching clean optional
checkout can be reused; otherwise acquisition uses a private detached checkout fetched by exact commit with Git global
configuration, prompting and credential helpers disabled. It never installs dependencies from the module repository.
The source and verifier identities are written to an untracked acquisition receipt and rechecked after execution.

Each case executes native pytest with the selected module's Observer in a fresh isolated Python process using existing
core environment dependencies. The real observation is then consumed by that module's actual portable adapter. Only
the capsule subprocess transport and fixed observation path are redirected; validation, coverage policy, findings and
severity remain real. A subprocess proxy avoids modifying the shared subprocess module. Import origins are verified.

Acquisition, authentication, imports and native execution are fixture setup preconditions. Missing dependencies or
transport errors produce setup errors, never skips or expected behavioral failures. The body of each test asserts the
required error finding only after native pytest exits zero with the expected actual outcomes and coverage inventory.

The six cases are skip, XFAIL, non-strict XPASS, empty-reason XPASS, absent reviewed-source coverage and low reviewed-source
coverage under a native zero-percent floor. Outcome cases measure their entire production source. Coverage cases contain
only passing native tests and prove respectively absence or less than 80 percent production coverage.

The new test file contains its own acquisition and subprocess helpers so proof inputs can be frozen without changing
shared conftests or scripts. A new mapping binds exactly six selectors. An independent reviewer must accept that mapping
before protected RED publication. After actual CI RED, only the docs lock and necessary documentation are updated to a
final accepted CI-signed module source; tests, helpers and mapping stay byte-identical. The old docs-16 proof and
`ci/module-fixture.lock.json` are never edited by this change.

This is native pytest plus adapter contract evidence. It is not full capsule acceptance, cross-platform execution support
or authority to publish an unsigned/unmerged candidate. Public signed release and Linux corpus acceptance remain separate.

The dedicated Hatch test environment must declare `pytest-cov`, matching the existing development dependency and
frozen CI graph, because the native subprocess deliberately loads that plugin. Missing plugins remain setup errors;
local bootstrap failure does not replace the six retained behavioral RED cases. This adds no adapter or proof override.
