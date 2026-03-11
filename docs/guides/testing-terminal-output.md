---
layout: default
title: Testing Terminal Output Modes
permalink: /testing-terminal-output/
---

# Testing Terminal Output Modes

This guide explains how to test SpecFact CLI's terminal output auto-detection on Ubuntu/GNOME systems.

## Quick Test Methods

### Method 1: Use NO_COLOR (Easiest)

The `NO_COLOR` environment variable is the standard way to disable colors:

```bash
# Test in current terminal session
NO_COLOR=1 specfact --help

# Or export for the entire session
export NO_COLOR=1
specfact code import my-bundle
unset NO_COLOR  # Re-enable colors
```

### Method 2: Simulate CI/CD Environment

Simulate a CI/CD pipeline (BASIC mode):

```bash
# Set CI environment variable
CI=true specfact --help

# Or simulate GitHub Actions
GITHUB_ACTIONS=true specfact code import my-bundle
```

### Method 3: Use Dumb Terminal Type

Force a "dumb" terminal that doesn't support colors:

```bash
# Start a terminal with dumb TERM
TERM=dumb specfact --help

# Or use vt100 (minimal terminal)
TERM=vt100 specfact --help
```

### Method 4: Redirect to Non-TTY

Redirect output to a file or pipe (non-interactive):

```bash
# Redirect to file (non-TTY)
specfact --help > output.txt 2>&1
cat output.txt

# Pipe to another command (non-TTY)
specfact --help | cat
```

### Method 5: Use script Command

The `script` command can create a non-interactive session:

```bash
# Create a script session (records to typescript file)
script -c "specfact --help" output.txt

# Or use script with dumb terminal
TERM=dumb script -c "specfact --help" output.txt
```

## Testing in GNOME Terminal

### Option A: Launch Terminal with NO_COLOR

```bash
# Launch gnome-terminal with NO_COLOR set
gnome-terminal -- bash -c "export NO_COLOR=1; specfact --help; exec bash"
```

### Option B: Create a Test Script

Create a test script `test-no-color.sh`:

```bash
#!/bin/bash
export NO_COLOR=1
specfact --help
```

Then run:

```bash
chmod +x test-no-color.sh
./test-no-color.sh
```

### Option C: Use Different Terminal Emulators

Install and test with different terminal emulators:

```bash
# Install alternative terminals
sudo apt install xterm terminator

# Test with xterm (can be configured for minimal support)
xterm -e "NO_COLOR=1 specfact --help"

# Test with terminator
terminator -e "NO_COLOR=1 specfact --help"
```

## Verifying Terminal Mode Detection

You can verify which mode is detected:

```bash
# Check detected terminal mode
python3 -c "from specfact_cli.runtime import get_terminal_mode; print(get_terminal_mode())"

# Check terminal capabilities
python3 -c "
from specfact_cli.utils.terminal import detect_terminal_capabilities
caps = detect_terminal_capabilities()
print(f'Color: {caps.supports_color}')
print(f'Animations: {caps.supports_animations}')
print(f'Interactive: {caps.is_interactive}')
print(f'CI: {caps.is_ci}')
"
```

## Expected Behavior

### GRAPHICAL Mode (Default in Full Terminal)

- ✅ Colors enabled
- ✅ Animations enabled
- ✅ Full progress bars
- ✅ Rich formatting

### BASIC Mode (NO_COLOR or CI/CD)

- ❌ No colors
- ❌ No animations
- ✅ Plain text progress updates
- ✅ Readable output

### MINIMAL Mode (TEST_MODE)

- ❌ No colors
- ❌ No animations
- ❌ Minimal output
- ✅ Test-friendly

## Complete Test Workflow

```bash
# 1. Test with colors (default)
specfact --help

# 2. Test without colors (NO_COLOR)
NO_COLOR=1 specfact --help

# 3. Test CI/CD mode
CI=true specfact --help

# 4. Test minimal mode
TEST_MODE=true specfact --help

# 5. Verify detection
python3 -c "from specfact_cli.runtime import get_terminal_mode; print(get_terminal_mode())"
```

## Troubleshooting

If terminal detection isn't working as expected:

1. **Check environment variables**:

   ```bash
   echo "NO_COLOR: $NO_COLOR"
   echo "FORCE_COLOR: $FORCE_COLOR"
   echo "TERM: $TERM"
   echo "CI: $CI"
   ```

2. **Verify TTY status**:

   ```bash
   python3 -c "import sys; print('Is TTY:', sys.stdout.isatty())"
   ```

3. **Check terminal capabilities**:

   ```bash
   python3 -c "
   from specfact_cli.utils.terminal import detect_terminal_capabilities
   import json
   caps = detect_terminal_capabilities()
   print(json.dumps({
       'supports_color': caps.supports_color,
       'supports_animations': caps.supports_animations,
       'is_interactive': caps.is_interactive,
       'is_ci': caps.is_ci
   }, indent=2))
   "
   ```

## Related Documentation

- [Troubleshooting](troubleshooting.md#terminal-output-issues) - Terminal output issues and auto-detection
- [UX Features](ux-features.md) - User experience features including terminal output
