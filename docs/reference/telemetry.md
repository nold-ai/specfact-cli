# Privacy-First Telemetry (Optional)

> **Opt-in analytics that highlight how SpecFact prevents brownfield regressions.**

SpecFact CLI now ships with a telemetry system that is **disabled by default** and only activates when you explicitly opt in. When enabled, we collect high-level, anonymized metrics so we can quantify outcomes like “what percentage of prevented regressions came from contract violations vs. plan drift.” These insights help us communicate the value of SpecFact to the broader brownfield community (e.g., “71% of bugs caught by early adopters were surfaced only after contracts were introduced”).

---

## How to Opt In

### Fast opt-in (environment variable)

```bash
export SPECFACT_TELEMETRY_OPT_IN=true
# Optional: send events to your own OTLP collector
export SPECFACT_TELEMETRY_ENDPOINT="https://telemetry.yourcompany.com/v1/traces"
export SPECFACT_TELEMETRY_HEADERS="Authorization: Bearer xxxx"
```

### Persistent opt-in (config file)

Create `~/.specfact/telemetry.opt-in` with:

```
true
```

Remove the file (or set it to `false`) to opt out again.

### Local storage only (default)

If no OTLP endpoint is provided, telemetry is persisted as JSON lines in `~/.specfact/telemetry.log`. You own this file—feel free to rotate, inspect, or delete it at any time.

---

## Data We Collect (and Why)

| Field | Description | Example |
| --- | --- | --- |
| `command` | CLI command identifier | `import.from_code` |
| `mode` | High-level command family | `repro` |
| `execution_mode` | How the command ran (agent vs. AST) | `agent` |
| `files_analyzed` | Count of Python files scanned (rounded) | `143` |
| `features_detected` | Number of features plan import discovered | `27` |
| `stories_detected` | Total stories extracted from code | `112` |
| `checks_total` | Number of validation checks executed | `6` |
| `checks_failed` / `violations_detected` | How many checks or contracts failed | `2` |
| `duration_ms` | Command duration (auto-calculated) | `4280` |
| `success` | Whether the CLI exited successfully | `true` |

**We never collect:**

- Repository names or paths
- File contents or snippets
- Usernames, emails, or hostnames

---

## Why Opt In?

- **Quantify impact:** Aggregated metrics help us prove that SpecFact is catching bugs modern linting/tests missed. Early adopters can point to community-wide stats like “contracts stopped 3.7x more bugs than unit tests during modernization.”
- **Guide roadmap:** Seeing which commands and enforcement levels prevent the most regressions helps us prioritize VS Code features, spec converters, and new templates.
- **Give back anonymously:** Your telemetry stays anonymous but still contributes to the larger story (“X% of prevented production issues were brownfield contract violations”).

---

## Routing Telemetry to Your Stack

1. Deploy or reuse an OTLP collector that supports HTTPS (Tempo, Honeycomb, SigNoz, etc.).
2. Set `SPECFACT_TELEMETRY_ENDPOINT` to your collector URL.
3. (Optional) Provide HTTP headers via `SPECFACT_TELEMETRY_HEADERS` for tokens or custom auth.
4. Keep `SPECFACT_TELEMETRY_OPT_IN=true`.

SpecFact will continue writing the local JSON log **and** stream spans to your collector using the OpenTelemetry data model.

---

## Inspecting & Deleting Data

```bash
# View the most recent events
tail -n 20 ~/.specfact/telemetry.log | jq

# Delete everything (immediate opt-out)
rm ~/.specfact/telemetry.log
unset SPECFACT_TELEMETRY_OPT_IN
```

---

## FAQ

**Does telemetry affect performance?**  
No. We buffer metrics in-memory and write to disk at the end of each command. When OTLP export is enabled, spans are batched and sent asynchronously.

**Can enterprises keep data on-prem?**  
Yes. Point `SPECFACT_TELEMETRY_ENDPOINT` to an internal collector. Nothing leaves your network unless you decide to forward it.

**Can I prove contracts are preventing bugs?**  
Absolutely. We surface `violations_detected` from commands like `specfact repro` so you can compare “bugs caught by contracts” vs. “bugs caught by legacy tests” over time, and we aggregate the ratios (anonymously) to showcase SpecFact’s brownfield impact publicly.

---

**Related docs:**  
- [`docs/brownfield-faq.md`](../brownfield-faq.md) – Brownfield workflows  
- [`docs/guides/brownfield-roi.md`](../guides/brownfield-roi.md) – Quantifying the savings  
- [`docs/examples/brownfield-django-modernization.md`](../examples/brownfield-django-modernization.md) – Example pipeline
