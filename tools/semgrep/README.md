# Semgrep Rules for SpecFact CLI

This directory contains Semgrep rules for detecting common async anti-patterns in Python code.

**Note**: This file (`tools/semgrep/async.yml`) is used for **development** (hatch scripts, local testing). For **runtime** use in the installed package, the file is bundled as `src/specfact_cli/resources/semgrep/async.yml` and will be automatically included in the package distribution.

## Rules

### `async.yml` - Python Async Anti-Patterns

Detects 13 categories of async/await issues:

#### ERROR Severity (Block PRs)

1. **asyncio-create-task-not-awaited** - Fire-and-forget tasks without reference
2. **blocking-sleep-in-async** - `time.sleep()` in async functions
3. **missing-await-on-coroutine** - Coroutine called without `await`
4. **event-loop-in-async-context** - Nested event loops (deadlock risk)
5. **sync-lock-in-async** - Threading locks in async code

#### WARNING Severity (Review Required)

6. **bare-except-in-async** - Bare except or silent exception handling
7. **missing-timeout-on-wait** - Async operations without timeouts
8. **blocking-file-io-in-async** - Synchronous file I/O in async functions
9. **asyncio-gather-without-error-handling** - `gather()` without error handling
10. **task-result-not-checked** - Background tasks with unchecked results

#### INFO Severity (Best Practice)

11. **missing-async-context-manager** - Context manager without variable binding
12. **sequential-await-could-be-parallel** - Opportunities for parallelization
13. **missing-cancellation-handling** - No `CancelledError` handling

## Usage

### Command Line

Run Semgrep with these rules:

```bash
# Scan entire project
semgrep --config tools/semgrep/async.yml .

# Scan specific directory
semgrep --config tools/semgrep/async.yml src/

# JSON output for CI
semgrep --config tools/semgrep/async.yml --json . > semgrep-results.json

# Auto-fix where possible
semgrep --config tools/semgrep/async.yml --autofix .
```

### Hatch Integration

```bash
# Run via hatch (recommended)
hatch run scan        # Run with custom args
hatch run scan-all    # Scan entire project
hatch run scan-json   # Generate JSON report
hatch run scan-fix    # Auto-fix violations
```

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run Semgrep Async Rules
  run: |
    pip install semgrep
    semgrep --config tools/semgrep/async.yml --error --json . > semgrep.json
    
- name: Upload Results
  uses: actions/upload-artifact@v4
  with:
    name: semgrep-results
    path: semgrep.json
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/semgrep/semgrep
  rev: v1.50.0
  hooks:
    - id: semgrep
      args: ['--config', 'tools/semgrep/async.yml', '--error']
```

## Rule Examples

### Fire-and-forget Task (ERROR)

```python
# ❌ Bad - task may be garbage collected
async def process():
    asyncio.create_task(long_running_task())

# ✅ Good - reference stored
async def process():
    task = asyncio.create_task(long_running_task())
    await task
```

### Blocking Sleep (ERROR)

```python
# ❌ Bad - blocks event loop
async def process():
    time.sleep(1)

# ✅ Good - yields control
async def process():
    await asyncio.sleep(1)
```

### Missing Await (ERROR)

```python
# ❌ Bad - coroutine never executes
async def process():
    fetch_data()  # Returns coroutine object

# ✅ Good - coroutine executed
async def process():
    await fetch_data()
```

### Sync Lock in Async (ERROR)

```python
# ❌ Bad - blocks event loop
async def process():
    lock = threading.Lock()
    with lock:
        await operation()

# ✅ Good - async lock
async def process():
    lock = asyncio.Lock()
    async with lock:
        await operation()
```

### Missing Timeout (WARNING)

```python
# ❌ Bad - may hang indefinitely
async def process():
    await external_api_call()

# ✅ Good - has timeout
async def process():
    await asyncio.wait_for(external_api_call(), timeout=30)
```

### Sequential Awaits (INFO)

```python
# ⚠️ Suboptimal - sequential
async def process():
    result1 = await fetch_user()
    result2 = await fetch_posts()

# ✅ Better - parallel
async def process():
    result1, result2 = await asyncio.gather(
        fetch_user(),
        fetch_posts(),
    )
```

## Customization

### Adding New Rules

1. Edit `async.yml`
2. Follow Semgrep pattern syntax
3. Test with: `semgrep --test tools/semgrep/async.yml`
4. Add examples to this README

### Disabling Rules

Inline comment:

```python
# nosemgrep: asyncio-create-task-not-awaited
asyncio.create_task(background_task())
```

Configuration file (`.semgrepignore`):

```bash
# Ignore test files
tests/
```

## Rule Severity Mapping

| Severity | CI Behavior | PR Status | Description |
|----------|-------------|-----------|-------------|
| ERROR | Fail build | ❌ Block | Critical correctness issues |
| WARNING | Pass with warnings | ⚠️ Review | Potential bugs or bad practices |
| INFO | Pass | ℹ️ Informational | Optimization opportunities |

## Resources

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Semgrep Rule Syntax](https://semgrep.dev/docs/writing-rules/rule-syntax/)
- [Python Async Best Practices](https://docs.python.org/3/library/asyncio-task.html)

## Contributing

When adding new rules:

1. Use descriptive IDs (kebab-case)
2. Include clear messages with fix hints
3. Add metadata (category, likelihood, impact, confidence)
4. Provide examples in this README
5. Test against false positives

---

**Maintained by**: SpecFact CLI Team
**Last Updated**: 2025-10-30
