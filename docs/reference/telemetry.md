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

### Option 1: Local-only (No endpoint or auth needed) ⭐ Simplest

**No authentication required!** Telemetry works out-of-the-box with local storage only.

**Quick start:**

```bash
# Enable telemetry (local storage only)
echo "true" > ~/.specfact/telemetry.opt-in
```

That's it! Telemetry data will be stored in `~/.specfact/telemetry.log` (JSONL format). You can inspect, rotate, or delete this file anytime.

**Note:** If you later create `~/.specfact/telemetry.yaml` with `enabled: true`, the config file takes precedence and the `.opt-in` file is no longer needed.

**Benefits:**

- ✅ No setup required - works immediately
- ✅ No authentication needed
- ✅ Your data stays local (privacy-first)
- ✅ You own the data file

### Option 2: Remote export (Requires endpoint and auth)

If you want to send telemetry to a remote collector (for dashboards, analytics, etc.), you'll need:

1. **An OTLP collector endpoint** (self-hosted or cloud service like Grafana Cloud)
2. **Authentication credentials** (if your collector requires auth)

**When you need auth:**

- Using a **cloud service** (Grafana Cloud, Honeycomb, etc.) - you sign up and get API keys
- Using a **self-hosted collector with auth** - you configure your own auth
- Using a **company's existing observability stack** - your team provides credentials

**When you DON'T need auth:**

- Using a **self-hosted collector without auth** (local development)
- **Local-only mode** (no endpoint = no auth needed)

### Recommended: Config file (persistent)

For remote export (or local-only with persistent config), create `~/.specfact/telemetry.yaml` with your telemetry configuration.

**Important:** If you have `enabled: true` in `telemetry.yaml`, you **do NOT need** the `.opt-in` file. The config file takes precedence. The `.opt-in` file is only used as a fallback if the config file doesn't exist or has `enabled: false`.

**Quick start:** Copy the example template:

```bash
# Copy the example template
cp resources/templates/telemetry.yaml.example ~/.specfact/telemetry.yaml

# Or if installed via pip/uvx, find it in the package:
# On Linux/Mac: ~/.local/share/specfact-cli/resources/templates/telemetry.yaml.example
# Then edit ~/.specfact/telemetry.yaml with your settings
```

**Manual setup:** Create `~/.specfact/telemetry.yaml` with your telemetry configuration:

```yaml
# Enable telemetry
enabled: true

# OTLP endpoint (HTTPS recommended for corporate environments)
# Example for Grafana Cloud:
endpoint: "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp/v1/traces"

# Authentication headers
# For Grafana Cloud, use Basic auth with your instance-id:api-key (base64 encoded)
headers:
  Authorization: "Basic YOUR_BASE64_ENCODED_CREDENTIALS_HERE"

# Optional: Advanced configuration
service_name: "specfact-cli"  # Custom service name (default: "specfact-cli")
batch_size: 512               # Batch size (default: 512)
batch_timeout: 5              # Batch timeout in seconds (default: 5)
export_timeout: 10            # Export timeout in seconds (default: 10)
debug: false                  # Enable console output for debugging (default: false)
local_path: "~/.specfact/telemetry.log"  # Local log file path (default: ~/.specfact/telemetry.log)
```

**Benefits:**

- Persistent configuration (survives shell restarts)
- All settings in one place
- Easy to version control or share with team
- Environment variables can still override (for temporary changes)

### Alternative: Environment variables (temporary)

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

**Note:** Environment variables override config file settings (useful for temporary testing).

### Legacy: Simple opt-in file (backward compatibility)

Create `~/.specfact/telemetry.opt-in` with:

```text
true
```

Remove the file (or set it to `false`) to opt out again.

**Note:** This method only enables telemetry with local storage. For OTLP export, use the config file or environment variables.

**Precedence:** If you have both `telemetry.yaml` (with `enabled: true`) and `telemetry.opt-in`, the config file takes precedence. The `.opt-in` file is only checked if the config file doesn't exist or has `enabled: false`.

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

