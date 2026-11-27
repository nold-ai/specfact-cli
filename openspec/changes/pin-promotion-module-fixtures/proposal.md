## Why

Core promotion PR #771 reports four high-severity CodeQL alerts where Actions jobs check out companion module fixtures through dynamically evaluated repository or ref inputs. Draft PR #796 contains the fixture pinning approach. The retired scanner lane from that draft is outside this change.

## What changes

- Pin the existing module and documentation fixtures by literal official repository and reviewed commit in CI checkout steps.
- Retain lockfile commit and tree validation, protected documentation package digest validation, and disabled checkout credential persistence.
- Keep the existing workflow events, frozen dependency inputs, and publishing controls.

## Impact

The affected checks are core CLI validation, Docs Review, and the module-backed jobs in the PR orchestrator. The fixture contents and public application package are unchanged.
