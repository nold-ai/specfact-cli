## Context

The original proposal mixed validation workflow content, sub-skills, and installation. The preflight architecture makes that ownership ambiguous: a signed module must own the canonical workflow it implements, while core can safely own the reusable distribution mechanism. This rescope retains issue #251 and its current Feature hierarchy while removing content ownership.

## Goals / Non-Goals

**Goals:**

- Discover skill assets from installed modules through a stable descriptor contract.
- Verify source module, version, asset digest, supported workflow identity, and installation scope.
- Materialize a canonical `.agents/skills` layout that compatible tools can consume or translate.
- Make install/update/uninstall deterministic, idempotent, and safe around user modifications.

**Non-Goals:**

- Author validation, preflight, remediation, or conformance workflow content.
- Generate instruction files or external harness packages.
- Install hooks or execute a skill during installation.

## Decisions

### 1. Module is the content source of truth

An installed module exposes a versioned skill descriptor and immutable asset digests. Core validates and copies those assets; it does not rewrite workflow semantics. A skill identity includes module ID/version, skill ID/version, canonical entrypoint, content digest, and declared compatibility.

### 2. Canonical export is `.agents/skills`

The portable project export is `.agents/skills/<skill-id>/SKILL.md` with supporting files kept beneath that skill directory. Harness-specific locations are produced by later instruction/export adapters from the same verified source, never treated as independent canonical content.

### 3. Safe install inventory

Core records exactly which files it installed and their digests. Reinstall is idempotent. Update or uninstall stops on user-modified files unless an explicit conflict policy is selected. Unrelated skills and harness assets are never removed.

### 4. Collision and trust fail closed

Two modules cannot silently claim the same canonical skill ID. Untrusted, unsigned where policy requires signing, incompatible, or digest-mismatched assets are not installed. Diagnostics identify the competing identities and remediation options.

### 5. First consumer follows checkpoint/conformance publication

The signed modules #434 identity supplies `specfact-preflight` and the bounded implementation-check workflow. #251 discovers and exports them unchanged. This proves the generic mechanism but does not couple the installer to preflight or checkpoint semantics.

## Risks / Trade-offs

- **Module/harness content drift:** Preserve canonical module digest through every export.
- **User file overwrite:** Inventory digests and explicit conflict resolution.
- **Skill ID collision:** Fail closed with source identities.
- **Core content creep:** Tests assert byte/semantic pass-through rather than core-authored workflow text.

## Migration and Rollback

Existing manually installed skills remain untouched until explicitly adopted. Rollback removes only inventory-owned files whose current digests match and leaves module packages installed. A failed update retains the last verified installation.

## Open Questions Deferred to Implementation

- Exact descriptor location in the module package contract.
- User-scope canonical root for each supported operating system.
- Whether exporters copy assets or use a generated reference when a harness supports one.
