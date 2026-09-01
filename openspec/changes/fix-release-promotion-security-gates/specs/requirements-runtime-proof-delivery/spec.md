## ADDED Requirements

### Requirement: Active change selection authenticates archives and Git results

Requirements selection SHALL ignore a moved active change only when Git proves
an exact complete native archive. A Git command failure SHALL be an error, not
evidence that the active source or an extra destination is absent.

#### Scenario: Exact native archive does not compete with the next active change

- **GIVEN** every regular file of one active change moves with identical mode and blob to one correctly dated archive directory
- **AND** no active source or extra archive destination remains
- **WHEN** Requirements selects the changed active plan
- **THEN** it SHALL ignore the completed archive and select the one remaining active change.

#### Scenario: Partial, fabricated, or uncertain archive fails closed

- **WHEN** an archive is partial, copied instead of moved, changes a blob or mode, uses multiple destinations, leaves an active source, adds an extra file, or any required Git enumeration fails
- **THEN** Requirements selection SHALL NOT classify it as a complete archive
- **AND** the gate SHALL report the conflicting or unverifiable change state.

#### Scenario: Ordinary active authoring remains valid

- **WHEN** a contributor deletes a file while other indexed files remain in the same active change or renames a file within that active directory
- **THEN** the pre-commit gate SHALL continue to treat the change as active authoring rather than a completed archive.

### Requirement: Proof execution resolves installed pytest before repository code

The Requirements proof executor SHALL prevent the candidate repository root from
shadowing the installed pytest package while preserving explicit loading of the
repository-owned proof plugin and exact selectors.

#### Scenario: Repository pytest.py cannot replace installed pytest

- **GIVEN** the candidate repository contains a root-level `pytest.py`
- **WHEN** the proof executor starts the selected test process
- **THEN** Python isolated-path mode SHALL import installed pytest first
- **AND** only then SHALL the bootstrap append the repository root and load the explicit proof plugin.

### Requirement: Bootstrap metadata failures retain stable diagnostics

Malformed authority bytes or JSON SHALL be reported as `authority-metadata`;
only explicit comment-contract validation errors SHALL expose an
`authority-comment-*` diagnostic.

#### Scenario: Invalid UTF-8 does not become an arbitrary parser diagnostic

- **WHEN** the bootstrap authority comment contains invalid UTF-8 or malformed JSON
- **THEN** validation SHALL fail with `authority-metadata`
- **AND** it SHALL not reveal arbitrary exception text.

### Requirement: External command path arguments are unambiguous

Repository path operands passed to tools that accept options SHALL follow an
explicit option terminator so a dash-prefixed path cannot alter command meaning.

#### Scenario: Dash-prefixed Markdown path is not an rg option

- **GIVEN** documentation validation receives a Markdown path whose filename begins with `-`
- **WHEN** the validator invokes ripgrep
- **THEN** it SHALL place `--` before every file operand
- **AND** ripgrep SHALL treat the path as data rather than an option.
