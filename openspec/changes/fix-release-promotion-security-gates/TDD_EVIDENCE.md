# TDD Evidence

Change: `fix-release-promotion-security-gates`

Baseline: `origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c`

## Failing before

Timestamp: 2026-09-02 00:17:45 Europe/Berlin

Environment: macOS arm64, Python 3.13.14, pytest 9.1.1. The interpreter came
from the existing repository-frozen environment; the clean replay worktree had
no synchronized environment yet. Production files remained identical to
`origin/dev` apart from the OpenSpec-native archive of already-completed #689.

Command:

```text
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest \
  tests/unit/security/test_release_promotion_security_gates.py -q
```

Result: expected failure, exit 1; 11 collected, 11 failed. Each scenario failed
at its intended pre-fix observation: uv cache enabled; manual dispatch present;
npm cache present; Semgrep/MCP old graph and waiver; Code Review lock unbound;
Pylint exception leaked; archive Git results unchecked; `python -m pytest`
shadowable; invalid UTF-8 diagnostic leaked; `rg` lacked `--`; version remained
0.55.3.

## Passing after

Pending implementation and final verification.
