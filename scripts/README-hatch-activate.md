# Hatch Virtual Environment Activation with Git Branch

This directory contains scripts to enhance your hatch virtual environment activation by showing the current git branch in your shell prompt.

## Quick Start

### Option 1: Direct Source (Recommended)

From the project root directory:

```bash
source scripts/hatch-activate-with-branch.sh
```

### Option 2: Add to Shell Config

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
# Hatch venv activation with git branch
source /home/dom/git/nold-ai/specfact-cli/scripts/hatch-prompt-function.sh
```

Then use the function from any hatch project:

```bash
hatch-activate
```

### Option 3: Create an Alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias hatch-activate='source /home/dom/git/nold-ai/specfact-cli/scripts/hatch-activate-with-branch.sh'
```

Then use:

```bash
hatch-activate
```

## Features

- ✅ **Automatic venv detection**: Uses `hatch env find` to locate the virtual environment
- ✅ **Git branch display**: Shows current branch in prompt (with `*` if uncommitted changes)
- ✅ **Works with any hatch project**: Not limited to specfact-cli
- ✅ **Bash and Zsh support**: Works with both shell types
- ✅ **Safe activation**: Checks for hatch and venv before activating

## Prompt Format

The prompt will show:

```
(venv-name) user@host:~/path/to/project (branch-name) $
```

If there are uncommitted changes:

```
(venv-name) user@host:~/path/to/project (branch-name *) $
```

## Troubleshooting

### "hatch command not found"

Install hatch:

```bash
pip install hatch
# or
pipx install hatch
```

### "Could not find hatch virtual environment"

Create the environment:

```bash
hatch env create
```

### Script not found

Make sure you're running from the project root, or use the full path:

```bash
source /home/dom/git/nold-ai/specfact-cli/scripts/hatch-activate-with-branch.sh
```

## How It Works

1. The script uses `hatch env find` to locate the virtual environment path
2. Sources the standard `bin/activate` script
3. Modifies `PS1` (bash) or uses `precmd` hooks (zsh) to add git branch info
4. Updates the prompt dynamically as you navigate

## Compatibility

- ✅ Bash 4.0+
- ✅ Zsh 5.0+
- ✅ Hatch 1.0+
- ✅ Works with any hatch-managed project
