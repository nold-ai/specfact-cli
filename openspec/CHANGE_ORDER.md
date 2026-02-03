# OpenSpec change order by command and implementation dependency

Changes are grouped by **main CLI command** and prefixed with **command-NN-** (double-digit order) so implementation order is explicit. Implement **01** before **02** within each command; cross-command dependencies are listed under "Blocked by" below.

## Naming convention

- **Folder**: `<command>-<NN>-<suffix>` (e.g. `backlog-01-add-backlog-dependency-analysis-and-commands`).
- **Order**: 01, 02, … within the command group; lower numbers are implemented first where dependencies require it.

## Command groups and change folders

| Command   | Order | Change folder (new name) | GitHub # | Blocked by |
|----------|-------|---------------------------|----------|------------|
| policy   | 01    | policy-01-unify-policies-engine | 176 | — |
| patch    | 01    | patch-01-patch-mode-preview-apply | 177 | #176 |
| backlog  | 01    | backlog-01-add-backlog-dependency-analysis-and-commands | 116 | — |
| backlog  | 02    | backlog-02-add-backlog-add-interactive-issue-creation | 173 | #116 |
| backlog  | 03    | backlog-03-daily-standup-exceptions-first | 175 | #176, #177 |
| backlog  | 04    | backlog-04-sprint-planning-capacity-commitment-support | 170 | — |
| backlog  | 05    | backlog-05-story-complexity-splitting-hints-support | 171 | — |
| backlog  | 06    | backlog-06-kanban-flow-metrics | 183 | #116, #176 |
| backlog  | 07    | backlog-07-safe-pi-planning | 184 | #116, #176 |
| backlog  | 08    | backlog-08-risk-rollups | 182 | #116, #176, #170, #171 |
| backlog  | 09    | backlog-09-definition-of-done-support | 169 | — (optional: #176) |
| ceremony | 01    | ceremony-01-ceremony-cockpit | 185 | #175, #170, #176 (optional: #183, #184) |
| validation | 01  | validation-01-add-thorough-codebase-validation | 163 | — |
| sidecar  | 01    | sidecar-01-add-sidecar-flask-support | 102 | — |
| bundle   | 01    | bundle-01-add-bundle-mapping-strategy | 121 | — |

## GitHub "Blocked by" relationships

Set these in GitHub so issue dependencies are explicit:

1. **Issue #177** (patch-mode): **Blocked by** #176  
2. **Issue #173** (backlog add): **Blocked by** #116  
3. **Issue #175** (daily standup E1): **Blocked by** #176, #177  
4. **Issue #183** (kanban flow): **Blocked by** #116, #176  
5. **Issue #184** (safe PI): **Blocked by** #116, #176  
6. **Issue #182** (risk rollups): **Blocked by** #116, #176, #170, #171  
7. **Issue #185** (ceremony cockpit): **Blocked by** #175, #170, #176  

**How to set in GitHub**: Open the issue (e.g. <https://github.com/nold-ai/specfact-cli/issues/177>) → right sidebar **Relationships** → **Mark as blocked by** → search and select the blocking issue(s). Repeat for each issue in the table above that has blockers.

## Parent issues (Epics) per command

One parent issue per main command for grouping. **Do not add an Epic label** — the project **Type** property already defines Epic (and other issue types). Set Type to Epic for these parent issues in the project board. Link child/change issues via **Relationships** (e.g. sub-issues or "tracks") or by setting the project **Parent** field to the epic.

| Command / area | Parent issue | GitHub # |
|----------------|-------------|----------|
| `specfact backlog` | [Epic] specfact backlog | [#186](https://github.com/nold-ai/specfact-cli/issues/186) |
| `specfact policy` | [Epic] specfact policy | [#187](https://github.com/nold-ai/specfact-cli/issues/187) |
| Patch mode | [Epic] Patch mode (preview/apply) | [#188](https://github.com/nold-ai/specfact-cli/issues/188) |
| `specfact ceremony` | [Epic] specfact ceremony | [#189](https://github.com/nold-ai/specfact-cli/issues/189) |
| Thorough validation | [Epic] Thorough codebase validation | [#190](https://github.com/nold-ai/specfact-cli/issues/190) |
| Sidecar validation | [Epic] Sidecar validation | [#191](https://github.com/nold-ai/specfact-cli/issues/191) |
| Bundle mapping | [Epic] Bundle/spec mapping | [#192](https://github.com/nold-ai/specfact-cli/issues/192) |
| **Architecture** | [Epic] Architecture (CLI structure, modularity, performance) | [#194](https://github.com/nold-ai/specfact-cli/issues/194) |

**Linking child issues**: On each change issue (e.g. #116, #173, #175, …), use the project **Type** and **Parent** (or GitHub Relationships) to associate it with the epic above. Type (Epic, Feature, Story, etc.) is set via the project **Type** property only; do not use an Epic or other type label.

## Suggested implementation waves

- **Wave 1 (foundation)**: policy-01, backlog-01  
- **Wave 2**: patch-01, backlog-02, backlog-04, backlog-05, backlog-09, validation-01, sidecar-01, bundle-01  
- **Wave 3**: backlog-03 (needs policy-01 + patch-01), backlog-06, backlog-07, backlog-08  
- **Wave 4**: ceremony-01 (after backlog-03, backlog-04, policy-01)
