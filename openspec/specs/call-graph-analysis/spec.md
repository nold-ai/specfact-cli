# call-graph-analysis Specification

## Purpose
TBD - created by archiving change dep-security-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Call-graph extraction via pycg CLI

The system SHALL provide optional call-graph analysis using the `pycg` CLI tool (MIT-licensed). When `pycg` is not installed, the system SHALL degrade gracefully by returning an empty call graph without raising an exception. All code paths involving `pycg` MUST be decorated with `@beartype` and `@icontract` on public-facing methods.

#### Scenario: pycg available — call graph extracted successfully

- **WHEN** `pycg` is available on `$PATH`
- **AND** `graph_analyzer.extract_call_graph(file_path)` is called with a valid Python file
- **THEN** the system SHALL invoke `subprocess.run` with argv equivalent to
  `["pycg", "--package", <repo_root>, str(file_path), "--output", <temp_json_path>]`
  (repository root is the analyzer's `repo_path`)
- **AND** SHALL parse the resulting JSON file using `_parse_pycg_json`
- **AND** SHALL return a `dict[str, list[str]]` mapping **caller** names to lists of **callee** names (PyCG simple JSON adjacency list)
- **AND** SHALL store the result in `self.call_graphs` keyed by relative file path

#### Scenario: pycg not available — graceful degradation

- **WHEN** `pycg` is NOT available on `$PATH`
- **AND** `graph_analyzer.extract_call_graph(file_path)` is called
- **THEN** the system SHALL return an empty dict `{}`
- **AND** SHALL NOT raise any exception

#### Scenario: pycg invocation fails (non-zero exit)

- **WHEN** `pycg` is available but returns a non-zero exit code for a given file
- **THEN** the system SHALL return an empty dict `{}`
- **AND** SHALL NOT propagate the subprocess error to the caller

#### Scenario: JSON output parsed into call graph structure

- **WHEN** `pycg` produces a JSON file with content `{"foo": ["bar", "baz"]}`
- **THEN** `_parse_pycg_json` SHALL return `{"foo": ["bar", "baz"]}` (caller `foo` calls `bar` and `baz`)
- **AND** the result SHALL be a `dict[str, list[str]]`

### Requirement: Optional dep availability check for pycg

The system SHALL expose enhanced-analysis availability via `check_enhanced_analysis_dependencies()` in `optional_deps.py`. That routine SHALL include `pycg` using `check_cli_tool_available("pycg")` and document that **`pycg` is the active call-graph tool**.

#### Scenario: pycg listed in optional deps report

- **WHEN** `check_enhanced_analysis_dependencies()` is called
- **THEN** the returned dict SHALL contain a `"pycg"` key
- **AND** the value SHALL be `(True, None)` when `pycg` is available and the probe succeeds
- **AND** the value SHALL be `(False, <error_message>)` when `pycg` is not available (non-empty installation hint string)

### Requirement: License-clean optional analysis stack

All packages in the `enhanced-analysis` extra SHALL use MIT, Apache-2.0, BSD, or PSF licenses. No GPL or AGPL packages SHALL appear in any distributed extra.

#### Scenario: enhanced-analysis extra contains no GPL packages

- **WHEN** `pip install specfact-cli[enhanced-analysis]` is run
- **THEN** no installed package SHALL carry a GPL-2.0, GPL-3.0, AGPL-3.0, or GPL-2.0-or-later license
- **AND** the call-graph capability SHALL be provided by `pycg` (MIT)

