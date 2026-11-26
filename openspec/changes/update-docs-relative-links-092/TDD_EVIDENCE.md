## Before the update

- The locked 0.9.1 plugin raises `ArgumentError` when the relative-link
  probe reaches a tilde path for a nonexistent user.
- The frozen compatibility workflow test fails against unchanged `dev`
  because the build has no 0.9.2 constraint or reviewed artifact.

## After the update

- RubyGems reports SHA-256
  `9a1e7c58465f4fc63827a6d59ff95e1386b5f6b7683b633ec0230a144859c38c`
  for the downloaded 0.9.2 gem. The checked file matches that digest.
- All eight Ruby compatibility cases passed, four at each deployment path.
- The documentation site built with base URLs `""` and `"/preview"`.
- The docs validation tests passed. The frozen Linux lock changes only
  the target gem version and its constraint.
