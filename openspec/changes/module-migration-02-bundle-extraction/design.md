# Design: Bundle Extraction and Marketplace Publishing

## Context

`module-migration-01-categorize-and-group` added category metadata (`category`, `bundle`, `bundle_group_command`, `bundle_sub_command`) to all 21 `module-package.yaml` files and introduced the `groups/` layer that mounts the 5 category umbrella commands. This change (module-migration-02) is the extraction step: it physically moves module source code from the core package into independently versioned bundle packages in the `specfact-cli-modules` repository, signs and publishes those packages to the marketplace registry, and wires the bundle-level dependency graph.

**Current state after module-migration-01:**

- 21 modules have category metadata in `module-package.yaml`
- Category group commands (`specfact project`, `specfact code`, etc.) are live
- Backward-compat flat shims are registered
- All 21 module sources remain in `src/specfact_cli/modules/*/src/`
- `specfact-cli-modules/registry/index.json` has schema v1.0.0 but `modules: []`

**After this change:**

- 5 bundle packages in `specfact-cli-modules/packages/`
- Module sources moved to bundle namespaces; re-export shims left in core
- `index.json` populated with 5 signed official-tier bundle entries
- Shared code audited; any cross-bundle private imports factored into `specfact_cli.common`
- All module-package.yaml checksums/signatures updated after source move

**Constraints:**

- Must not break any existing `specfact <command>` invocations (compat shims + groups/ layer)
- Must not break `specfact_cli.modules.*` imports (re-export shims in `src/`)
- Must satisfy all existing module-security contracts (SHA-256 + Ed25519)
- Must work offline (signing and verification do not require internet)
- All new public APIs must carry `@icontract` and `@beartype` decorators

## Goals / Non-Goals

**Goals:**

- Create `specfact-cli-modules/packages/<bundle>/` for all 5 bundles
- Move module source into bundle namespaces with correct import updates
- Leave re-export shims in `src/specfact_cli/modules/*/src/`
- Audit and factor shared code into `specfact_cli.common`
- Sign and publish all 5 bundle tarballs to `specfact-cli-modules/registry/`
- Populate `index.json` with tier, publisher, dependency, and integrity fields
- Add `official` tier concept to `crypto_validator.py` and `module_installer.py`
- Update all `module-package.yaml` checksums and signatures after source move

**Non-Goals:**

- Removing bundled module source from `pyproject.toml` / core package (module-migration-03)
- Removing backward-compat shims (module-migration-03)
- Changing CLI-visible command topology (done by module-migration-01)
- Implementing the first-run bundle selection UI (done by module-migration-01)

## Decisions

### Decision 1: Bundle namespace naming convention

**Options:**

- **A**: `specfact_<category_slug>` (e.g., `specfact_codebase`, `specfact_project`)
- **B**: `specfact_cli_<category_slug>` (mirrors core namespace)
- **C**: `specfact.<category_slug>` (namespace package)

**Choice: A (`specfact_<category_slug>`)**

**Rationale:**

- Clean break from `specfact_cli` namespace — signals these are marketplace packages, not core
- Short and predictable: `from specfact_codebase.analyze import app`
- Consistent with PyPI package names (`specfact-codebase` → `specfact_codebase`)
- Avoids namespace package complexity of option C

**Bundle namespace mapping:**

```text
specfact-project  → specfact_project
specfact-backlog  → specfact_backlog
specfact-codebase → specfact_codebase
specfact-spec     → specfact_spec
specfact-govern   → specfact_govern
```

### Decision 2: Re-export shim implementation strategy

**Options:**

- **A**: `__getattr__` module-level hook in the shim module (lazy, per-attribute)
- **B**: Explicit star import (`from specfact_codebase.validate import *`) at shim module top
- **C**: Explicit re-export of specific public symbols only

**Choice: A (`__getattr__` hook)**

**Rationale:**

- Zero maintenance — any new symbol added to the bundle module is automatically available through the shim
- Lazy: no import cost until the attribute is actually accessed
- Emits `DeprecationWarning` on first access, not on import (avoids startup noise)
- Clean: the shim file is 5–10 lines regardless of module size

**Shim template:**

```python
"""Re-export shim: specfact_cli.modules.validate → specfact_codebase.validate.

Deprecated: Use `from specfact_codebase.validate import ...` directly.
This shim will be removed in the next major version.
"""
import importlib
import warnings

_TARGET = "specfact_codebase.validate"


def __getattr__(name: str) -> object:
    warnings.warn(
        f"specfact_cli.modules.validate is deprecated; use {_TARGET} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    mod = importlib.import_module(_TARGET)
    return getattr(mod, name)
```

### Decision 3: Shared-code audit approach

**Options:**

- **A**: Manual audit of import graphs before extraction
- **B**: Automated import graph analysis using `importlab` or `pyright --outputjson`
- **C**: Attempt extraction and rely on test failures to surface cross-bundle imports

