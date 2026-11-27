## Why

Core promotion checks need to exercise the reviewed documentation fixture after revocation of the previous module signing key.

## What Changes

- Authenticate the existing documentation source with its exact repository, commit, tree and package digest from the protected base checkout.
- Keep strict base-verifier signature checks for other fixtures and older base snapshots without the reviewed digest.
- Preserve both Python command strings while resolving the two implicit concatenation findings on #771.

## Impact

Docs Review and CLI Command Validation share the same fixture checks. Runtime admission, the 0.55.4 cutoff and package publication stay outside this change.
