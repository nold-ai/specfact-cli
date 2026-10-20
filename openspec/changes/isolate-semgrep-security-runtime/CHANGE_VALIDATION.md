# Change validation

The owner requested actual fixes on 2026-10-20 Europe/Berlin. This active delta
covers the immediate certifi trust-store correction. The native scanner proposal
from commit `1a3af0cde3e3c13bdefc0de1c914d2837469a486` is preserved separately in
`openspec/parking-lot/replace-vulnerable-scanner-runtime/`, including all fourteen
unimplemented scenarios, requirements mapping and historical review evidence.
No native migration, component audit, parity or artifact admission is claimed here.

The original frozen audit reports certifi 2026.7.22 / GHSA-6q48-6c7w-9gw2 and
MCP 1.29.0 / CVE-2026-59951. The reviewed certifi advisory recommends >=2026.10.19.
The old hash-verified bundle contains the compromised CA fingerprint; the patched
bundle excludes it. Authored test evidence must be recorded before dependency edits.
The same test and canonical frozen checks must pass after refresh. Full security
audit remains blocked until MCP is actually remediated.

Sources accessed 2026-10-20.

- [Reviewed certifi advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
- [Failed frozen audit](https://github.com/nold-ai/specfact-cli/actions/runs/39492552089/job/118869420960).
- [Certifi release metadata](https://pypi.org/pypi/certifi/2026.10.19/json).
