# Brownfield Modernization FAQ

> **Frequently asked questions about using SpecFact CLI for legacy code modernization**

---

## General Questions

### What is brownfield modernization?

**Brownfield modernization** refers to improving, refactoring, or migrating existing (legacy) codebases, as opposed to greenfield development (starting from scratch).

SpecFact CLI is designed specifically for brownfield projects where you need to:

- Understand undocumented legacy code
- Modernize without breaking existing behavior
- Extract specs from existing code (code2spec)
- Enforce contracts during refactoring

---

## Code Analysis

### Can SpecFact analyze code with no docstrings?

**Yes.** SpecFact's code2spec analyzes:

- Function signatures and type hints
- Code patterns and control flow
- Existing validation logic
- Module dependencies
- Commit history and code structure

No docstrings needed. SpecFact infers behavior from code patterns.

### What if the legacy code has no type hints?

**SpecFact infers types** from usage patterns and generates specs. You can add type hints incrementally as part of modernization.

**Example:**

```python
# Legacy code (no type hints)
def process_order(user_id, amount):
    # SpecFact infers: user_id: int, amount: float
    ...

# SpecFact generates:
# - Precondition: user_id > 0, amount > 0
# - Postcondition: returns Order object
```

### Can SpecFact handle obfuscated or minified code?

**Limited.** SpecFact works best with:

- Source code (not compiled bytecode)
- Readable variable names
- Standard Python patterns

For heavily obfuscated code, consider:

1. Deobfuscation first (if possible)
2. Manual documentation of critical paths
3. Adding contracts incrementally to deobfuscated sections

### What about code with no tests?

**SpecFact doesn't require tests.** In fact, code2spec is designed for codebases with:

- No tests
- No documentation
- No type hints

SpecFact extracts specs from code structure and patterns, not from tests.

---

## Contract Enforcement

### Will contracts slow down my code?

**Minimal impact.** Contract checks are fast (microseconds per call). For high-performance code:

- **Development/Testing:** Keep contracts enabled (catch violations)
- **Production:** Optionally disable contracts (performance-critical paths only)

**Best practice:** Keep contracts in tests, disable only in production hot paths if needed.

### Can I add contracts incrementally?

**Yes.** Recommended approach:

1. **Week 1:** Add contracts to 3-5 critical functions
2. **Week 2:** Expand to 10-15 functions
3. **Week 3:** Add contracts to all public APIs
4. **Week 4+:** Add contracts to internal functions as needed

Start with shadow mode (observe only), then enable enforcement incrementally.

### What if a contract is too strict?

**Contracts are configurable.** You can:

- **Relax contracts:** Adjust preconditions/postconditions to match actual behavior
- **Shadow mode:** Observe violations without blocking
- **Warn mode:** Log violations but don't raise exceptions
- **Block mode:** Raise exceptions on violations (default)

Start in shadow mode, then tighten as you understand the code better.

---

## Edge Case Discovery

### How does CrossHair discover edge cases?

**CrossHair uses symbolic execution** to explore all possible code paths mathematically. It:

1. Represents inputs symbolically (not concrete values)
2. Explores all feasible execution paths
3. Finds inputs that violate contracts
4. Generates concrete test cases for violations

**Example:**

```python
@icontract.require(lambda numbers: len(numbers) > 0)
@icontract.ensure(lambda numbers, result: min(numbers) > result)
def remove_smallest(numbers: List[int]) -> int:
    smallest = min(numbers)
    numbers.remove(smallest)
    return smallest

# CrossHair finds: [3, 3, 5] violates postcondition
# (duplicates cause min(numbers) == result after removal)
```

### Can CrossHair find all edge cases?

**No tool can find all edge cases**, but CrossHair is more thorough than:

- Manual testing (limited by human imagination)
- Random testing (limited by coverage)
- LLM suggestions (probabilistic, not exhaustive)

CrossHair provides **mathematical guarantees** for explored paths, but complex code may have paths that are computationally infeasible to explore.

### How long does CrossHair take?

**Typically 10-60 seconds per function**, depending on:

- Function complexity
- Number of code paths
- Contract complexity

For large codebases, run CrossHair on critical functions first, then expand.

---

## Modernization Workflow

### How do I start modernizing safely?

**Recommended workflow:**

1. **Extract specs** (`specfact import from-code`)
2. **Add contracts** to 3-5 critical functions
3. **Run CrossHair** to discover edge cases
4. **Refactor incrementally** (one function at a time)
5. **Verify contracts** still pass after refactoring
6. **Expand contracts** to more functions

Start in shadow mode, then enable enforcement as you gain confidence.

### What if I break a contract during refactoring?

**That's the point!** Contracts catch regressions immediately:

```python
# Refactored code violates contract
process_payment(user_id=-1, amount=-50, currency="XYZ")

# Contract violation caught:
# ❌ ContractViolation: Payment amount must be positive (got -50)
#    → Fix the bug before it reaches production!
```

Contracts are your **safety net** - they prevent breaking changes from being deployed.

### Can I use SpecFact with existing test suites?

**Yes.** SpecFact complements existing tests:

