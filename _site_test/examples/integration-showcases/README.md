# Integration Showcases

> **Core USP**: SpecFact CLI works seamlessly with VS Code, Cursor, GitHub Actions, and any agentic workflow. This folder contains real examples of bugs that were caught and fixed through different integration points.

---

## 📚 What's in This Folder

This folder contains everything you need to understand and test SpecFact CLI integrations:

### Main Documents

1. **[`integration-showcases.md`](integration-showcases.md)** ⭐ **START HERE**

   - **Purpose**: Real-world examples of bugs fixed via CLI integrations
   - **Content**: 5 complete examples showing how SpecFact catches bugs in different workflows
   - **Best for**: Understanding what SpecFact can do and seeing real bug fixes
   - **Time**: 15-20 minutes to read

2. **[`integration-showcases-testing-guide.md`](integration-showcases-testing-guide.md)** 🔧 **TESTING GUIDE**

   - **Purpose**: Step-by-step guide to test and validate all 5 examples
   - **Content**: Detailed instructions, expected outputs, validation status
   - **Best for**: Developers who want to verify the examples work as documented
   - **Time**: 2-4 hours to complete all tests

3. **[`integration-showcases-quick-reference.md`](integration-showcases-quick-reference.md)** ⚡ **QUICK REFERENCE**

   - **Purpose**: Quick command reference for all 5 examples
   - **Content**: Essential commands, setup steps, common workflows
   - **Best for**: Quick lookups when you know what you need
   - **Time**: 5 minutes to scan

### Setup Script

1. **[`setup-integration-tests.sh`](setup-integration-tests.sh)** 🚀 **AUTOMATED SETUP**

   - **Purpose**: Automated script to create test cases for all examples
   - **Content**: Creates test directories, sample code, and configuration files
   - **Best for**: Setting up test environment quickly
   - **Time**: < 1 minute to run

---

## 🎯 Quick Start Guide

### For First-Time Users

**Step 1**: Read the main showcase document
→ **[`integration-showcases.md`](integration-showcases.md)**

This gives you a complete overview of what SpecFact can do with real examples.

**Step 2**: Choose your path:

- **Want to test the examples?** → Use [`setup-integration-tests.sh`](setup-integration-tests.sh) then follow [`integration-showcases-testing-guide.md`](integration-showcases-testing-guide.md)

- **Just need quick commands?** → Check [`integration-showcases-quick-reference.md`](integration-showcases-quick-reference.md)

- **Ready to integrate?** → Pick an example from [`integration-showcases.md`](integration-showcases.md) and adapt it to your workflow

### For Developers Testing Examples

**Step 1**: Run the setup script

```bash
./docs/examples/integration-showcases/setup-integration-tests.sh
```

**Step 2**: Follow the testing guide

→ **[`integration-showcases-testing-guide.md`](integration-showcases-testing-guide.md)**

**Step 3**: Verify validation status

- Example 1: ✅ **FULLY VALIDATED**
- Example 2: ✅ **FULLY VALIDATED**
- Example 3: ⚠️ **COMMANDS VERIFIED** (end-to-end testing deferred)
- Example 4: ✅ **FULLY VALIDATED**
- Example 5: ⏳ **PENDING VALIDATION**

---

## 📋 Examples Overview

### Example 1: VS Code Integration - Async Bug Detection

- **Integration**: VS Code + Pre-commit Hook
- **Bug**: Blocking I/O call in async context
- **Result**: Caught before commit, prevented production race condition
- **Status**: ✅ **FULLY VALIDATED**

### Example 2: Cursor Integration - Regression Prevention

- **Integration**: Cursor AI Assistant
- **Bug**: Missing None check in data processing
- **Result**: Prevented regression during refactoring
- **Status**: ✅ **FULLY VALIDATED**

### Example 3: GitHub Actions - CI/CD Integration

- **Integration**: GitHub Actions workflow
- **Bug**: Type mismatch in API endpoint
- **Result**: Blocked bad code from merging
- **Status**: ✅ **FULLY VALIDATED** (CI/CD workflow validated in production)

### Example 4: Pre-commit Hook - Breaking Change Detection

- **Integration**: Git pre-commit hook
- **Bug**: Function signature change (breaking change)
- **Result**: Blocked commit locally before pushing
- **Status**: ✅ **FULLY VALIDATED**

### Example 5: Agentic Workflows - Edge Case Discovery

- **Integration**: AI assistant workflows
- **Bug**: Edge cases in data validation
- **Result**: Discovered hidden bugs with symbolic execution
- **Status**: ⏳ **PENDING VALIDATION**

---

## 🔗 Related Documentation

- **[Examples README](../README.md)** - Overview of all SpecFact examples
- **[Brownfield FAQ](../../guides/brownfield-faq.md)** - Common questions about brownfield modernization
- **[Getting Started](../../getting-started/README.md)** - Installation and setup
- **[Command Reference](../../reference/commands.md)** - All available commands

---

## ✅ Validation Status

**Overall Progress**: 80% complete (4/5 fully validated, 1/5 pending)

**Key Achievements**:

- ✅ CLI-first approach validated (works offline, no account required)
- ✅ 3+ integration case studies showing bugs fixed
- ✅ Enforcement blocking validated across all tested examples
- ✅ Documentation updated with actual command outputs and test results

**Remaining Work**:

- ⏳ Example 5 validation (2-3 hours estimated)
- ✅ Example 3 validated in production CI/CD (GitHub Actions workflow verified)

---

## 💡 Tips

1. **Start with Example 1** - It's the simplest and fully validated

2. **Use the setup script** - Saves time creating test cases

3. **Check validation status** - Examples 1, 2, and 4 are fully tested and working

4. **Read the testing guide** - It has actual command outputs and expected results

5. **Adapt to your workflow** - These examples are templates you can customize

---

**Questions?** Check the [Brownfield FAQ](../../guides/brownfield-faq.md) or open an issue on GitHub.
