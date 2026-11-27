## Why

The former official module signing key may have been exposed. Prepare a cutoff that preserves independently verified official releases while rejecting later or altered bytes.

## What Changes

- Pin official archive and installed-file hashes to the modules registry snapshot present at the Core 0.55.4 release.
- Apply the same managed module check before dependency installation, on cached downloads, and when loading official modules from disk.
- Preserve the four bundled modules from the verified Core 0.55.4 PyPI wheel.
- Keep new official releases frozen until an explicit later authorization changes the cutoff.

## Impact

The existing key is no longer a trust source for managed official modules. The release cutoff is immutable. Released CLI versions need an upgrade to enforce this change.
