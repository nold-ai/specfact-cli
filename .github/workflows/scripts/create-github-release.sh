#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with release notes from CHANGELOG.md
# Usage: create-github-release.sh <version>
# Requires: GITHUB_TOKEN environment variable

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
# Ensure version has 'v' prefix
if [[ ! $VERSION =~ ^v ]]; then
  VERSION="v${VERSION}"
fi

echo "📝 Generating release notes for $VERSION..."

# Generate release notes from CHANGELOG.md
RELEASE_NOTES=$(./.github/workflows/scripts/generate-release-notes.sh "$VERSION")

if [[ -z "$RELEASE_NOTES" ]]; then
  echo "❌ Failed to generate release notes" >&2
  exit 1
fi

echo "🚀 Creating GitHub release $VERSION..."

# Check if release already exists
if gh release view "$VERSION" &>/dev/null; then
  echo "⚠️ Release $VERSION already exists, skipping creation"
  exit 0
fi

# Create the release
gh release create "$VERSION" \
  --title "$VERSION" \
  --notes "$RELEASE_NOTES" \
  --repo "$GITHUB_REPOSITORY"

echo "✅ Successfully created GitHub release $VERSION"

