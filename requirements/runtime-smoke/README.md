# Frozen runtime smoke seed

This auxiliary lock supplies module-only dependencies to workspace-owned direct
and console smoke interpreters. It is not part of the shipped CLI graph. Shared
packages remain constrained to `requirements/ci/locked.txt`; marketplace pip has
no index. Dependency installation, frozen resolution and genuine CLI discovery
remain exercised; no module dependency check is skipped.

Generate after artifact review:

```bash
uv pip compile requirements/runtime-smoke/requirements.in --no-deps \
  --constraints requirements/runtime-smoke/locked.txt --python-version 3.12 \
  --only-binary :all: --generate-hashes --no-annotate --output-file /tmp/smoke-lock.txt
```

Copy the generated requirement body and bind it with exactly one
`# input-sha256:` digest of `requirements.in`. The frozen-delivery gate recompiles
under the committed constraints and rejects stale input bindings or hash bodies.
The separate audit and Socket checks remain required. Pip installs only wheels
with committed hashes into the child. Missing shared/transitive dependencies are
rejected by normal marketplace resolution.

Artifact review on **2026-10-11 Europe/Berlin**:

- Astroid 4.0.4, Dill 0.4.1, Mccabe 0.7.0 and Pylint 4.0.7 retain the already
  reviewed Code Review lock versions. This lock does not permit their shared
  dependencies to upgrade the CI environment. Pylint is seeded solely for the
  isolated Code Review module smoke fixture and is scanned through the existing
  exact `code-review-only` license scope. It is not added to shipped CLI metadata
  or the root development graph; the exception is not widened.
- Lz4 4.4.5: inspected wheel metadata and BSD license; CPython 3.12 macOS arm64
  and Linux x86_64 distribution hashes match the PyPI release metadata.
- BasedPyright 1.39.9 matches `tools/basedpyright/package.json`; MIT license,
  bundled Typeshed Apache/BSD notices, exact wrapper source inspected. Its Python
  wrapper launches the bundled checker through `nodejs_wheel.executable.node`.
- Nodejs-wheel-binaries 24.19.0: inspected MIT/package notices and wrapper;
  upstream tag `v24.19.0` resolves to `0a3c599f0c527c1d23d2bba420a456f28529aa98`.
  The exact tag's CMake recipe compiles Node from upstream source and changes
  c-ares configuration. These are **not** repackaged byte-identical official Node
  binaries; an attempted binary comparison rejected that assumption. The reviewed
  source-build recipe explains the distinction; no binary-equivalence claim is
  made. This tool is a development smoke dependency, with broad Node upgrades
  outside the dependency consolidation scope.

Primary provenance:
[Lz4](https://pypi.org/pypi/lz4/4.4.5/json),
[BasedPyright](https://pypi.org/pypi/basedpyright/1.39.9/json),
[Node wheel](https://pypi.org/pypi/nodejs-wheel-binaries/24.19.0/json),
[exact build recipe](https://github.com/njzjz/nodejs-wheel/blob/0a3c599f0c527c1d23d2bba420a456f28529aa98/CMakeLists.txt),
[official Node release](https://nodejs.org/en/blog/release/v24.19.0).

| Inspected distribution | SHA-256 |
| --- | --- |
| `basedpyright-1.39.9-py3-none-any.whl` | `6b0837b9eba972c71895167ab9b127e6afdbc17abc92312e3f8d15ca82a5611c` |
| `lz4-4.4.5-cp312-cp312-macosx_11_0_arm64.whl` | `6d0bf51e7745484d2092b3a51ae6eb58c3bd3ce0300cf2b2c14f76c536d5697a` |
| `lz4-4.4.5-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `24092635f47538b392c4eaeff14c7270d2c8e806bf4be2a6446a378591c5e69e` |
| `nodejs_wheel_binaries-24.19.0-py2.py3-none-macosx_13_0_arm64.whl` | `e12cbfd69089504e42fb14194ce734a9dcf3eb38c820ca63dd511d36fb964e9c` |
| `nodejs_wheel_binaries-24.19.0-py2.py3-none-manylinux_2_28_x86_64.whl` | `4196a947bcc883f2003ab101762d729f3e99b5e86b75bd09151563403e2eceb8` |
