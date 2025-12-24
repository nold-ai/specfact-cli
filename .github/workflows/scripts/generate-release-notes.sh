#!/usr/bin/env bash
set -euo pipefail

# generate-release-notes.sh
# Extracts release notes from CHANGELOG.md for a given version
# Usage: generate-release-notes.sh <version>
# Outputs release notes to stdout

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
# Remove 'v' prefix if present for CHANGELOG matching
VERSION_NO_V=${VERSION#v}

# Extract the section for this version from CHANGELOG.md
# Look for the version header and extract until the next version header or end of file
python3 << PYTHON_SCRIPT
import re
import sys

version = "$VERSION_NO_V"
changelog_path = "CHANGELOG.md"

try:
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the version section
    # Pattern: ## [version] - date
    pattern = rf'## \[{re.escape(version)}\][^\n]*\n(.*?)(?=\n## \[|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        notes = match.group(1).strip()
        # Remove leading/trailing whitespace and horizontal rules
        notes = re.sub(r'^---\s*$', '', notes, flags=re.MULTILINE)
        notes = notes.strip()
        
        if notes:
            print(notes)
        else:
            print(f"No release notes found for version {version}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Version {version} not found in CHANGELOG.md", file=sys.stderr)
        sys.exit(1)
except FileNotFoundError:
    print(f"Error: {changelog_path} not found", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error extracting release notes: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

