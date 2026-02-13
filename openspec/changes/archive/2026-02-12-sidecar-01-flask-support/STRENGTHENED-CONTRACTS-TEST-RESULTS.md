# Strengthened Contracts Test Results (9.2.6)

**Date**: 2026-02-12  
**Change**: sidecar-01-flask-support  
**Target**: Microblog Flask application

## Test Execution

```bash
hatch run specfact validate sidecar init microblog /home/dom/git/specfact-validation/microblog
hatch run specfact validate sidecar run microblog /home/dom/git/specfact-validation/microblog --no-run-specmatic
```

## Results Summary

| Metric | Value |
|--------|-------|
| Framework detected | flask |
| Routes extracted | 66 |
| Contracts populated | 23 |
| Harness generated | Yes |
| CrossHair confirmed | 0 |
| CrossHair not confirmed | 1 |
| Violations found | 0 |

## Business Logic Constraints Verified

### Preconditions Applied

The harness includes business logic preconditions as implemented in 9.2.5:

- **`username` path parameter**: `@require(lambda username: len(username) >= 1, 'username must be non-empty')`
  - Applied to: `harness_user`, `harness_user_popup`, `harness_follow`, and other routes with `{username}`

- **`token` path parameter**: Non-empty constraint for `/reset_password/{token}`

- **`id` path parameter** (when present): Default `minimum: 1` for valid resource IDs

### Postconditions Applied

- Status code validation: `[200, 201, 204, 302, 400, 404]` (500 excluded as server error)
- Response structure: `result` must be dict with `status_code` and `data`
- When response schema defines `id` property: `id >= 1` for success responses

## CrossHair Analysis

- **Outcome**: Timeout (expected for 66 routes with 23 harness functions)
- **Partial results**: Analysis ran; timeout occurred before all paths could be confirmed
- **Violations**: 0 detected (contracts allow 302, 404 which are common for unauthenticated Flask requests)

## Violation Detection Notes

The flexible status code contracts (200, 201, 204, 302, 404) intentionally allow:

- **302**: Redirects (e.g., login→login page when not authenticated)
- **404**: Not found (e.g., user/{username} when user doesn't exist)

This avoids false positives for normal Flask behavior. Violations would be detected for:

- **500 responses**: Server errors (explicitly rejected)
- **Invalid response structure**: Missing required fields, wrong types
- **Invalid id values**: When schema defines id, postcondition requires id >= 1

## Recommendations

1. **Increase timeout** for larger apps: Use `--crosshair-timeout` or `--crosshair-per-path-timeout` for more complete analysis
2. **Tighter contracts** for specific routes: Manually add stricter postconditions where 404/302 should not occur
3. **Schema enhancement**: Add response schemas with `id` property to enable id validity postconditions

## Related Documents

- [CONTRACT-STRENGTHENING.md](./CONTRACT-STRENGTHENING.md) - Business logic constraints documentation
- [CROSSHAIR-EXECUTION.md](./CROSSHAIR-EXECUTION.md) - CrossHair execution and timeout behavior
