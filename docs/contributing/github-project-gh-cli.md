# SpecFact CLI project – gh CLI automation

How to set **Projects** and project fields (Status, Type, Parent issue) that appear on each issue/PR **sidebar** for the [SpecFact CLI project](https://github.com/orgs/nold-ai/projects/1). All of this can be done with the GitHub CLI (`gh`).

**Project:** SpecFact CLI · <https://github.com/orgs/nold-ai/projects/1>  
**Owner:** `nold-ai` · **Project number:** `1`

---

## Add issue or PR to the project (Projects field on sidebar)

```bash
gh project item-add 1 --owner nold-ai --url "https://github.com/nold-ai/specfact-cli/issues/ISSUE_NUMBER"
# or for a PR:
gh project item-add 1 --owner nold-ai --url "https://github.com/nold-ai/specfact-cli/pull/PR_NUMBER"
```

Requires project scope: `gh auth refresh -s project` if it fails.

---

## Set Status (single-select)

You need the **project item ID** (not the issue number), then:

```bash
gh project item-edit --id ITEM_ID --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id OPTION_ID
```

**IDs for SpecFact CLI project (as of 2026-02):**

- Project ID: `PVT_kwDODWwjB84BKws4`
- Status field ID: `PVTSSF_lADODWwjB84BKws4zg6iOak`
- Status options: Todo `f75ad846`, In Progress `47fc9ee4`, Done `98236657`, Rejected `82beb238`

**Get issue item ID (after the issue is on the project):**

```bash
ISSUE_ITEM_ID=$(gh api graphql -f query='{organization(login: "nold-ai") {projectV2(number: 1) {items(first: 100) {nodes {id content {... on Issue {number}}}}}}}' | jq -r '.data.organization.projectV2.items.nodes[] | select(.content.number == ISSUE_NUMBER) | .id')
```

Only one field can be updated per `gh project item-edit` call for non-draft items.

---

## List project fields and option IDs (Type, etc.)

```bash
gh project field-list 1 --owner nold-ai --format json
```

Use this to get field and option IDs for any single-select (e.g. Type), then set them with `gh project item-edit ... --single-select-option-id ID`.

---

## Parent issue (Epic) field

The project has a **Parent issue** field (ID `PVTF_lADODWwjB84BKws4zg6iObA`). It is an item-link field. `gh project item-edit` does not support setting it (no item-link flag). Use the GraphQL mutation `updateProjectV2ItemFieldValue` if you need to set it from automation.

---

## Summary

| Sidebar property | gh CLI |
|------------------|--------|
| **Projects** (add to SpecFact CLI) | `gh project item-add 1 --owner nold-ai --url URL` |
| **Status** | `gh project item-edit --id ITEM_ID --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id OPTION_ID` |
| **Type** (if added as single-select) | Same pattern; get IDs with `gh project field-list 1 --owner nold-ai --format json` |
| **Parent issue** | GraphQL only (not `gh project item-edit`) |

Refs: [gh project item-add](https://cli.github.com/manual/gh_project_item-add), [gh project item-edit](https://cli.github.com/manual/gh_project_item-edit), [gh project field-list](https://cli.github.com/manual/gh_project_field-list).
