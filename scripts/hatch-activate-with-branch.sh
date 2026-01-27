#!/usr/bin/env bash
# Activate hatch virtual environment with git branch in prompt.
#
# This script:
# 1. Finds the hatch virtual environment using 'hatch env find'
# 2. Activates the virtual environment
# 3. Modifies PS1 to show the current git branch
# 4. Works for any hatch project, not just specfact-cli
#
# Usage:
#   source scripts/hatch-activate-with-branch.sh
#   # or add to your .bashrc/.zshrc:
#   alias hatch-activate='source /path/to/scripts/hatch-activate-with-branch.sh'

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || {
    echo "Error: Could not change to project root: $PROJECT_ROOT" >&2
    return 1 2>/dev/null || exit 1
}

# Check if hatch is available
if ! command -v hatch >/dev/null 2>&1; then
    echo "Error: hatch command not found. Please install hatch first." >&2
    return 1 2>/dev/null || exit 1
fi

# Find the hatch virtual environment
VENV_PATH=$(hatch env find 2>/dev/null)

if [ -z "$VENV_PATH" ] || [ ! -d "$VENV_PATH" ]; then
    echo "Error: Could not find hatch virtual environment." >&2
    echo "Try running: hatch env create" >&2
    return 1 2>/dev/null || exit 1
fi

# Check if activate script exists
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "Error: Virtual environment activate script not found: $ACTIVATE_SCRIPT" >&2
    return 1 2>/dev/null || exit 1
fi

# Function to get git branch for prompt
_get_git_branch() {
    local branch
    if branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); then
        # Check if there are uncommitted changes
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo " ($branch *)"
        else
            echo " ($branch)"
        fi
    else
        echo ""
    fi
}

# Store original PS1 if not already stored
if [ -z "$_ORIGINAL_PS1" ]; then
    _ORIGINAL_PS1="$PS1"
fi

# Activate the virtual environment
source "$ACTIVATE_SCRIPT"

# Modify PS1 to include git branch
# Detect shell type
if [ -n "$ZSH_VERSION" ]; then
    # Zsh
    _update_prompt() {
        local git_branch=$(_get_git_branch)
        PS1="${VIRTUAL_ENV:+(${VIRTUAL_ENV##*/}) }%n@%m:%~${git_branch}%# "
    }
    # Set up precmd hook for zsh
    precmd_functions+=(_update_prompt)
    _update_prompt
elif [ -n "$BASH_VERSION" ]; then
    # Bash
    _update_prompt() {
        local git_branch=$(_get_git_branch)
        PS1="${VIRTUAL_ENV:+(${VIRTUAL_ENV##*/}) }\u@\h:\w${git_branch}\$ "
    }
    # Update prompt immediately and set up PROMPT_COMMAND
    # Preserve existing PROMPT_COMMAND if it exists
    if [ -n "$PROMPT_COMMAND" ]; then
        PROMPT_COMMAND="_update_prompt; $PROMPT_COMMAND"
    else
        PROMPT_COMMAND="_update_prompt"
    fi
    _update_prompt
else
    # Fallback for other shells
    echo "Warning: Shell type not recognized. Git branch may not appear in prompt." >&2
fi

echo "✅ Hatch virtual environment activated: ${VENV_PATH##*/}"
echo "📁 Project: $(basename "$PROJECT_ROOT")"
if git rev-parse --git-dir >/dev/null 2>&1; then
    echo "🌿 Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
fi
