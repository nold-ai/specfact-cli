# Certificate trust-store regression

## Failing before dependency changes

On 2026-10-20 Europe/Berlin, the existing frozen lock was installed with
`uv sync --locked --all-extras` into an isolated environment using Python 3.13.14.
It installed certifi 2026.7.22. No dependency input had been edited.

Command from this worktree:

```bash
/private/tmp/specfact-dependency-audit-20261020/certifi-tools/bin/python -m pytest tests/unit/security/test_certificate_trust_store.py -q --no-cov
```

The actual SSL trust-store comparison failed as intended:

```text
Extra items in the left set:
'86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b'
1 failed in 0.06s
```

The installed bundle still trusted the compromised emSign ECC Root CA - G3.
The full local capture is
`/private/tmp/specfact-dependency-audit-20261020/certifi-root-red.log`.
The frozen audit independently reported GHSA-6q48-6c7w-9gw2 and the separate MCP
finding. Passing-after evidence must use the same test against the refreshed
frozen installation. This local record does not replace native CI execution proof.
