# How SpecFact Compares to GitHub Spec-Kit

> **Complementary positioning: When to use Spec-Kit, SpecFact, or both together**

---

## TL;DR: Complementary, Not Competitive

**Spec-Kit excels at:** Documentation, greenfield specs, multi-language support  
**SpecFact excels at:** Runtime enforcement, edge case discovery, high-risk brownfield

**Use both together:**

1. Use Spec-Kit for initial spec generation (fast, LLM-powered)
2. Use SpecFact to add runtime contracts to critical paths (safety net)
3. Spec-Kit generates docs, SpecFact prevents regressions

---

## Quick Comparison

| Capability | GitHub Spec-Kit | SpecFact CLI | When to Choose |
|-----------|----------------|--------------|----------------|
| **Code2spec (brownfield analysis)** | ✅ LLM-generated markdown specs | ✅ AST + contracts extraction | SpecFact for executable contracts |
| **Runtime enforcement** | ❌ No | ✅ icontract + beartype | **SpecFact only** |
| **Symbolic execution** | ❌ No | ✅ CrossHair SMT solver | **SpecFact only** |
| **Edge case discovery** | ⚠️ LLM suggests (probabilistic) | ✅ Mathematical proof (deterministic) | SpecFact for formal guarantees |
| **Regression prevention** | ⚠️ Code review (human) | ✅ Contract violation (automated) | SpecFact for automated safety net |
| **Multi-language** | ✅ 10+ languages | ⚠️ Python (Q1: +JS/TS) | Spec-Kit for multi-language |
| **GitHub integration** | ✅ Native slash commands | ✅ GitHub Actions + CLI | Spec-Kit for native integration |
| **Learning curve** | ✅ Low (markdown + slash commands) | ⚠️ Medium (decorators + contracts) | Spec-Kit for ease of use |
| **High-risk brownfield** | ⚠️ Good documentation | ✅ Formal verification | **SpecFact for high-risk** |
| **Free tier** | ✅ Open-source | ✅ Apache 2.0 | Both free |

---

## Detailed Comparison

### Code Analysis (Brownfield)

**GitHub Spec-Kit:**

- Uses LLM (Copilot) to generate markdown specs from code
- Fast, but probabilistic (may miss details)
- Output: Markdown documentation

**SpecFact CLI:**

- Uses AST analysis + LLM hybrid for precise extraction
- Generates executable contracts, not just documentation
- Output: YAML plans + Python contract decorators

**Winner:** SpecFact for executable contracts, Spec-Kit for quick documentation

### Runtime Enforcement

**GitHub Spec-Kit:**

- ❌ No runtime validation
- Specs are documentation only
- Human review catches violations (if reviewer notices)

**SpecFact CLI:**

- ✅ Runtime contract enforcement (icontract + beartype)
- Contracts catch violations automatically
- Prevents regressions during modernization

**Winner:** SpecFact (core differentiation)

### Edge Case Discovery

**GitHub Spec-Kit:**

- ⚠️ LLM suggests edge cases based on training data
- Probabilistic (may miss edge cases)
- Depends on LLM having seen similar patterns

**SpecFact CLI:**

- ✅ CrossHair symbolic execution
- Mathematical proof of edge cases
- Explores all feasible code paths

**Winner:** SpecFact (formal guarantees)

### Regression Prevention

**GitHub Spec-Kit:**

- ⚠️ Code review catches violations (if reviewer notices)
- Spec-code divergence possible (documentation drift)
- No automated enforcement

**SpecFact CLI:**

- ✅ Contract violations block execution automatically
- Impossible to diverge (contract = executable truth)
- Automated safety net during modernization

**Winner:** SpecFact (automated enforcement)

### Multi-Language Support

**GitHub Spec-Kit:**

- ✅ 10+ languages (Python, JS, TS, Go, Ruby, etc.)
- Native support for multiple ecosystems

**SpecFact CLI:**

- ⚠️ Python only (Q1 2026: +JavaScript/TypeScript)
- Focused on Python brownfield market

**Winner:** Spec-Kit (broader language support)

### GitHub Integration

**GitHub Spec-Kit:**

- ✅ Native slash commands in GitHub
- Integrated with Copilot
- Seamless GitHub workflow

**SpecFact CLI:**

- ✅ GitHub Actions integration
- CLI tool (works with any Git host)
- Not GitHub-specific

**Winner:** Spec-Kit for native GitHub integration, SpecFact for flexibility

---

## When to Use Spec-Kit

### Use Spec-Kit For

- **Greenfield projects** - Starting from scratch with specs
- **Rapid prototyping** - Fast spec generation with LLM
- **Multi-language teams** - Support for 10+ languages
- **Documentation focus** - Want markdown specs, not runtime enforcement
- **GitHub-native workflows** - Already using Copilot, want native integration

### Example Use Case (Spec-Kit)

**Scenario:** Starting a new React + Node.js project

**Why Spec-Kit:**

- Multi-language support (React + Node.js)
- Fast spec generation with Copilot
- Native GitHub integration
- Documentation-focused workflow

---

## When to Use SpecFact

### Use SpecFact For

