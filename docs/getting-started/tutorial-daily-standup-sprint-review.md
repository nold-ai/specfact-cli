---
layout: default
title: Tutorial - Daily Standup and Sprint Review with SpecFact CLI
description: End-to-end daily standup and sprint review using specfact backlog ceremony standup. Auto-detect repo from git (GitHub or Azure DevOps), view standup table, post standup comments, use interactive mode and Copilot export.
permalink: /getting-started/tutorial-daily-standup-sprint-review/
---

# Tutorial: Daily Standup and Sprint Review with SpecFact CLI

This tutorial walks you through a complete **daily standup and sprint review** workflow using SpecFact CLI: view your backlog items, optionally post standup comments to issues, use interactive step-through and Copilot export—with **no need to pass org/repo or org/project** when you run from your cloned repo.

Preferred command path is `specfact backlog ceremony standup ...`. The legacy `specfact backlog daily ...` path remains supported for compatibility.

**Time**: ~10–15 minutes  
**Outcome**: End-to-end flow from "clone + auth" to standup view, optional post, interactive review, and Copilot-ready export.

---

## What You'll Learn

- Run **`specfact backlog ceremony standup`** and see your standup table (assigned + unassigned items) with **auto-detected** GitHub org/repo or Azure DevOps org/project from the git remote
- Use **`.specfact/backlog.yaml`** or environment variables when you're not in the repo (e.g. CI) or to override
- **Post a standup comment** to the first (or selected) item with `--yesterday`, `--today`, `--blockers` and `--post`
- Use **`--interactive`** for step-by-step story review (arrow-key selection, full detail, latest comment + hidden-count hint, and optional in-flow posting on the selected story)
- Use **`--copilot-export <path>`** to write a Markdown summary for Copilot slash-command during standup;
  add **`--comments`** (alias **`--annotations`**) to include descriptions and comment annotations when
  the adapter supports fetching comments