- **Tests:** Verify specific scenarios
- **Contracts:** Enforce behavior at API boundaries
- **CrossHair:** Discover edge cases tests miss

Use all three together for comprehensive coverage.

### What's the learning curve for contract-first development?

**Minimal.** SpecFact is designed for incremental adoption:

**Week 1 (2-4 hours):**

- Run `import from-code` to extract specs (10 seconds)
- Review extracted plan bundle
- Add contracts to 3-5 critical functions

**Week 2 (4-6 hours):**

- Expand contracts to 10-15 functions
- Run CrossHair on critical paths
- Set up pre-commit hook

**Week 3+ (ongoing):**

- Add contracts incrementally as you refactor
- Use shadow mode to observe violations
- Enable enforcement when confident

**No upfront training required.** Start with shadow mode (observe only), then enable enforcement incrementally as you understand the code better.

**Resources:**

- [Brownfield Engineer Guide](guides/brownfield-engineer.md) - Complete walkthrough
- [Integration Showcases](../examples/integration-showcases.md) - Real examples
- [Getting Started](../getting-started/README.md) - Quick start guide

---

## Integration

### Does SpecFact work with GitHub Spec-Kit?

**Yes.** SpecFact complements Spec-Kit:

- **Spec-Kit:** Interactive spec authoring (greenfield)
- **SpecFact:** Automated enforcement + brownfield support

**Use both together:**

1. Use Spec-Kit for initial spec generation (fast, LLM-powered)
2. Use SpecFact to add runtime contracts to critical paths (safety net)
3. Spec-Kit generates docs, SpecFact prevents regressions

See [Spec-Kit Comparison Guide](guides/speckit-comparison.md) for details.

### Can I use SpecFact in CI/CD?

**Yes.** SpecFact integrates with:

- **GitHub Actions:** PR annotations, contract validation
- **GitLab CI:** Pipeline integration
- **Jenkins:** Plugin support (planned)
- **Local CI:** Run `specfact enforce` in your pipeline

Contracts can block merges if violations are detected (configurable).

### Does SpecFact work with VS Code, Cursor, or other IDEs?

**Yes.** SpecFact's CLI-first design means it works with **any IDE or editor**:

- **VS Code:** Pre-commit hooks, tasks, or extensions
- **Cursor:** AI assistant integration with contract validation
- **Any editor:** Pure CLI, no IDE lock-in required
- **Agentic workflows:** Works with any AI coding assistant

**Example VS Code integration:**

```bash
# .git/hooks/pre-commit
#!/bin/sh
uvx specfact-cli@latest enforce stage --preset balanced
```

**Example Cursor integration:**

```bash
# Validate AI suggestions before accepting
cursor-agent --validate-with "uvx specfact-cli@latest enforce stage"
```

See [Integration Showcases](../examples/integration-showcases.md) for real examples of bugs caught via different integrations.

### Do I need to learn a new platform?

**No.** SpecFact is **CLI-first**—it integrates into your existing workflow:

- ✅ Works with your current IDE (VS Code, Cursor, etc.)
- ✅ Works with your current CI/CD (GitHub Actions, GitLab, etc.)
- ✅ Works with your current tools (no new platform to learn)
- ✅ Works offline (no cloud account required)
- ✅ Zero vendor lock-in (OSS forever)

**No platform migration needed.** Just add SpecFact CLI to your existing workflow.

---

## Performance

### How fast is code2spec extraction?

**Typically < 10 seconds** for:

- 50-100 Python files
- Standard project structure
- Normal code complexity

Larger codebases may take 30-60 seconds. SpecFact is optimized for speed.

### Does SpecFact require internet?

**No.** SpecFact works 100% offline:

- No cloud services required
- No API keys needed
- No telemetry (opt-in only)
- Fully local execution

Perfect for air-gapped environments or sensitive codebases.

---

## Limitations

### What are SpecFact's limitations?

**Known limitations:**

1. **Python-only** (JavaScript/TypeScript support planned Q1 2026)
2. **Source code required** (not compiled bytecode)
3. **Readable code preferred** (obfuscated code may have lower accuracy)
4. **Complex contracts** may slow CrossHair (timeout configurable)

**What SpecFact does well:**

- ✅ Extracts specs from undocumented code
- ✅ Enforces contracts at runtime
- ✅ Discovers edge cases with symbolic execution
- ✅ Prevents regressions during modernization

---

## Support

### Where can I get help?

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues) - Report bugs
- 📧 [hello@noldai.com](mailto:hello@noldai.com) - Direct support

### Can I contribute?

**Yes!** SpecFact is open source. See [CONTRIBUTING.md](https://github.com/nold-ai/specfact-cli/blob/main/CONTRIBUTING.md) for guidelines.

---

## Next Steps

1. **[Brownfield Engineer Guide](guides/brownfield-engineer.md)** - Complete modernization workflow
2. **[ROI Calculator](guides/brownfield-roi.md)** - Calculate your savings
3. **[Examples](../examples/)** - Real-world brownfield examples

---

**Still have questions?** [Open a discussion](https://github.com/nold-ai/specfact-cli/discussions) or [email us](mailto:hello@noldai.com).
