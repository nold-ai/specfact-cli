# Frozen runtime smoke seed

This auxiliary lock supplies **Lz4 4.4.5** to workspace-owned direct and console
smoke interpreters. The complete frozen `uv.lock` graph, matching the CI export, is installed
offline from the reviewed cache into each child first; parent site-packages and inherited Python
paths are excluded. Marketplace pip has no index and its normal
manifest/dependency validation remains exercised.

Runtime smoke uses the separately pinned portable module snapshot in
`ci/runtime-smoke-fixture.lock.json`: commit
`046d366c190af7a188d6f48953a96edb65e766db`, tree
`c5b44db3477d1c9ea8dae1dceab2af276d265353`.
This is the already reviewed documentation snapshot, with Code Review 0.50.1
compatible with CLI 0.55.5 and only Packaging/Requests Python dependencies.
Its real module declarations and archives are preserved. No dependency is
removed from a staged manifest and no module dependency check is skipped.

The native Requirements provider remains independently pinned at 69f0758 in
`ci/module-fixture.lock.json`. Its original RED artifacts and protocol are
unchanged. CI checks out both snapshots at full SHAs and verifies the portable
snapshot's tree and clean working directory before any module execution.
Locally set `SPECFACT_SMOKE_MODULES_REPO` to that clean portable checkout;
`SPECFACT_MODULES_REPO` continues to select the Requirements provider.

BasedPyright uses the existing committed npm lock and SHA-pinned Node setup.
Neither BasedPyright's Python package nor an unofficial Node runtime wheel is
part of this seed. The dependency-trust gate applies its existing prohibited
release and minimum-version policy to this auxiliary graph too.

Generate after artifact review:

```bash
uv pip compile requirements/runtime-smoke/requirements.in --no-deps \
  --constraints requirements/runtime-smoke/locked.txt --python-version 3.12 \
  --only-binary :all: --generate-hashes --no-annotate --output-file /tmp/smoke-lock.txt
```

Copy the generated body with one `# input-sha256:` digest of `requirements.in`.
Frozen delivery recompiles it under committed constraints. The separate audit,
license and Socket checks remain required; pip installs only hash-pinned wheels.
The child wheelhouse contains only the authenticated manifests' transitive closure,
selected from exact committed hashes and downloaded with `--require-hashes`.
Normal marketplace pip-tools resolution uses that directory with no index. Its
project configuration emits pins without repeating transport options already in
the environment. Missing shared/transitive dependencies or frozen hashes fail.

Artifact review on **2026-10-11 Europe/Berlin**: inspected Lz4 wheel metadata and
BSD license; macOS arm64 and Linux x86_64 hashes match the exact
[PyPI 4.4.5 metadata](https://pypi.org/pypi/lz4/4.4.5/json).

| Inspected distribution | SHA-256 |
| --- | --- |
| `lz4-4.4.5-cp312-cp312-macosx_11_0_arm64.whl` | `6d0bf51e7745484d2092b3a51ae6eb58c3bd3ce0300cf2b2c14f76c536d5697a` |
| `lz4-4.4.5-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `24092635f47538b392c4eaeff14c7270d2c8e806bf4be2a6446a378591c5e69e` |
