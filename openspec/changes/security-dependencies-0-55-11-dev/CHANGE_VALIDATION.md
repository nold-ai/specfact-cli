# Current validation

The owner explicitly requires the missing security updates to enter `dev`
before a main release. This new change covers only that additive follow-up.
The delivered `isolate-semgrep-security-runtime` change and all original proof
identities remain unchanged. No old exact-head grant transfers.

At dev `9b5ad1e78430cc0b061cb16de42f73de96f4f312`, the new spec validates with
`openspec validate security-dependencies-0-55-11-dev --strict`. Targeted Ruff
0.15.20 checks pass. The network-enabled 15-case local failing-before run
contains 15 intended assertion failures, zero errors and zero skips, with all
recorded inputs unchanged. An earlier run's three installation failures remain
setup evidence only, despite its matching pytest failure count.
These observations are not full-project quality or native CI acceptance.

Only spec/tests and authentic local proof have been prepared. The seven
production inputs remain byte-identical to the dev base. The normal Hatch
environment, independent corrected-prefix review, normal hooks and CI signing
are being prepared. No signed dev PR, native RED, production change, passing
final wave or actual forge-ready state is claimed.

Live issue #780 is open, status Todo, parent #747, with security/dependency
labels and project assignment. Open blockers #783 and #523 remain recorded.
An internal wiki mirror is required for the new scope and remains a separate
bounded sibling-write item; the prior exact two-file grant is not reused.

Current risks are the expired native bootstrap, accidental loss of dev's third
audit/runtime protections, and stale authority after a head change. Keep the
bootstrap prerequisite explicit, review scoped hunks, and obtain fresh final
head/tree authority. No merge or release is authorized.
