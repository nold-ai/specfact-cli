---
layout: default
title: Tutorial - Backlog Refine with Your AI IDE
description: Integrate SpecFact CLI backlog refinement with your AI IDE. Improve story quality, underspec/overspec, split stories, fix ambiguities, respect DoR, and use custom template mapping.
permalink: /getting-started/tutorial-backlog-refine-ai-ide/
---

# Tutorial: Backlog Refine with Your AI IDE (Agile DevOps Teams)

This tutorial walks agile DevOps teams through integrating SpecFact CLI backlog refinement with their AI IDE (Cursor, VS Code + Copilot, Claude Code, etc.) using the interactive slash prompt. You will improve backlog story quality, make informed decisions about underspecification, split stories when too big, fix ambiguities, respect Definition of Ready (DoR), and optionally use custom template mapping for advanced teams.

Preferred command path is `specfact backlog ceremony refinement ...`. The legacy `specfact backlog refine ...` path remains supported for compatibility.

**Time**: ~20–30 minutes  
**Outcome**: End-to-end flow from raw backlog items to template-compliant, DoR-ready stories via your AI IDE.

---

## What You'll Learn

- Run `specfact backlog ceremony refinement` and use the **slash prompt** in your AI IDE for interactive refinement
- Use the **interactive feedback loop**: present story → assess specification level (under-/over-/fit) → list ambiguities → ask clarification → re-refine until approved
- Improve story quality: identify **underspecified** (missing AC, vague scope), **overspecified** (too many sub-steps, implementation detail), or **fit-for-scope** stories
- Decide when to **split** stories that are too big
- Respect **Definition of Ready (DoR)** once defined in your team
- For advanced teams: point to **custom template mapping** (e.g. ADO custom fields) when required

---

## Prerequisites

- SpecFact CLI installed (`uvx specfact-cli@latest` or `pip install specfact-cli`)
- Access to a backlog (GitHub repo or Azure DevOps project)
- AI IDE with slash commands (Cursor, VS Code + Copilot, etc.)
- Optional: `specfact init ide --ide cursor` (or your IDE) so the backlog-refine slash command is available

---

## Step 1: Run Backlog Refine and Get Items

From your **repo root** (or where your backlog lives):

```bash
# GitHub: org/repo are auto-detected from git remote when run from a GitHub clone
specfact backlog ceremony refinement github --search "is:open label:feature" --limit 5 --preview

# Or export to a temp file for your AI IDE to process (recommended for interactive loop)
specfact backlog ceremony refinement github --export-to-tmp --search "is:open label:feature" --limit 5
```

**Auto-detect from clone**: When you run from a **GitHub** clone (e.g. `https://github.com/owner/repo` or `git@github.com:owner/repo.git`), SpecFact infers `repo_owner` and `repo_name` from `git remote get-url origin`—no `--repo-owner`/`--repo-name` needed. When you run from an **Azure DevOps** clone (e.g. `https://dev.azure.com/org/project/_git/repo`; SSH keys: `git@ssh.dev.azure.com:v3/org/project/repo`; other SSH: `user@dev.azure.com:v3/org/project/repo`), org and project are inferred. Override with `.specfact/backlog.yaml`, env vars (`SPECFACT_GITHUB_REPO_OWNER`, `SPECFACT_ADO_ORG`, etc.), or CLI options when not in the repo or to override.

If you're **not** in a clone, pass adapter context explicitly:

```bash
specfact backlog ceremony refinement github --repo-owner OWNER --repo-name REPO --search "is:open label:feature" --limit 5 --preview
# or ADO:
specfact backlog ceremony refinement ado --ado-org ORG --ado-project PROJECT --state Active --limit 5 --preview
```

- Use `--ignore-refined` (default) so `--limit` applies to items that **need** refinement
- Use `--id ISSUE_ID` to refine a **single** item by ID
- Use `--check-dor` when your team has a DoR config in `.specfact/dor.yaml`

---

## Step 2: Invoke the Slash Prompt in Your AI IDE

In Cursor, VS Code, or your IDE:

1. Open the **slash command** for backlog refinement (e.g. `/specfact.backlog-refine` or the equivalent in your IDE).
2. Pass the same arguments you would use in the CLI, for example:
   - `/specfact.backlog-refine --adapter github --repo-owner OWNER --repo-name NAME --labels feature --limit 5`

The AI will use the **SpecFact Backlog Refinement** prompt, which includes:

- Template-driven refinement (user story, defect, spike, enabler)
- **Interactive refinement (Copilot mode)**: present story → list ambiguities → ask clarification → re-refine until you approve
- **Specification level**: for each story, the AI assesses whether it is **under-specified**, **over-specified**, or **fit for scope and intent**, with evidence (missing AC, vague scope, too many sub-steps, etc.)

---

