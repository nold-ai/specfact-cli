## Why

The protected consumer on promotion PR #771 reuses the exact development evidence, then reviews the accumulated Python diff against main. It found excessive branching in the retained PR786 upload validator and fixture, plus two direct dynamic-execution calls in an inline-code test.

## What Changes

- Keep the upload receipt's provider, time, digest, ZIP, and byte-for-byte validation checks while making each validation step independently readable.
- Keep the inline verifier and the standalone verifier equivalent.
- Execute the same checked-in workflow fragment in the test through Python's file runner with its existing synthetic inputs.

## Impact

This changes the maintenance surface of the retained proof verification and its tests. The recorded origin, frozen evidence, signed bytes, promotion policy, and review rules stay fixed.

The signed release candidate also addresses typed documentation fixtures,
duplicated CLI test cases, and module validation complexity identified by the
same full Code Review. The existing score floor and scanner inputs are retained.