#### Choice: B (automated import graph analysis), with A as fallback

**Rationale:**

- A 21-module codebase has too many imports to audit manually with confidence
- `pyright --outputjson` or `pydeps` can produce the import graph without running the code
- Automation produces a reproducible audit artifact that can be committed
- Option C is too risky — runtime failures may not surface all import paths in tests

**Audit command (pre-extraction):**

```bash
hatch run python -c "
import ast, pathlib, json, sys

# Collect all intra-module imports across src/specfact_cli/modules/
# and flag any that cross bundle boundaries
"
```

### Decision 4: publish-module.py extension strategy

**Options:**

- **A**: New `scripts/publish-bundle.py` separate from existing `publish-module.py`
- **B**: Extend `publish-module.py` with a `--bundle` flag and bundle-specific code path

#### Choice: B (extend publish-module.py with --bundle)

**Rationale:**

- Single publish script is easier to maintain and discover
- Bundle publishing reuses all the tarball, signing, and index-write logic from marketplace-02
- `--bundle <name>` flag selects the bundle mode; non-bundle module publish is unchanged

**Extended CLI signature:**

```bash
# Existing (marketplace-02):
python scripts/publish-module.py --module <module-name> --key-file <pem>

# New (bundle mode):
python scripts/publish-module.py --bundle specfact-codebase --key-file <pem> [--version 0.29.0]
python scripts/publish-module.py --bundle all --key-file <pem>  # publishes all 5 bundles
```

### Decision 5: Official-tier allowlist storage

**Options:**

- **A**: Hardcoded in `crypto_validator.py` (`OFFICIAL_PUBLISHERS = {"nold-ai"}`)
- **B**: Loaded from `~/.specfact/config.yaml` (configurable per user)
- **C**: Embedded in the project public key metadata (key-bound)

#### Choice: A (hardcoded allowlist)

**Rationale:**

- The `official` tier is a canonical concept — it should not be overridable by user config
- Keeps trust semantics auditable at source level
- Future extension: if additional official publishers are added, the allowlist is updated in a versioned code change, not silently in user config

### Decision 6: Atomic index.json write

**Rationale:** `index.json` is read by the marketplace installer. A partial write could corrupt the registry. Using `tempfile + os.replace` (atomic on POSIX) prevents partial-write corruption.

```python
import json, os, tempfile, pathlib

def write_index(index_path: pathlib.Path, index: dict) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", dir=index_path.parent, suffix=".tmp", delete=False
    ) as f:
        json.dump(index, f, indent=2)
        tmp_path = f.name
    os.replace(tmp_path, index_path)
```

## Architecture

### Directory layout after extraction

```text
specfact-cli-modules/
  packages/
    specfact-project/
      module-package.yaml          # bundle manifest: tier, publisher, deps, version
      src/
        specfact_project/
          __init__.py
          project/                 # moved from specfact_cli.modules.project.src.project
          plan/
          import_cmd/
          sync/
          migrate/
    specfact-backlog/
      module-package.yaml
      src/
        specfact_backlog/
          __init__.py
          backlog/
          policy_engine/
    specfact-codebase/
      module-package.yaml
      src/
        specfact_codebase/
          __init__.py
          analyze/
          drift/
          validate/
          repro/
    specfact-spec/
      module-package.yaml          # bundle_dependencies: [nold-ai/specfact-project]
      src/
        specfact_spec/
          __init__.py
          contract/
          spec/
          sdd/
          generate/
    specfact-govern/
      module-package.yaml          # bundle_dependencies: [nold-ai/specfact-project]
      src/
        specfact_govern/
          __init__.py
          enforce/
          patch_mode/

  registry/
    index.json                     # 5 official bundle entries (populated)
    modules/
      specfact-project-0.29.0.tar.gz
      specfact-backlog-0.29.0.tar.gz
      specfact-codebase-0.29.0.tar.gz
      specfact-spec-0.29.0.tar.gz
      specfact-govern-0.29.0.tar.gz
    signatures/
      specfact-project-0.29.0.sig
      specfact-backlog-0.29.0.sig
      specfact-codebase-0.29.0.sig
      specfact-spec-0.29.0.sig
      specfact-govern-0.29.0.sig
```

### Re-export shim layout in core (specfact-cli repo)

```text
src/specfact_cli/modules/validate/src/validate/
  __init__.py          # re-export shim → specfact_codebase.validate
  (all other .py files deleted — content moved to specfact-codebase)
```

### index.json bundle entry schema

```json
{
  "id": "nold-ai/specfact-codebase",
  "namespace": "nold-ai",
  "name": "specfact-codebase",
  "description": "Codebase quality bundle: analyze, drift, validate, repro.",
  "latest_version": "0.29.0",
  "core_compatibility": ">=0.29.0,<1.0.0",
  "download_url": "https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/main/registry/modules/specfact-codebase-0.29.0.tar.gz",
  "checksum_sha256": "<sha256-hex>",
  "signature_url": "https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/main/registry/signatures/specfact-codebase-0.29.0.sig",
  "tier": "official",
  "publisher": "nold-ai",
  "bundle_dependencies": []
}
```

