## Why

The documentation site's Jekyll relative-link resolver can fail during a build
when a link starts with a tilde username. Version 0.9.2 fixes this behavior and
corrects handling of titled links and protocol-relative URLs.

## What Changes

- Update the documentation bundle to the reviewed Jekyll relative-links 0.9.2 artifact.
- Keep the other locked gems and the frozen installation workflow.
- Exercise the existing Ruby compatibility check for both root and prefixed builds.

Refs #789.
