# Required workflow trigger evidence

## Scope and baseline

On 2026-09-15 (Europe/Berlin), PR #732 head `bffeea78cb6f9db8f41b5207aa15ba77cb278ba2` retained original dev tree `a696d32965bdc1f702684f8d981dc28ece3e9ffd`. GitHub documentation confirms manual dispatch checks cannot satisfy required PR rules. Only the two native pull-request path filters are targeted.

## Actual RED before implementation

After strict specification validation, the new two-case regression ran against unchanged workflows:

```sh
hatch run python -m pytest tests/unit/workflows/test_required_check_workflow_triggers.py -q
```

Result: **2 failed in 0.59 seconds**, exit 1. `TRIGGER_RED.txt` records actual assertion failures for Docs Review `paths` and SpecFact CLI Validation `paths-ignore`. Ruff lint and format checks on the regression passed. This local result does not confer protected CI RED authority.

## Prospective authority and remaining validation

The `.github/` implementation paths require verified maturity. Retain the independently reviewed immutable test/mapping commit through canonical CI before editing workflows. Actual GREEN, required native PR checks, and final protected validation remain outstanding. Existing docs proof files and fixture identities are unchanged.

## Rejected first CI binding and fresh cycle

Canonical Requirements run `35026816358`, attempt 2, at source `b94350c7f748afe6e89c7e6a92423ebb9239d017` executed exactly two assertion failures with zero errors/skips (Python 3.12.14, pytest 9.1.1). Artifact `10419259913`, digest `sha256:b15096adfa9856f68f91210412d3af652e68a984aef1688ff672d85896c4d341`, retains the JUnit but reports `Red proof binding rejected: prior-red-proof-invalid`. It is **not accepted RED evidence**.

The unchanged provenance validator examines merge commits against their second parent. The earlier ancestry-only merge therefore included governed production paths in history even though its tree matched dev. The new `codex/bugfix-required-workflow-trigger-parity` branch starts directly at public dev `a4a04786588d61fbc9105137dbaf0236fce009ee`. Only the signed tests/spec commit is cherry-picked; selected tests, mappings and independent review bytes remain unchanged. PR #732 and its commits remain intact. New canonical CI RED must succeed at binding before production edits.

Independent source-mapping acceptance: <https://github.com/nold-ai/specfact-cli/issues/733#issuecomment-5688443069>. Source mapping digest `sha256:0dc4fe32a24bbe080f82f6f6e6a3cde9f3d5d5a5bfa63b9c98a2a27dae01fc0f`.