## Why Opt In? (Win-Win-Win)

Telemetry creates a **mutual benefit cycle**: you help us build better features, we prioritize what you need, and the community benefits from collective insights.

### 🎯 For You (The User)

**Shape the roadmap:**

- Your usage patterns directly influence what we build next
- Features you use get prioritized and improved
- Pain points you experience get fixed faster

**Validate your approach:**

- Compare your metrics against community benchmarks
- See if your results align with other users
- Build confidence that you're using SpecFact effectively

**Get better features:**

- Data-driven prioritization means we build what matters
- Your usage helps us understand real-world needs
- You benefit from features built based on actual usage patterns

**Prove value:**

- Community metrics help justify adoption to your team
- "X% of users prevented Y violations" is more convincing than anecdotes
- Helps make the case for continued investment

### 🚀 For SpecFact (The Project)

**Understand real usage:**

- See which commands are actually used most
- Identify pain points and unexpected use cases
- Discover patterns we wouldn't know otherwise

**Prioritize effectively:**

- Focus development on high-impact features
- Fix bugs that affect many users
- Avoid building features nobody uses

**Prove the tool works:**

- Aggregate metrics demonstrate real impact
- "Contracts caught 3.7x more bugs than tests" is more credible with data
- Helps attract more users and contributors

**Build credibility:**

- Public dashboards show transparency
- Data-backed claims are more trustworthy
- Helps the project grow and succeed

### 🌍 For the Community

**Collective proof:**

- Aggregate metrics validate the contract-driven approach
- Helps others decide whether to adopt SpecFact
- Builds momentum for the methodology

**Knowledge sharing:**

- See what works for other teams
- Learn from community patterns
- Avoid common pitfalls

**Open source contribution:**

- Low-effort way to contribute to the project
- Helps SpecFact succeed, which benefits everyone
- Your anonymized data helps the entire community

### Real-World Impact

**Without telemetry:**

- Roadmap based on assumptions
- Hard to prove impact
- Features may not match real needs

**With telemetry:**

- "71% of bugs caught by early adopters were contract violations"
- "Average user prevented 12 regressions per week"
- "Most-used command: `import.from_code` (67% of sessions)"
- Roadmap based on real usage data

### The Privacy Trade-Off

**What you share:**

- Anonymized usage patterns (commands, metrics, durations)
- No personal data, repository names, or file contents

**What you get:**

