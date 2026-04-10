# Change: Add Debug Mode and ADO Authentication Improvements

## Why

Recent improvements to the SpecFact CLI require proper documentation and specification:

1. **Global Debug Output**: Users need a way to see diagnostic information (URLs, authentication status, API details) without cluttering normal output. Currently, debug messages are always shown or hidden, with no user control.

2. **ADO Authentication Issues**:
   - OAuth tokens expire after ~1 hour, requiring frequent re-authentication
   - Missing API tokens in requests due to incorrect Authorization header construction
   - ADO adapter not using centralized authentication helper methods
   - URL construction issues for project-based permissions in larger organizations

3. **Token Management**: Users need options for longer-lived authentication (PATs) and automatic token refresh (like Azure CLI) to avoid frequent re-authentication.

4. **Error Messages**: Error messages for expired tokens and missing authentication need to be more helpful and guide users to solutions.

This change adds global debug mode, improves ADO authentication with automatic token refresh, adds PAT support, fixes authentication header construction, and improves error messages.

## What Changes

- **ADD**: Global `--debug` CLI flag that enables debug output across all commands
- **ADD**: `debug_print()` helper function in runtime module for conditional debug output
- **ADD**: `set_debug_mode()` and `is_debug_mode()` functions for debug state management
- **MODIFY**: ADO adapter to use `_auth_headers()` helper method consistently (replaces manual header construction)
- **MODIFY**: ADO adapter to attempt automatic OAuth token refresh using persistent token cache
- **MODIFY**: ADO adapter URL construction to ensure org is always included before project in URL path
- **MODIFY**: Auth command to support `--pat` option for storing Personal Access Tokens directly
- **MODIFY**: Auth command to enable persistent token cache for automatic token refresh (like Azure CLI)
- **MODIFY**: ADO adapter error messages to provide helpful guidance for expired tokens and missing authentication
- **MODIFY**: Debug console.print statements in init.py to use `debug_print()` helper
- **MODIFY**: ADO adapter debug output (URLs, auth status) to use `debug_print()` helper

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #133
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/133>
- **Last Synced Status**: proposed
- **Sanitized**: true
