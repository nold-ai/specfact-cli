#!/usr/bin/env bash
# Bash/Zsh function to activate hatch venv with git branch in prompt.
#
# Add this to your ~/.bashrc or ~/.zshrc:
#
#   source /path/to/specfact-cli/scripts/hatch-prompt-function.sh
#
# Then use: hatch-activate
#
# Or create an alias in your shell config:
#   alias hatch-activate='source /path/to/specfact-cli/scripts/hatch-activate-with-branch.sh'

hatch-activate() {
    local script_dir
    # Try to find the script relative to current directory
    if [ -f "scripts/hatch-activate-with-branch.sh" ]; then
        script_dir="$(pwd)/scripts/hatch-activate-with-branch.sh"
    elif [ -f "$HOME/git/nold-ai/specfact-cli/scripts/hatch-activate-with-branch.sh" ]; then
        script_dir="$HOME/git/nold-ai/specfact-cli/scripts/hatch-activate-with-branch.sh"
    else
        echo "Error: Could not find hatch-activate-with-branch.sh" >&2
        echo "Please run this from a hatch project directory or set HATCH_ACTIVATE_SCRIPT path." >&2
        return 1
    fi
    
    source "$script_dir"
}

# Function to get git branch (can be used standalone)
_get_git_branch() {
    local branch
    if branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); then
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo " ($branch *)"
        else
            echo " ($branch)"
        fi
    else
        echo ""
    fi
}