- **High-risk brownfield modernization** - Finance, healthcare, government
- **Runtime enforcement needed** - Can't afford production bugs
- **Edge case discovery** - Need formal guarantees, not LLM suggestions
- **Contract-first culture** - Already using Design-by-Contract, TDD
- **Python-heavy codebases** - Data engineering, ML pipelines, DevOps

### Example Use Case (SpecFact)

**Scenario:** Modernizing legacy Python payment system

**Why SpecFact:**

- Runtime contract enforcement prevents regressions
- CrossHair discovers hidden edge cases
- Formal guarantees (not probabilistic)
- Safety net during modernization

---

## When to Use Both Together

### ✅ Best of Both Worlds

**Workflow:**

1. **Spec-Kit** generates initial specs (fast, LLM-powered)
2. **SpecFact** adds runtime contracts to critical paths (safety net)
3. **Spec-Kit** maintains documentation (living specs)
4. **SpecFact** prevents regressions (contract enforcement)

### Example Use Case

**Scenario:** Modernizing multi-language codebase (Python backend + React frontend)

**Why Both:**

- **Spec-Kit** for React frontend (multi-language support)
- **SpecFact** for Python backend (runtime enforcement)
- **Spec-Kit** for documentation (markdown specs)
- **SpecFact** for safety net (contract enforcement)

**Integration:**

```bash
# Step 1: Use Spec-Kit for initial spec generation
# (Interactive slash commands in GitHub)

# Step 2: Import Spec-Kit artifacts into SpecFact (via bridge adapter)
specfact import from-bridge --adapter speckit --repo ./my-project

# Step 3: Add runtime contracts to critical Python paths
# (SpecFact contract decorators)

# Step 4: Keep both in sync
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional
```

---

## Competitive Positioning

### Spec-Kit's Strengths

- ✅ **Multi-language support** - 10+ languages
- ✅ **Native GitHub integration** - Slash commands, Copilot
- ✅ **Fast spec generation** - LLM-powered, interactive
- ✅ **Low learning curve** - Markdown + slash commands
- ✅ **Greenfield focus** - Designed for new projects

### SpecFact's Strengths

- ✅ **Runtime enforcement** - Contracts prevent regressions
- ✅ **Symbolic execution** - CrossHair discovers edge cases
- ✅ **Formal guarantees** - Mathematical verification
- ✅ **Brownfield-first** - Designed for legacy code
- ✅ **High-risk focus** - Finance, healthcare, government

### Where They Overlap

- ⚠️ **Low-risk brownfield** - Internal tools, non-critical systems
  - **Spec-Kit:** Fast documentation, good enough
  - **SpecFact:** Slower setup, overkill for low-risk
  - **Winner:** Spec-Kit (convenience > rigor for low-risk)

- ⚠️ **Documentation + enforcement** - Teams want both
  - **Spec-Kit:** Use for specs, add tests manually
  - **SpecFact:** Use for contracts, generate markdown from contracts
  - **Winner:** Depends on team philosophy (docs-first vs. contracts-first)

---

## FAQ

### Can I use Spec-Kit and SpecFact together?

**Yes!** They're complementary:

1. Use Spec-Kit for initial spec generation (fast, LLM-powered)
2. Use SpecFact to add runtime contracts to critical paths (safety net)
3. Keep both in sync with bidirectional sync

### Which should I choose for brownfield projects?

**Depends on risk level:**

- **High-risk** (finance, healthcare, government): **SpecFact** (runtime enforcement)
- **Low-risk** (internal tools, non-critical): **Spec-Kit** (fast documentation)
- **Mixed** (multi-language, some high-risk): **Both** (Spec-Kit for docs, SpecFact for enforcement)

### Does SpecFact replace Spec-Kit?

**No.** They serve different purposes:

- **Spec-Kit:** Documentation, greenfield, multi-language
- **SpecFact:** Runtime enforcement, brownfield, formal guarantees

Use both together for best results.

### Can I migrate from Spec-Kit to SpecFact?

**Yes.** SpecFact can import Spec-Kit artifacts:

```bash
specfact import from-bridge --adapter speckit --repo ./my-project
```

You can also keep using both tools with bidirectional sync.

---

## Decision Matrix

### Choose Spec-Kit If

- ✅ Starting greenfield project
- ✅ Need multi-language support
- ✅ Want fast LLM-powered spec generation
- ✅ Documentation-focused workflow
- ✅ Low-risk brownfield project

### Choose SpecFact If

- ✅ Modernizing high-risk legacy code
- ✅ Need runtime contract enforcement
- ✅ Want formal guarantees (not probabilistic)
- ✅ Python-heavy codebase
- ✅ Contract-first development culture

### Choose Both If

- ✅ Multi-language codebase (some high-risk)
- ✅ Want documentation + enforcement
- ✅ Team uses Spec-Kit, but needs safety net
- ✅ Gradual migration path desired

---

## Next Steps

1. **[Brownfield Engineer Guide](brownfield-engineer.md)** - Complete modernization workflow
2. **[Spec-Kit Journey](speckit-journey.md)** - Migration from Spec-Kit
3. **[Examples](../examples/)** - Real-world examples

---

## Support

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)

---

**Questions?** [Open a discussion](https://github.com/nold-ai/specfact-cli/discussions) or [email us](mailto:hello@noldai.com).
