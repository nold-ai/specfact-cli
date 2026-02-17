#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_NAME="worktree.sh"
readonly ALLOWED_TYPES="feature/*, bugfix/*, hotfix/*, chore/*"

WORKTREE_ROOT="${WORKTREE_ROOT:-../specfact-cli-worktrees}"
BASE_REF="${BASE_REF:-origin/dev}"
DRY_RUN="${WORKTREE_DRY_RUN:-0}"

print_usage() {
  cat <<USAGE
Usage:
  scripts/worktree.sh create <type>/<slug>
  scripts/worktree.sh list
  scripts/worktree.sh cleanup <type>/<slug>
  scripts/worktree.sh help

Allowed branch types: ${ALLOWED_TYPES}
Protected branches (blocked for worktrees): dev, main

Environment overrides:
  WORKTREE_ROOT   Override default root (default: ../specfact-cli-worktrees)
  BASE_REF        Base ref for create (default: origin/dev)
  WORKTREE_DRY_RUN=1  Print commands without executing
USAGE
}

err() {
  printf 'Error: %s\n' "$*" >&2
}

info() {
  printf '%s\n' "$*"
}

run_cmd() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '+ %s\n' "$*"
    return 0
  fi
  "$@"
}

ensure_repo_if_needed() {
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    err "must be run from inside a git repository"
    exit 1
  fi
}

validate_branch() {
  local branch="$1"

  if [[ "$branch" == "dev" || "$branch" == "main" ]]; then
    err "protected branch '$branch' is not allowed in worktrees"
    exit 1
  fi

  if [[ ! "$branch" =~ ^(feature|bugfix|hotfix|chore)/[A-Za-z0-9._-]+$ ]]; then
    err "unsupported branch '$branch'; allowed branch types: ${ALLOWED_TYPES}"
    exit 1
  fi
}

branch_type() {
  local branch="$1"
  printf '%s\n' "${branch%%/*}"
}

branch_slug() {
  local branch="$1"
  printf '%s\n' "${branch#*/}"
}

worktree_path_for() {
  local branch="$1"
  local type slug
  type="$(branch_type "$branch")"
  slug="$(branch_slug "$branch")"
  printf '%s/%s/%s\n' "$WORKTREE_ROOT" "$type" "$slug"
}

resolve_base_ref() {
  local resolved="$BASE_REF"

  if [[ "$DRY_RUN" == "1" ]]; then
    printf '%s\n' "$resolved"
    return 0
  fi

  if git rev-parse --verify --quiet "${resolved}^{commit}" >/dev/null; then
    printf '%s\n' "$resolved"
    return 0
  fi

  err "base ref '${resolved}' is not available after fetch; set BASE_REF to a valid ref"
  exit 1
}

fetch_origin_if_present() {
  if [[ "$DRY_RUN" == "1" ]]; then
    run_cmd git fetch origin
    return 0
  fi

  if git remote get-url origin >/dev/null 2>&1; then
    run_cmd git fetch origin
  else
    info "No origin remote configured; skipping fetch."
  fi
}

cmd_create() {
  local branch="$1"
  local path base

  validate_branch "$branch"
  ensure_repo_if_needed

  path="$(worktree_path_for "$branch")"

  run_cmd mkdir -p "$(dirname "$path")"
  fetch_origin_if_present
  base="$(resolve_base_ref)"

  info "Target worktree path: ${path}"
  info "Base ref: ${base}"
  run_cmd git worktree add "$path" -b "$branch" "$base"

  info "Worktree ready: ${path}"
}

cmd_list() {
  ensure_repo_if_needed
  run_cmd git worktree list
}

cmd_cleanup() {
  local branch="$1"
  local path

  validate_branch "$branch"
  ensure_repo_if_needed

  path="$(worktree_path_for "$branch")"
  info "Cleanup target: ${path}"

  run_cmd git worktree remove "$path"
  run_cmd git branch -d "$branch"
  run_cmd git worktree prune

  info "Cleanup complete for branch: ${branch}"
}

main() {
  local command="${1:-help}"

  case "$command" in
    create)
      if [[ $# -ne 2 ]]; then
        err "create requires a branch argument"
        print_usage
        exit 1
      fi
      cmd_create "$2"
      ;;
    list)
      if [[ $# -ne 1 ]]; then
        err "list takes no additional arguments"
        print_usage
        exit 1
      fi
      cmd_list
      ;;
    cleanup)
      if [[ $# -ne 2 ]]; then
        err "cleanup requires a branch argument"
        print_usage
        exit 1
      fi
      cmd_cleanup "$2"
      ;;
    help|-h|--help)
      print_usage
      ;;
    *)
      err "unknown command: ${command}"
      print_usage
      exit 1
      ;;
  esac
}

main "$@"