### crypto_validator.py extension (official tier)

```python
OFFICIAL_PUBLISHERS: frozenset[str] = frozenset({"nold-ai"})

@require(lambda manifest: manifest.get("tier") in {"official", "community", "unsigned"})
@beartype
def validate_module(bundle_path: Path, manifest: dict[str, str]) -> ValidationResult:
    """Validate module artifact integrity and tier trust."""
    tier = manifest.get("tier", "unsigned")

    if tier == "official":
        publisher = manifest.get("publisher", "")
        if publisher not in OFFICIAL_PUBLISHERS:
            raise SecurityError(
                f"Publisher '{publisher}' is not in the official allowlist: {OFFICIAL_PUBLISHERS}"
            )

    # existing checksum + signature verification ...
    _verify_checksum(bundle_path, manifest["integrity_sha256"])
    _verify_signature(bundle_path, manifest["signature_ed25519"])

    return ValidationResult(tier=tier, publisher=publisher, signature_valid=True)
```

### Publish pipeline flow

```text
scripts/publish-module.py --bundle specfact-codebase --key-file key.pem
  │
  ├─ Locate bundle directory: specfact-cli-modules/packages/specfact-codebase/
  ├─ Read module-package.yaml → extract version, name, description
  ├─ Check: version > current latest_version in index.json (reject downgrade)
  │
  ├─ Package: tar.gz all files (reject path-traversal entries)
  ├─ Compute SHA-256 of tarball
  ├─ Sign tarball with Ed25519 (key-file) → .sig file
  │
  ├─ Write tarball to registry/modules/specfact-codebase-<ver>.tar.gz
  ├─ Write signature to registry/signatures/specfact-codebase-<ver>.sig
  │
  ├─ Inline verify (verify-modules-signature.py logic): checksum + Ed25519
  │    └─ abort if verification fails (do not update index.json)
  │
  └─ Atomic write: update index.json with new bundle entry
       ├─ write to .tmp file
       └─ os.replace → index.json
```

## Risks / Trade-offs

### Risk 1: Missed cross-bundle private import causes runtime ImportError after shim replacement

**Mitigation:** Automated import graph audit before any source move. TDD: unit tests that import all module public APIs through the shim paths — failures surface before extraction is complete.

### Risk 2: Circular import in specfact_project (sync ↔ plan)

**Mitigation:** Both `plan` and `sync` are in the same `specfact_project` namespace. Intra-bundle imports are allowed. The circular-ish dependency (sync imports plan, plan has no direct sync import) is resolved by Python's import system within the namespace.

### Risk 3: Large diff makes PR review difficult

**Mitigation:** Structure the change as a sequence of atomic commits: (1) shared-code audit + factoring, (2) one bundle extracted per commit, (3) re-export shims, (4) signing + publish, (5) index.json. Reviewers can follow each commit independently.

### Risk 4: publish-module.py not yet available (marketplace-02 in progress)

**Mitigation:** This change is hard-blocked on `module-migration-01` which is hard-blocked on `marketplace-02`. By the time module-migration-02 is implemented, `publish-module.py` will exist. If it is incomplete, extend it rather than creating a parallel script.

### Risk 5: Ed25519 key management in CI

**Mitigation:** The private key used for signing is not committed to the repository. The publish pipeline requires `--key-file <path>` argument; CI jobs receive the key via a repository secret. Documentation task includes updating CI workflow docs.

## Open Questions

**Q1: Should bundle packages be published to PyPI in addition to the marketplace registry?**

- Recommendation: Defer to module-migration-03. The marketplace registry is sufficient for the first publish. PyPI publishing adds complexity (PyPI accounts, twine, package names) that belongs in a separate change.
- **Gap analysis update (2026-03-02):** Migration-03's proposal does not include PyPI publishing in its scope (Gap 7 in `GAP_ANALYSIS.md`). Ownership remains unresolved. If not added to migration-03's What Changes, a dedicated `module-migration-06-pypi-publishing` change should be created and added to `CHANGE_ORDER.md`. Without PyPI publishing, `pip install specfact-codebase` does not work — only the marketplace registry path is available.

**Q2: Should specfact-cli-modules be a git submodule of specfact-cli?**

- Recommendation: No. Keep them as separate repositories. The publish script operates on a local checkout of `specfact-cli-modules`; CI uses separate checkout steps.

**Q3: What happens when a bundle module source changes — does the bundle version need to bump?**

- Recommendation: Yes. Any source change to a member module requires a patch version bump of the containing bundle. The publish script enforces this (rejects same-version re-publish).