- Use **`--summarize`** or **`--summarize-to <path>`** to output a **prompt** (instruction + filter context
  + standup data) for a slash command (e.g. `specfact.daily`) or copy-paste to Copilot to **generate a
  standup summary**; add **`--comments`**/**`--annotations`** to include comment annotations in the prompt.
  The prompt content is always **normalized to Markdown-only text** (no raw HTML tags or HTML entities) so
  ADO-style HTML descriptions/comments and GitHub/Markdown content render consistently.
- Use the **`specfact.backlog-daily`** (or `specfact.daily`) slash prompt for interactive walkthrough with the DevOps team story-by-story (focus, issues, open questions, discussion notes as comments)
- Filter by **`--assignee`**, **`--sprint`** / **`--iteration`**, **`--search`**, **`--release`**, **`--id`**, **`--first-issues`** / **`--last-issues`**, **`--blockers-first`**, and optional **`--suggest-next`**

---

## Prerequisites

- SpecFact CLI installed (`uvx specfact-cli@latest` or `pip install specfact-cli`)
- **Authenticated** to your backlog provider: `specfact backlog auth github` or Azure DevOps (PAT in env)
- A **clone** of your repo (GitHub or Azure DevOps) so the CLI can auto-detect org/repo or org/project from `git remote origin`

---

## Step 1: Run Daily Standup (Auto-Detect Repo)

From your **repo root** (where `.git` lives):

```bash
# GitHub: org/repo are inferred from git remote origin
specfact backlog ceremony standup github

# Azure DevOps: org/project are inferred from git remote origin
# (e.g. https://dev.azure.com/... or git@ssh.dev.azure.com:v3/... for SSH keys; user@dev.azure.com:v3/... if not using SSH keys)
specfact backlog ceremony standup ado
```

**What you see**:

- **Daily standup** table: your assigned (or filtered) items with ID, title, status, last updated, yesterday/today/blockers columns
- **Pending / open for commitment**: unassigned items in the same scope

**No `--repo-owner`/`--repo-name` (GitHub) or `--ado-org`/`--ado-project` (ADO) needed** when the repo was cloned from that provider—SpecFact reads `git remote get-url origin` and infers the context.

If you're **not** in a clone (e.g. different directory), use one of:

- **`.specfact/backlog.yaml`** in the project (see [Project backlog context](../guides/devops-adapter-integration.md#project-backlog-context-specfactbacklogyaml))
- **Environment variables**: `SPECFACT_GITHUB_REPO_OWNER`, `SPECFACT_GITHUB_REPO_NAME` or `SPECFACT_ADO_ORG`, `SPECFACT_ADO_PROJECT`
- **CLI options**: `--repo-owner` / `--repo-name` or `--ado-org` / `--ado-project`

---

## Step 2: Filter and Scope

Narrow the list to your sprint or assignee:

```bash
# My items only (GitHub: login; ADO: current user)
specfact backlog ceremony standup github --assignee me

# Current sprint (when adapter supports it, e.g. ADO)
specfact backlog ceremony standup ado --sprint current

# Open items, limit 10, blockers first
specfact backlog ceremony standup github --state open --limit 10 --blockers-first
```

Default scope is **state=open**, **limit=20**; overridable via `SPECFACT_STANDUP_STATE`, `SPECFACT_STANDUP_LIMIT`, or `.specfact/standup.yaml`.

---

## Step 3: Post a Standup Comment (Optional)

To add a **standup comment** to the **first** item in the list, pass **values** for yesterday/today/blockers and `--post`:

```bash
specfact backlog ceremony standup github \
  --yesterday "Worked on daily standup and progress support" \
  --today "Will add tests and docs" \
  --blockers "None" \
  --post
```

**Expected**: The CLI posts a comment on that item's issue (GitHub issue or ADO work item) with a standup block (Yesterday / Today / Blockers). You'll see: `✓ Standup comment posted to story <id>: <issue URL>`.

**Important**: You must pass **values** for at least one of `--yesterday`, `--today`, or `--blockers`. Using `--post` alone (or with flags but no text) will prompt you to add values; see the in-command message and help.

---

## Step 4: Interactive Step-Through (Optional)

For a **refine-like** walkthrough (select item → view full detail → next/previous/back/exit):

```bash
specfact backlog ceremony standup github --interactive
```

- Use the menu to **select** an item (arrow keys).
- View **full detail** (description, acceptance criteria, standup fields, and comment context). Interactive detail shows the **latest comment only** plus a hint when older comments exist.
- Choose **Next story**, **Previous story**, **Post standup update** (posts to the currently selected story), **Back to list**, or **Exit**.

Use **`--suggest-next`** to show a suggested next item by value score (business value / (story points × priority)) when the data is available.

---

## Step 5: Export for Copilot (Optional)

To feed a **summary file** into your AI IDE (e.g. for a Copilot slash-command during standup):

```bash
specfact backlog ceremony standup github --copilot-export ./standup-summary.md --comments
```

The file contains one section per item (ID, title, status, assignees, last updated, progress, blockers).
With `--comments`/`--annotations`, it also includes the item description and comment annotations when the
adapter supports fetching comments. You can open it in your IDE and use it with Copilot. Same scope as
the standup table (state, assignee, limit, etc.).

---

## Step 6: Standup Summary Prompt (Optional)

To get a **prompt** you can paste into Copilot or feed to a slash command (e.g. `specfact.daily`) so an AI can **generate a short standup summary** (e.g. "Today: 3 in progress, 1 blocked, 2 pending commitment"):

```bash
# Print prompt to stdout (copy-paste to Copilot). In an interactive terminal, SpecFact renders a
# Markdown-formatted view; in CI/non-interactive environments the same normalized Markdown is printed
# without ANSI formatting.
specfact backlog ceremony standup github --summarize --comments

# Write prompt to a file (e.g. for slash command). The file always contains plain Markdown-only content
# (no raw HTML, no ANSI control codes), suitable for IDE slash commands or copy/paste into Copilot.
specfact backlog ceremony standup github --summarize-to ./standup-prompt.md --comments
```

The output includes an instruction to generate a standup summary, the applied filter context (adapter,
state, sprint, assignee, limit), and the same per-item data as `--copilot-export`. With
`--comments`/`--annotations`, the prompt includes normalized descriptions and comment annotations when
supported. Use it with the **`specfact.backlog-daily`** slash prompt for interactive team walkthrough
(story-by-story, current focus, issues/open questions, discussion notes as comments).

---

## End-to-End Example: One Standup Session

1. **Authenticate once** (if not already):

   ```bash
   specfact backlog auth github
   ```

2. **Open your repo** and run daily (repo auto-detected):

   ```bash
   cd /path/to/your-repo
   specfact backlog ceremony standup github
   ```

3. **Optional: post today's standup** to the first item:

   ```bash
   specfact backlog ceremony standup github \
     --yesterday "Implemented backlog context and git inference" \
     --today "Docs and tests for daily standup tutorial" \
     --blockers "None" \
     --post
   ```

4. **Optional: interactive review** or **Copilot export**:

   ```bash
   specfact backlog ceremony standup github --interactive --last-comments 3
   # or
   specfact backlog ceremony standup github --copilot-export ./standup.md
   ```

---

## Summary

| Goal | How |
|------|-----|
| View standup without typing org/repo | Run `specfact backlog ceremony standup github` or `ado` from **repo root**; org/repo or org/project are **auto-detected** from git remote. |
| Override or use outside repo | Use `.specfact/backlog.yaml`, env vars (`SPECFACT_GITHUB_REPO_OWNER`, etc.), or CLI `--repo-owner`/`--repo-name` or `--ado-org`/`--ado-project`. |
| Post standup to first item | Use `--yesterday "..."` `--today "..."` `--blockers "..."` and `--post` (values required). |
| Post standup while reviewing selected story | Use `--interactive` and choose **Post standup update** from navigation. |
| Step through stories with readable comment context | Use `--interactive`; it shows latest comment + hidden-count hint. Use `--first-comments`/`--last-comments` to tune comment density. |
| Feed standup into Copilot | Use `--copilot-export <path>`; add `--comments`/`--annotations` for comment annotations. |
| Generate standup summary via AI (slash command or Copilot) | Use `--summarize` (stdout) or `--summarize-to <path>`; add `--comments`/`--annotations` for comment annotations; use with `specfact.backlog-daily` slash prompt. |

---

## Related Documentation

- **[Agile/Scrum Workflows](../guides/agile-scrum-workflows.md)** — Daily standup, iteration/sprint, unassigned items, blockers-first
- **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** — Project backlog context (`.specfact/backlog.yaml`), env vars, **Git fallback (auto-detect from clone)** for GitHub and Azure DevOps
- **[Backlog Refinement Guide](../guides/backlog-refinement.md)** — Template-driven refinement (complementary to daily standup)