## Step 3: Use the Interactive Feedback Loop

For each story, the AI should:

1. **Present** the refined story (Title, Body, Acceptance Criteria, Metrics) in a clear, scannable format.
2. **Assess specification level**:
   - **Under-specified**: Missing acceptance criteria, vague scope, unclear “so that” or user value. List what’s missing.
   - **Over-specified**: Too much implementation detail, too many sub-steps for one story, or solution prescribed instead of outcome. Suggest what to trim or move.
   - **Fit for scope and intent**: Clear persona, capability, benefit, and testable AC; appropriate size. State briefly why it’s ready.
3. **List ambiguities** or open questions (e.g. conflicting assumptions, unclear priority).
4. **Ask** you (PO/stakeholder): “Do you want any changes? Any ambiguities to resolve? Should this story be split?”
5. **Re-refine** if you give feedback, then repeat from “Present” until you **explicitly approve** (e.g. “looks good”, “approved”).
6. Only after approval: mark the story done and move to the next. Do **not** update the backlog item until that story is approved.

This loop ensures the DevOps team sees **underspecification** (and over-specification) explicitly and can improve story quality and respect DoR before committing to the backlog.

---

## Step 4: Respect Definition of Ready (DoR)

If your team uses DoR:

1. Create or edit `.specfact/dor.yaml` in the repo (e.g. require story_points, priority, business_value, acceptance_criteria).
2. Run refine with `--check-dor`:

   ```bash
   specfact backlog ceremony refinement github --repo-owner OWNER --repo-name REPO --check-dor --labels feature
   ```

3. In the interactive loop, treat DoR as part of “fit for scope”: if the refined story doesn’t meet DoR (e.g. missing AC or story points), the AI should flag it as under-specified or not ready and suggest what to add.

---

## Step 5: When to Split a Story

During the loop, if the AI or you identify that a story is **too big** (e.g. multiple capabilities, many sub-steps, or clearly two user outcomes):

- The AI should state: “This story may be too large; consider splitting by [capability / user outcome / step].”
- You decide: either split into two (or more) stories and refine each separately, or keep as one and trim scope. Only after that decision should the story be marked approved and written back.

---

## Step 6: Write Back (When Ready)

When you’re satisfied with the refined content:

```bash
# If you used --export-to-tmp, save the refined file as ...-refined.md, then:
# (From repo root, org/repo or org/project are auto-detected from git remote)
specfact backlog ceremony refinement github --import-from-tmp --write

# Or run refine interactively with --write (use with care; confirm each item)
specfact backlog ceremony refinement github --write --labels feature --limit 3
```

Use `--preview` (default) until you’re confident; use `--write` only when you want to update the remote backlog.

---

## Step 7: Advanced Teams — Custom Template Mapping

If your team uses **custom fields** (e.g. Azure DevOps custom process templates):

1. **ADO**: Add a custom field mapping file and point the CLI to it:

   ```bash
   specfact backlog ceremony refinement ado --ado-org ORG --ado-project PROJECT \
     --custom-field-mapping .specfact/templates/backlog/field_mappings/ado_custom.yaml \
     --state Active
   ```

2. See **[Template Customization](../guides/template-customization.md)** and **[Custom Field Mapping](../guides/custom-field-mapping.md)** for defining templates and mapping ADO fields.
3. The same **interactive loop and specification-level assessment** (under-/over-/fit) apply; the AI should use your template’s required sections when assessing “fit for scope”.

---

## Summary

| Goal                         | How |
|-----------------------------|-----|
| Improve story quality       | Use the interactive loop; fix under-/over-specification and ambiguities before approving. |
| Know if a story is under/over/fit | AI assesses each story and lists evidence; you decide to add detail, split, or accept. |
| Split stories that are too big | AI suggests splitting when appropriate; you refine each new story separately. |
| Respect DoR                 | Use `--check-dor` and treat DoR as part of “fit for scope” in the loop. |
| Custom templates / mapping  | Use `--custom-field-mapping` (ADO) and custom templates; see Template Customization and Custom Field Mapping guides. |

---

## Related Documentation

- **[Backlog Refinement Guide](../guides/backlog-refinement.md)** — Full reference: templates, options, export/import, DoR
- **[Story scope and specification level](../guides/backlog-refinement.md#story-scope-and-specification-level)** — Underspecification, over-specification, fit-for-scope
- **[Definition of Ready (DoR)](../guides/backlog-refinement.md#step-45-definition-of-ready-dor-validation-optional)** — DoR configuration and validation
- **[Template Customization](../guides/template-customization.md)** — Custom templates for advanced teams
- **[Custom Field Mapping](../guides/custom-field-mapping.md)** — ADO custom field mapping
- **[IDE Integration](../guides/ide-integration.md)** — Set up slash commands in Cursor, VS Code, etc.
