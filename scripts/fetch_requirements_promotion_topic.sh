#!/usr/bin/env bash
# Fetch provider metadata for a signed topic. The caller installs this script from main.
set -euo pipefail

metadata_root="$1"
topic_ref="$2"
topic_sha="$3"
repo=nold-ai/specfact-cli

[[ "$topic_ref" =~ ^codex/promotion-from-dev-pr-([1-9][0-9]{0,8})$ ]]
source_number="${BASH_REMATCH[1]}"
[[ "$topic_sha" =~ ^[0-9a-f]{40}$ ]]
test "${GITHUB_REPOSITORY:-}" = "$repo"
origin="$(git remote get-url origin)"
[[ "$origin" == "https://github.com/$repo" || "$origin" == "https://github.com/$repo.git" ]]

gh api "repos/$repo/pulls/$source_number" > "$metadata_root/source-pull.json"
jq -e '[.]' "$metadata_root/source-pull.json" > "$metadata_root/source-pulls.json"
source_sha="$(jq -er '.head.sha | select(type == "string" and test("^[0-9a-f]{40}$"))' "$metadata_root/source-pull.json")"
git fetch --no-tags origin \
  "+refs/heads/$topic_ref:refs/remotes/origin/$topic_ref" \
  "+refs/pull/$source_number/head:refs/remotes/origin/requirements-promotion-source"
test "$(git rev-parse "refs/remotes/origin/$topic_ref^{commit}")" = "$topic_sha"
test "$(git rev-parse 'refs/remotes/origin/requirements-promotion-source^{commit}')" = "$source_sha"
gh api "repos/$repo/git/commits/$topic_sha" > "$metadata_root/topic-commit.json"
gh api "repos/$repo/git/commits/$source_sha" > "$metadata_root/source-commit.json"
jq -en --slurpfile head "$metadata_root/topic-commit.json" \
  --slurpfile source "$metadata_root/source-commit.json" '{head:$head[0],source:$source[0]}' > "$metadata_root/topic-commits.json"
printf '%s\n' "$source_sha"
