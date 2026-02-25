#!/bin/bash
#
# Setup Git hooks for contract-first test coverage.
#
# This script sets up pre-commit hooks that use the contract-first test system
# to avoid unnecessary full test runs during development.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Setting up Git hooks for contract-first test coverage...${NC}"

# Ensure we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a Git repository. Please run this from the project root."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy pre-commit hook
if [ -f "scripts/pre-commit-smart-checks.sh" ]; then
    cp scripts/pre-commit-smart-checks.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✅ Pre-commit hook installed${NC}"
else
    echo "❌ Pre-commit hook script not found at scripts/pre-commit-smart-checks.sh"
    exit 1
fi

# Test the contract-first test system
echo -e "${YELLOW}🧪 Testing contract-first test system...${NC}"

if hatch run contract-test-status; then
    echo -e "${GREEN}✅ Contract-first test system is working${NC}"
else
    echo "❌ Contract-first test system test failed"
    exit 1
fi

echo -e "${GREEN}🎉 Git hooks setup complete!${NC}"
echo ""
echo "The pre-commit hook will now:"
echo "  • Verify module signatures and enforce version bumps"
echo "  • Run yamllint for YAML changes (relaxed policy)"
echo "  • Run actionlint for .github/workflows changes"
echo "  • Check for file changes using smart detection"
echo "  • Run contract-first tests when source files change (fast local feedback)"
echo "  • Use cached contract test data when no changes detected"
echo "  • Let GitHub Actions handle full contract test suite validation"
echo "  • Provide fast feedback for developers with contract validation"
echo ""
echo "Manual commands:"
echo "  • Module signatures: hatch run ./scripts/verify-modules-signature.py --require-signature --enforce-version-bump"
echo "  • YAML lint: hatch run yaml-lint"
echo "  • Workflow lint: hatch run lint-workflows"
echo "  • Contract tests: hatch run contract-test"
echo ""
echo "To bypass the hook temporarily: git commit --no-verify"
echo "To run specific contract layers:"
echo "  • Contract validation: hatch run contract-test-contracts"
echo "  • Contract exploration: hatch run contract-test-exploration"
echo "  • Scenario tests: hatch run contract-test-scenarios"
echo "To force a full test run: hatch run contract-test-full"
echo "Legacy smart tests: hatch run smart-test-force"