- Better tool (features you need get prioritized)
- Validated approach (compare against community)
- Community insights (learn from others' patterns)

**You're in control:**

- Can opt-out anytime
- Data stays local by default
- Choose where to send data (if anywhere)

---

## Routing Telemetry to Your Stack

### Scenario 1: Local-only (No setup needed)

If you just want to track your own usage locally, **no endpoint or authentication is required**:

```bash
# Enable telemetry (local storage only)
echo "true" > ~/.specfact/telemetry.opt-in
```

Data will be stored in `~/.specfact/telemetry.log`. That's it!

### Scenario 2: Self-hosted collector (No auth required)

If you're running your own OTLP collector locally or on your network without authentication:

```yaml
# ~/.specfact/telemetry.yaml
enabled: true
endpoint: "http://localhost:4318/v1/traces"  # Your local collector
# No headers needed if collector doesn't require auth
```

### Scenario 3: Cloud service (Auth required)

If you're using a cloud service like Grafana Cloud, you'll need to:

1. **Sign up for the service** (e.g., <https://grafana.com/products/cloud/>)
2. **Get your API credentials** from the service dashboard
3. **Configure SpecFact** with the endpoint and credentials

**Example for Grafana Cloud:**

1. Sign up at <https://grafana.com/products/cloud/> (free tier available)
2. Go to "Connections" → "OpenTelemetry" → "Send traces"
3. Copy your endpoint URL and API key
4. Configure SpecFact:

```yaml
# ~/.specfact/telemetry.yaml
enabled: true
endpoint: "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp/v1/traces"
headers:
  Authorization: "Basic YOUR_BASE64_ENCODED_CREDENTIALS_HERE"

# Optional: Resource attributes (recommended for Grafana Cloud)
service_name: "specfact-cli"        # Service name (default: "specfact-cli")
service_namespace: "cli"             # Service namespace (default: "cli")
deployment_environment: "production" # Deployment environment (default: "production")
```

**Where to get credentials:**

- **Grafana Cloud**: Dashboard → Connections → OpenTelemetry → API key
- **Honeycomb**: Settings → API Keys → Create new key
- **SigNoz Cloud**: Settings → API Keys
- **Your company's stack**: Ask your DevOps/Platform team

### Scenario 4: Company observability stack (Team provides credentials)

If your company already has an observability stack (Tempo, Jaeger, etc.):

1. **Ask your team** for the OTLP endpoint URL
2. **Get authentication credentials** (API key, token, etc.)
3. **Configure SpecFact** with the provided endpoint and auth

### Using Config File (Recommended for remote export)

1. Deploy or reuse an OTLP collector that supports HTTPS (Tempo, Honeycomb, SigNoz, Grafana Cloud, etc.).
2. Copy the example template and customize it:

```bash
# Copy the template
cp resources/templates/telemetry.yaml.example ~/.specfact/telemetry.yaml

# Edit with your settings
nano ~/.specfact/telemetry.yaml
```

Or create `~/.specfact/telemetry.yaml` manually with your endpoint and authentication:

```yaml
enabled: true
endpoint: "https://your-collector.com/v1/traces"
headers:
  Authorization: "Bearer your-token-here"
```

### Using Environment Variables

1. Deploy or reuse an OTLP collector that supports HTTPS.
2. Set `SPECFACT_TELEMETRY_ENDPOINT` to your collector URL.
3. (Optional) Provide HTTP headers via `SPECFACT_TELEMETRY_HEADERS` for tokens or custom auth.
4. Keep `SPECFACT_TELEMETRY_OPT_IN=true`.

**Note:** Environment variables override config file settings.

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

**Do I need authentication to use telemetry?**

**No!** Authentication is only required if you want to send telemetry to a remote collector (cloud service or company stack). For local-only mode, just enable telemetry - no endpoint or auth needed:

```bash
echo "true" > ~/.specfact/telemetry.opt-in
```

**Where do I get authentication credentials?**

**It depends on your setup:**

- **Local-only mode**: No credentials needed ✅
- **Self-hosted collector (no auth)**: No credentials needed ✅
- **Grafana Cloud**: Sign up at <https://grafana.com/products/cloud/> → Get API key from dashboard
- **Honeycomb**: Sign up at <https://www.honeycomb.io/> → Settings → API Keys
- **Company stack**: Ask your DevOps/Platform team for endpoint and credentials

**Do I need to set up my own collector?**

**No!** Telemetry works with **local storage only** by default. If you want dashboards or remote analytics, you can optionally route to your own OTLP collector (self-hosted or cloud service).

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

**Do I need both `telemetry.yaml` and `telemetry.opt-in`?**

**No!** If you have `enabled: true` in `telemetry.yaml`, you **don't need** the `.opt-in` file. The config file takes precedence. The `.opt-in` file is only used as a fallback for backward compatibility or if you're using the simple local-only method without a config file.

**Precedence order:**

1. Environment variables (highest priority)
2. Config file (`telemetry.yaml` with `enabled: true`)
3. Simple opt-in file (`telemetry.opt-in`) - only if config file doesn't enable it
4. Defaults (disabled)

---

**Related docs:**  

- [`docs/brownfield-faq.md`](../brownfield-faq.md) – Brownfield workflows  
- [`docs/guides/brownfield-roi.md`](../guides/brownfield-roi.md) – Quantifying the savings  
- [`docs/examples/brownfield-django-modernization.md`](../examples/brownfield-django-modernization.md) – Example pipeline
