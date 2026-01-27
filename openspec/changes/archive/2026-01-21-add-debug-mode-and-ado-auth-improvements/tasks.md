# Tasks: Add Debug Mode and ADO Authentication Improvements

## 1. Global Debug Mode Implementation

- [x] 1.1 Add `_debug_mode` global variable to runtime module
- [x] 1.2 Add `set_debug_mode()` function to enable/disable debug mode
- [x] 1.3 Add `is_debug_mode()` function to check debug mode state
- [x] 1.4 Add `debug_print()` helper function for conditional debug output
- [x] 1.5 Add `--debug` global option to main CLI callback
- [x] 1.6 Update ADO adapter to use `debug_print()` for URL and auth logging
- [x] 1.7 Convert debug console.print statements in init.py to use `debug_print()`

## 2. ADO Adapter Authentication Fixes

- [x] 2.1 Replace manual Authorization header construction with `_auth_headers()` helper in WIQL POST request
- [x] 2.2 Replace manual Authorization header construction with `_auth_headers()` helper in work items batch GET request
- [x] 2.3 Replace manual Authorization header construction with `_auth_headers()` helper in work item PATCH request
- [x] 2.4 Improve error messages for missing API token with helpful guidance
- [x] 2.5 Add debug logging for authentication status (URL, auth header preview)

## 3. ADO Adapter URL Construction Fixes

- [x] 3.1 Ensure org is always included before project in URL path for project-based permissions
- [x] 3.2 Update `_build_ado_url()` to include org even when collection is in base_url
- [x] 3.3 Improve error messages to separate org vs project requirements
- [x] 3.4 Update docstring to clarify org requirement for project-based permissions

## 4. Automatic Token Refresh Implementation

- [x] 4.1 Enable `TokenCachePersistenceOptions` in auth command with shared cache name
- [x] 4.2 Add `_try_refresh_oauth_token()` method to ADO adapter
- [x] 4.3 Implement automatic token refresh when expired OAuth token is detected
- [x] 4.4 Update stored token with refreshed access token
- [x] 4.5 Add helpful error messages when refresh fails

## 5. Personal Access Token (PAT) Support

- [x] 5.1 Add `--pat` option to `auth azure-devops` command
- [x] 5.2 Store PAT with `token_type: "basic"` (no expiration tracking)
- [x] 5.3 Update command documentation to explain PAT vs OAuth options
- [x] 5.4 Add helpful messages about PAT expiration (up to 1 year)

## 6. Testing

- [x] 6.1 Add tests for debug mode functionality (set_debug_mode, is_debug_mode, debug_print)
- [x] 6.2 Add tests for ADO adapter token refresh functionality
- [x] 6.3 Add tests for auth command PAT option
- [x] 6.4 Add tests for _auth_headers method (basic PAT, bearer OAuth, no token)
- [x] 6.5 Update existing tests for org/project requirement changes
- [x] 6.6 Run full test suite and fix any failures

## 7. Code Quality

- [x] 7.1 Run linting and fix any issues
- [x] 7.2 Run formatting and fix any issues
- [x] 7.3 Run type-checking and fix any errors
- [x] 7.4 Ensure all tests pass

## 8. Documentation and OpenSpec

- [x] 8.1 Create OpenSpec change proposal
- [x] 8.2 Validate OpenSpec change proposal
- [x] 8.3 Fix any validation issues
- [x] 8.4 Update CHANGELOG.md with all changes
- [x] 8.5 Update version numbers if needed (version 0.26.3 already set)
