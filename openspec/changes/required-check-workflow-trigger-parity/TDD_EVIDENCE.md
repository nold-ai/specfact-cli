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
