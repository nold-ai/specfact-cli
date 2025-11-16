# Privacy-First Telemetry (Optional)

> **Opt-in analytics that highlight how SpecFact prevents brownfield regressions.**

SpecFact CLI ships with an **enterprise-grade, privacy-first telemetry system** that is **disabled by default** and only activates when you explicitly opt in. When enabled, we collect high-level, anonymized metrics to quantify outcomes like "what percentage of prevented regressions came from contract violations vs. plan drift." These insights help us communicate the value of SpecFact to the broader brownfield community (e.g., "71% of bugs caught by early adopters were surfaced only after contracts were introduced").

**Key Features:**

- ✅ **Disabled by default** - Privacy-first, requires explicit opt-in
- ✅ **Local storage** - Data stored in `~/.specfact/telemetry.log` (you own it)
- ✅ **OTLP HTTP** - Standard OpenTelemetry Protocol, works with any collector
- ✅ **Test-aware** - Automatically disabled in test environments
- ✅ **Configurable** - Service name, batch settings, timeouts all customizable
- ✅ **Enterprise-ready** - Graceful error handling, retry logic, production-grade reliability

---

## How to Opt In

### Fast opt-in (environment variable)

```bash
# Basic opt-in (local storage only)
export SPECFACT_TELEMETRY_OPT_IN=true

# Optional: send events to your own OTLP collector
export SPECFACT_TELEMETRY_ENDPOINT="https://telemetry.yourcompany.com/v1/traces"
export SPECFACT_TELEMETRY_HEADERS="Authorization: Bearer xxxx"

# Advanced configuration (optional)
export SPECFACT_TELEMETRY_SERVICE_NAME="my-specfact-instance"  # Custom service name
export SPECFACT_TELEMETRY_BATCH_SIZE="1024"                    # Batch size (default: 512)
export SPECFACT_TELEMETRY_BATCH_TIMEOUT="10"                  # Batch timeout in seconds (default: 5)
export SPECFACT_TELEMETRY_EXPORT_TIMEOUT="30"                 # Export timeout in seconds (default: 10)
export SPECFACT_TELEMETRY_DEBUG="true"                        # Enable console output for debugging
```

### Persistent opt-in (config file)

Create `~/.specfact/telemetry.opt-in` with:

```text
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

### For Individual Developers

- **Track your progress:** See how many violations you've prevented, features you've documented, and time you've saved
- **Validate your approach:** Compare your brownfield modernization metrics against community benchmarks
- **Contribute to open source:** Help improve SpecFact by sharing anonymized usage patterns (no personal data)

### For Teams & Enterprises

- **Prove ROI:** Quantify how SpecFact prevents regressions and reduces technical debt
- **Benchmark performance:** Compare your team's metrics against industry standards
- **Guide tooling decisions:** Data-driven insights help justify continued investment in contract-driven development
- **On-premise control:** Route telemetry to your own OTLP collector - nothing leaves your network

### For the Community

- **Quantify impact:** Aggregated metrics prove that SpecFact catches bugs modern linting/tests missed. Early adopters can point to community-wide stats like "contracts stopped 3.7x more bugs than unit tests during modernization."
- **Guide roadmap:** Seeing which commands and enforcement levels prevent the most regressions helps us prioritize VS Code features, spec converters, and new templates.
- **Build the case:** Your telemetry (anonymized) contributes to the larger story ("X% of prevented production issues were brownfield contract violations"), helping more teams adopt contract-driven development.

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

## Advanced Configuration

### Service Name Customization

Customize the service name in your telemetry data:

```bash
export SPECFACT_TELEMETRY_SERVICE_NAME="my-project-specfact"
```

This is useful when routing multiple projects to the same collector and want to distinguish between them.

### Batch Processing Tuning

Optimize batch processing for your use case:

```bash
# Larger batches for high-volume scenarios
export SPECFACT_TELEMETRY_BATCH_SIZE="2048"

# Longer timeouts for slower networks
export SPECFACT_TELEMETRY_BATCH_TIMEOUT="15"
export SPECFACT_TELEMETRY_EXPORT_TIMEOUT="60"
```

**Defaults:**

- `BATCH_SIZE`: 512 spans
- `BATCH_TIMEOUT`: 5 seconds
- `EXPORT_TIMEOUT`: 10 seconds

### Test Environment Detection

Telemetry is **automatically disabled** in test environments. No configuration needed - we detect:

- `TEST_MODE=true` environment variable
- `PYTEST_CURRENT_TEST` (set by pytest)

This ensures tests run cleanly without telemetry overhead.

### Debug Mode

Enable console output to see telemetry events in real-time:

```bash
export SPECFACT_TELEMETRY_DEBUG=true
```

Useful for troubleshooting telemetry configuration or verifying data collection.

## FAQ

**Does telemetry affect performance?**  
No. We buffer metrics in-memory and write to disk at the end of each command. When OTLP export is enabled, spans are batched and sent asynchronously. Telemetry operations are non-blocking and won't slow down your CLI commands.

**Can enterprises keep data on-prem?**  
Yes. Point `SPECFACT_TELEMETRY_ENDPOINT` to an internal collector. Nothing leaves your network unless you decide to forward it. All data is stored locally in `~/.specfact/telemetry.log` by default.

**Can I prove contracts are preventing bugs?**  
Absolutely. We surface `violations_detected` from commands like `specfact repro` so you can compare "bugs caught by contracts" vs. "bugs caught by legacy tests" over time, and we aggregate the ratios (anonymously) to showcase SpecFact's brownfield impact publicly.

**What happens if the collector is unavailable?**  
Telemetry gracefully degrades - events are still written to local storage (`~/.specfact/telemetry.log`), and export failures are logged but don't affect your CLI commands. You can retry exports later by processing the local log file.

**Is telemetry enabled in CI/CD?**  
Only if you explicitly opt in. We recommend enabling telemetry in CI/CD to track brownfield adoption metrics, but it's completely optional. Test environments automatically disable telemetry.

**How do I verify telemetry is working?**  

1. Enable debug mode: `export SPECFACT_TELEMETRY_DEBUG=true`
2. Run a command: `specfact import from-code --repo .`
3. Check local log: `tail -f ~/.specfact/telemetry.log`
4. Verify events appear in your OTLP collector (if configured)

---

**Related docs:**  

- [`docs/brownfield-faq.md`](../brownfield-faq.md) – Brownfield workflows  
- [`docs/guides/brownfield-roi.md`](../guides/brownfield-roi.md) – Quantifying the savings  
- [`docs/examples/brownfield-django-modernization.md`](../examples/brownfield-django-modernization.md) – Example pipeline
