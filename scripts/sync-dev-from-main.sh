#!/usr/bin/env bash
# Sync dev branch with latest changes from main branch.
#
# This script:
# 1. Checks out main branch
# 2. Pulls latest changes from origin/main
# 3. Checks out dev branch
# 4. Merges main into dev
# 5. Ensures you're on dev branch ready for new feature branches
#
# OpenSpec / plans: Files under openspec/changes/ (e.g. tasks.md, proposal.md)
# are NOT overwritten by this script itself, but the merge can change them if
# main has different versions. Always commit your dev-only plan edits before
# running. After merge, the script reports any openspec/changes files that were
# modified by the merge so you can review or restore dev's version if needed.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; }

# Ensure we're in a git repository
if [ ! -d ".git" ]; then
    error "Not in a Git repository. Please run this from the project root."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    warn "You have uncommitted changes."
    echo ""
    echo "Please commit or stash your changes before syncing branches."
    echo "Options:"
    echo "  git stash                    # Stash changes temporarily"
    echo "  git commit -am 'message'     # Commit changes"
    echo "  git reset --hard HEAD        # Discard changes (destructive!)"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
info "Current branch: ${CURRENT_BRANCH}"

# Check if main branch exists
if ! git show-ref --verify --quiet refs/heads/main; then
    error "Main branch does not exist locally."
    exit 1
fi

# Check if dev branch exists
if ! git show-ref --verify --quiet refs/heads/dev; then
    warn "Dev branch does not exist locally. Creating it from main..."
    git checkout -b dev main
    success "Created dev branch from main"
    exit 0
fi

# Fetch latest changes from remote
info "Fetching latest changes from remote..."
git fetch origin

# Checkout main branch
info "Checking out main branch..."
git checkout main

# Pull latest changes from origin/main
info "Pulling latest changes from origin/main..."
if git pull origin main; then
    success "Main branch is up to date"
else
    error "Failed to pull from origin/main"
    exit 1
fi

# Checkout dev branch
info "Checking out dev branch..."
git checkout dev

# Merge main into dev
info "Merging main into dev..."
if git merge main --no-edit; then
    success "Successfully merged main into dev"
    # Report any openspec/changes files modified by the merge only when a merge commit was created.
    # When already up to date, Git does not create a merge commit; diffing HEAD^1..HEAD would then
    # compare dev to its single parent and falsely report dev's own openspec changes as merge changes.
    if git rev-parse --verify HEAD^2 >/dev/null 2>&1; then
        CHANGED_OPENSPEC=$(git diff --name-only HEAD^1..HEAD -- "openspec/changes/" 2>/dev/null || true)
        if [ -n "$CHANGED_OPENSPEC" ]; then
            warn "The following openspec/changes files were modified by the merge (main's version was merged in):"
            echo "$CHANGED_OPENSPEC" | sed 's/^/  /'
            echo ""
            echo "Review the changes. To restore dev's version of a file (before merge):"
            echo "  git checkout HEAD^1 -- <file>"
            echo ""
        fi
    fi
else
    error "Merge conflict detected!"
    echo ""
    echo "Please resolve the conflicts manually:"
    echo "  1. Review conflicts: git status"
    echo "  2. Resolve conflicts in the affected files"
    echo "  3. Stage resolved files: git add <files>"
    echo "  4. Complete merge: git commit"
    echo ""
    echo "Or abort the merge: git merge --abort"
    exit 1
fi

# Verify we're on dev branch
FINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$FINAL_BRANCH" = "dev" ]; then
    success "You are now on dev branch, ready for new feature branches"
    echo ""
    echo "Next steps:"
    echo "  git checkout -b feature/your-feature-name"
    echo "  git checkout -b bugfix/your-bugfix-name"
    echo "  git checkout -b hotfix/your-hotfix-name"
else
    warn "Expected to be on dev branch, but currently on: ${FINAL_BRANCH}"
fi
