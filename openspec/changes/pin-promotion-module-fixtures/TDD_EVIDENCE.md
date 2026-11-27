# Promotion module fixtures

The three fixture identity cases failed on protected dev `e90a4b57`.
The orchestrator and the standalone validation jobs supplied the fixture
checkout ref or repository through step outputs.

The same three cases failed for the expected checkout inputs on
`1afb4e87`, the new protected `dev` base after PR #800.

After pinning the nine checkouts, all 124 targeted tests passed on
Python 3.12.13. The tests cover the pinned inputs, documentation checkout
identity, authenticated package handling, and the existing scheduled
fixture verification. The three modified workflows passed actionlint.
The live promotion CodeQL result is pending this change's integration.
