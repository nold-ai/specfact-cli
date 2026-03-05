# TDD Evidence: backlog-core-07-ado-required-custom-fields-and-picklists

## Red Phase (Failing Before Implementation)

- **Timestamp (UTC)**: 2026-03-05T14:34:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-modules-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=/home/dom/git/nold-ai/specfact-cli/src:$PYTHONPATH python -m pytest tests/unit/specfact_backlog/test_map_fields_command.py -q`
- **Expected Result**: Failing tests (new behavior not implemented yet)
- **Observed Failure Summary**:
  - `No such option: --non-interactive`
  - Assertion expecting interactive fallback guidance could not pass because CLI option was missing.

## Green Phase (Passing After Implementation)

- **Timestamp (UTC)**: 2026-03-05T14:41:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-modules-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=/home/dom/git/nold-ai/specfact-cli/src:$PYTHONPATH python -m pytest tests/unit/specfact_backlog/test_map_fields_command.py -q`
- **Observed Result**:
  - `2 passed`
- **Passing Scope**:
  - Non-interactive `map-fields` auto-maps and persists required/allowed-values metadata.
  - Non-interactive `map-fields` fails with explicit guidance when required fields cannot be resolved.

## Green Phase Extensions (Passing Verification After Picklist API Improvement)

- **Timestamp (UTC)**: 2026-03-05T15:13:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-modules-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=packages/specfact-backlog/src:/home/dom/git/nold-ai/specfact-cli/src python -m pytest tests/unit/specfact_backlog/test_map_fields_command.py -q`
- **Observed Result**:
  - `2 passed`
- **Passing Scope**:
  - Picklist values are resolved through ADO lists API (`/_apis/work/processes/lists/{picklistId}`) when field-level `allowedValues` is empty.
  - Required metadata and allowed-values metadata persist in `.specfact/backlog-config.yaml` for the selected work item type.

## Runtime Reality Checks (Live ADO Demo Project)

- **Timestamp (UTC)**: 2026-03-05T15:14:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-modules-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=packages/specfact-backlog/src:/home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists/src python - <<'PY' ... map-fields --provider ado --ado-org noldai --ado-project specfact-cli --ado-framework scrum --non-interactive ... PY`
- **Observed Result**:
  - Exit `0`; provider settings now include required custom fields and live allowed-values lists for `Custom.Category` and `Custom.SubCategory`.

- **Timestamp (UTC)**: 2026-03-05T15:16:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=modules/backlog-core/src:src python - <<'PY' ... backlog add --adapter ado --project-id noldai/specfact-cli --type story --custom-field category=Architecture --custom-field subcategory='Runtime validation' --non-interactive ... PY`
- **Observed Result**:
  - Exit `0`; item successfully created in ADO (`id: 4`).

- **Timestamp (UTC)**: 2026-03-05T15:17:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=modules/backlog-core/src:src python - <<'PY' ... backlog add --adapter ado --project-id noldai/specfact-cli --type story --custom-field category=Business --custom-field subcategory='Runtime validation' --non-interactive ... PY`
- **Observed Result**:
  - Exit `1`; client-side validation rejects invalid picklist value and prints allowed options before adapter submit.

## Markdown Default and Normalization Verification

- **Timestamp (UTC)**: 2026-03-05T15:22:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=modules/backlog-core/src:src python -m pytest modules/backlog-core/tests/unit/test_adapter_create_issue.py -q -k "defaults_text_fields_to_markdown or normalizes_html_text_to_markdown"`
- **Observed Result**:
  - `2 passed`
- **Passing Scope**:
  - ADO create defaults multiline field rendering to `Markdown` when no classic override is supplied.
  - html-like description and acceptance criteria inputs are normalized to markdown before create submit.

- **Timestamp (UTC)**: 2026-03-05T15:23:00Z
- **Command**:
  - `cd /home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/backlog-core-07-ado-required-custom-fields-and-picklists && PYTHONPATH=modules/backlog-core/src:src python - <<'PY' ... backlog add with html body/ac ... read back created work item fields ... PY`
- **Observed Result**:
  - Exit `0`; created work item `id: 5`.
  - Readback confirms normalized markdown-style content persisted:
    - `System.Description`: `Hello **markdown**`
    - `Microsoft.VSTS.Common.AcceptanceCriteria`: `- Given A- When B`
