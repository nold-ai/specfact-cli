## ADDED Requirements

### Requirement: Call-graph extraction via pycg CLI

The system SHALL provide optional call-graph analysis using the `pycg` CLI tool (MIT-licensed). When `pycg` is not installed, the system SHALL degrade gracefully by returning an empty call graph without raising an exception. All code paths involving `pycg` MUST be decorated with `@beartype` and `@icontract` on public-facing methods.

#### Scenario: pycg available — call graph extracted successfully

- **WHEN** `pycg` is available on `$PATH`
- **AND** `graph_analyzer.extract_call_graph(file_path)` is called with a valid Python file
- **THEN** the system SHALL invoke `subprocess.run(["pycg", str(file_path), "--output", tmp_json_path])`
- **AND** SHALL parse the resulting JSON file using `_parse_pycg_json`
- **AND** SHALL return a `dict[str, list[str]]` mapping callee names to lists of caller names
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
- **THEN** `_parse_pycg_json` SHALL return `{"foo": ["bar", "baz"]}`
- **AND** the result SHALL be a `dict[str, list[str]]`

### Requirement: Optional dep availability check for pycg

The system SHALL expose a `pycg` availability check via `check_optional_analysis_deps()` in `optional_deps.py`. The check SHALL use `check_cli_tool_available("pycg")` and document that `pycg` is the active call-graph tool.

#### Scenario: pycg listed in optional deps report

- **WHEN** `check_optional_analysis_deps()` is called
- **THEN** the returned dict SHALL contain a `"pycg"` key
- **AND** the value SHALL be `(True, path_string)` if `pycg` is on `$PATH`
- **AND** the value SHALL be `(False, None)` if `pycg` is not on `$PATH`

### Requirement: License-clean optional analysis stack

All packages in the `enhanced-analysis` extra SHALL use MIT, Apache-2.0, BSD, or PSF licenses. No GPL or AGPL packages SHALL appear in any distributed extra.

#### Scenario: enhanced-analysis extra contains no GPL packages

- **WHEN** `pip install specfact-cli[enhanced-analysis]` is run
- **THEN** no installed package SHALL carry a GPL-2.0, GPL-3.0, AGPL-3.0, or GPL-2.0-or-later license
- **AND** the call-graph capability SHALL be provided by `pycg` (MIT)

## REMOVED Requirements

### Requirement: Call-graph extraction via pyan3 CLI

**Reason:** `pyan3` is licensed GPL-2.0, incompatible with specfact-cli's Apache-2.0 license and blocking future enterprise/commercial licensing. `pyan3` has also had no active releases since 2022.

**Migration:** Replace `pyan3` with `pycg` (`pip install pycg`). The CLI interface changes from `pyan3 <file> --dot` to `pycg <file> --output out.json`. Output format changes from DOT to JSON; internal parser updated accordingly. All public API contracts are preserved.
