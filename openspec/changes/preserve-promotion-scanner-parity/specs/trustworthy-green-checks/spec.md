## ADDED Requirements

### Requirement: The promotion preserves reviewed async callable bindings

The signed release source SHALL retain the reviewed async scanner's lexical
binding behavior when reconciling current development with protected `main`.

#### Scenario: The promotion preserves reviewed async callable bindings

- **GIVEN** the source scanner reads an async function with a locally assigned synchronous callable
- **WHEN** the scanner reports on that call and on a separate unawaited coroutine
- **THEN** only the coroutine call receives a missing-await finding.
