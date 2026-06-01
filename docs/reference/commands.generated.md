---
layout: default
title: Generated SpecFact CLI Command Overview
permalink: /reference/generated-command-overview/
exempt: true
exempt_reason: Generated command contract artifact.
---

# Generated SpecFact CLI Command Overview

This file is generated from the current CLI command tree. Do not edit by hand.

| Command | Owner | Options | Subcommands | Context |
| --- | --- | --- | --- | --- |
| `specfact` | core | --banner, --debug, --input-format, --install-completion, --interactive, --mode, --no-interactive, --output-format, --show-completion, --skip-checks, --version; args: - | backlog, code, govern, init, module, project, spec, upgrade |  |
| `specfact backlog` | nold-ai/specfact-backlog | --install-completion, --show-completion; args: - | add, analyze-deps, auth, ceremony, daily, delta, diff, init-config, map-fields, promote, refine, sync, verify-readiness |  |
| `specfact backlog add` | nold-ai/specfact-backlog | --acceptance-criteria, --adapter, --body, --body-end-marker, --business-value, --check-dor, --custom-config, --description-format, --non-interactive, --parent, --priority, --project-id, --provider-field, --repo-path, --sprint, --story-points, --template, --title, --type; args: - | - |  |
| `specfact backlog analyze-deps` | nold-ai/specfact-backlog | --adapter, --custom-config, --json-export, --output, --project-id, --template; args: - | - |  |
| `specfact backlog auth` | nold-ai/specfact-backlog | -; args: - | azure-devops, clear, github, status |  |
| `specfact backlog auth azure-devops` | nold-ai/specfact-backlog | --pat, --use-device-code; args: - | - |  |
| `specfact backlog auth clear` | nold-ai/specfact-backlog | --provider; args: - | - |  |
| `specfact backlog auth github` | nold-ai/specfact-backlog | --base-url, --client-id, --scopes; args: - | - |  |
| `specfact backlog auth status` | nold-ai/specfact-backlog | -; args: - | - |  |
| `specfact backlog ceremony` | nold-ai/specfact-backlog | -; args: - | flow, pi-summary, planning, refinement, standup |  |
| `specfact backlog ceremony flow` | nold-ai/specfact-backlog | --mode; args: - | - |  |
| `specfact backlog ceremony pi-summary` | nold-ai/specfact-backlog | --mode; args: - | - |  |
| `specfact backlog ceremony planning` | nold-ai/specfact-backlog | --mode; args: - | - |  |
| `specfact backlog ceremony refinement` | nold-ai/specfact-backlog | -; args: - | - |  |
| `specfact backlog ceremony standup` | nold-ai/specfact-backlog | --mode; args: - | - |  |
| `specfact backlog daily` | nold-ai/specfact-backlog | --ado-org, --ado-project, --ado-team, --ado-token, --annotations, --assignee, --blockers, --blockers-first, --comments, --copilot-export, --first-comments, --first-issues, --github-token, --id, --interactive, --iteration, --labels, --last-comments, --last-issues, --limit, --mode, --no-show-unassigned, --patch, --post, --release, --repo-name, --repo-owner, --search, --show-unassigned, --sprint, --state, --suggest-next, --summarize, --summarize-to, --tags, --today, --unassigned-only, --yesterday; args: - | - |  |
| `specfact backlog delta` | nold-ai/specfact-backlog | -; args: - | cost-estimate, impact, rollback-analysis, status |  |
| `specfact backlog delta cost-estimate` | nold-ai/specfact-backlog | --adapter, --baseline-file, --project-id, --template; args: - | - |  |
| `specfact backlog delta impact` | nold-ai/specfact-backlog | --adapter, --project-id, --template; args: - | - |  |
| `specfact backlog delta rollback-analysis` | nold-ai/specfact-backlog | --adapter, --baseline-file, --project-id, --template; args: - | - |  |
| `specfact backlog delta status` | nold-ai/specfact-backlog | --adapter, --baseline-file, --project-id, --repo-name, --repo-owner, --since, --template; args: - | - |  |
| `specfact backlog diff` | nold-ai/specfact-backlog | --adapter, --baseline-file, --project-id, --template; args: - | - |  |
| `specfact backlog init-config` | nold-ai/specfact-backlog | --force; args: - | - |  |
| `specfact backlog map-fields` | nold-ai/specfact-backlog | --ado-base-url, --ado-framework, --ado-org, --ado-project, --ado-token, --github-project-id, --github-project-v2-id, --github-type-field-id, --github-type-option, --non-interactive, --provider, --reset; args: - | - |  |
| `specfact backlog promote` | nold-ai/specfact-backlog | --adapter, --item-id, --project-id, --template, --to-status; args: - | - |  |
| `specfact backlog refine` | nold-ai/specfact-backlog | --ado-org, --ado-project, --ado-team, --ado-token, --assignee, --auto-accept-high-confidence, --auto-bundle, --bundle, --check-dor, --custom-field-mapping, --export-to-tmp, --first-comments, --first-issues, --framework, --github-token, --id, --ignore-refined, --import-from-tmp, --iteration, --labels, --last-comments, --last-issues, --limit, --no-ignore-refined, --no-preview, --openspec-comment, --persona, --preview, --release, --repo-name, --repo-owner, --search, --sprint, --state, --tags, --template, --tmp-file, --write; args: - | - |  |
| `specfact backlog sync` | nold-ai/specfact-backlog | --adapter, --baseline-file, --force-baseline-overwrite, --output-format, --project-id, --template; args: - | - |  |
| `specfact backlog verify-readiness` | nold-ai/specfact-backlog | --adapter, --project-id, --target-items, --template; args: - | - |  |
| `specfact code` | nold-ai/specfact-codebase | --install-completion, --show-completion; args: - | analyze, drift, import, repro, review, validate |  |
| `specfact code analyze` | nold-ai/specfact-codebase | -; args: - | contracts |  |
| `specfact code analyze contracts` | nold-ai/specfact-codebase | --bundle, --repo; args: - | - |  |
| `specfact code drift` | nold-ai/specfact-codebase | -; args: - | detect |  |
| `specfact code drift detect` | nold-ai/specfact-codebase | --format, --out, --repo; args: - | - |  |
| `specfact code import` | nold-ai/specfact-codebase | --confidence, --enrich-for-speckit, --enrichment, --entry-point, --exclude-tests, --force, --include-tests, --key-format, --no-enrich-for-speckit, --no-revalidate-features, --repo, --report, --revalidate-features, --shadow-only; args: - | from-bridge, from-code |  |
| `specfact code import from-bridge` | nold-ai/specfact-codebase | --adapter, --dry-run, --force, --out-branch, --repo, --report, --write; args: - | - |  |
| `specfact code import from-code` | nold-ai/specfact-codebase | --confidence, --enrich-for-speckit, --enrichment, --entry-point, --exclude-tests, --force, --include-tests, --key-format, --no-enrich-for-speckit, --no-revalidate-features, --repo, --report, --revalidate-features, --shadow-only; args: - | - |  |
| `specfact code repro` | nold-ai/specfact-codebase | --budget, --crosshair-per-path-timeout, --crosshair-required, --fail-fast, --fix, --out, --repo, --sidecar, --sidecar-bundle, --verbose; args: - | setup |  |
| `specfact code repro setup` | nold-ai/specfact-codebase | --install-crosshair, --repo; args: - | - |  |
| `specfact code review` | nold-ai/specfact-code-review | -; args: - | ledger, rules, run |  |
| `specfact code review ledger` | nold-ai/specfact-code-review | -; args: - | reset, status, update |  |
| `specfact code review ledger reset` | nold-ai/specfact-code-review | --confirm; args: - | - |  |
| `specfact code review ledger status` | nold-ai/specfact-code-review | -; args: - | - |  |
| `specfact code review ledger update` | nold-ai/specfact-code-review | --from; args: - | - |  |
| `specfact code review rules` | nold-ai/specfact-code-review | -; args: - | init, show, update |  |
| `specfact code review rules init` | nold-ai/specfact-code-review | --ide; args: - | - |  |
| `specfact code review rules show` | nold-ai/specfact-code-review | -; args: - | - |  |
| `specfact code review rules update` | nold-ai/specfact-code-review | --ide; args: - | - |  |
| `specfact code review run` | nold-ai/specfact-code-review | --bug-hunt, --enforcement, --exclude-tests, --fix, --focus, --include-noise, --include-tests, --instructions, --interactive, --json, --level, --mode, --no-tests, --out, --path, --preview-fixes, --scope, --score-only, --suppress-noise, --with-mutation; args: - | - |  |
| `specfact code validate` | nold-ai/specfact-codebase | -; args: - | sidecar |  |
| `specfact code validate sidecar` | nold-ai/specfact-codebase | -; args: - | init, run |  |
| `specfact code validate sidecar init` | nold-ai/specfact-codebase | -; args: - | - |  |
| `specfact code validate sidecar run` | nold-ai/specfact-codebase | --no-run-crosshair, --no-run-specmatic, --run-crosshair, --run-specmatic; args: - | - |  |
| `specfact govern` | nold-ai/specfact-govern | --install-completion, --show-completion; args: - | enforce, patch |  |
| `specfact govern enforce` | nold-ai/specfact-govern | -; args: - | sdd, stage |  |
| `specfact govern enforce sdd` | nold-ai/specfact-govern | --no-interactive, --out, --output-format, --sdd; args: - | - |  |
| `specfact govern enforce stage` | nold-ai/specfact-govern | --preset; args: - | - |  |
| `specfact govern patch` | nold-ai/specfact-govern | -; args: - | apply |  |
| `specfact govern patch apply` | nold-ai/specfact-govern | --dry-run, --write, --yes; args: - | - |  |
| `specfact init` | core | --install, --install-completion, --install-deps, --profile, --repo, --show-completion; args: - | ide |  |
| `specfact init ide` | core | --env-manager, --force, --ide, --install-deps, --prompts, --repo; args: - | - |  |
| `specfact module` | core | --install-completion, --show-completion; args: - | add-registry, alias, disable, doctor, enable, init, install, list, list-registries, remove-registry, search, show, uninstall, upgrade |  |
| `specfact module add-registry` | core | --id, --priority, --trust; args: - | - |  |
| `specfact module alias` | core | -; args: - | create, list, remove |  |
| `specfact module alias create` | core | --force; args: - | - |  |
| `specfact module alias list` | core | -; args: - | - |  |
| `specfact module alias remove` | core | -; args: - | - |  |
| `specfact module disable` | core | --force; args: - | - |  |
| `specfact module doctor` | core | --repo; args: - | - |  |
| `specfact module enable` | core | --force, --trust-non-official; args: - | - |  |
| `specfact module init` | core | --repo, --scope, --trust-non-official; args: - | - |  |
| `specfact module install` | core | --force, --reinstall, --repo, --scope, --skip-deps, --source, --trust-non-official, --version; args: - | - |  |
| `specfact module list` | core | --available, --marketplace, --show-bundled-available, --show-origin, --source; args: - | - |  |
| `specfact module list-registries` | core | -; args: - | - |  |
| `specfact module remove-registry` | core | -; args: - | - |  |
| `specfact module search` | core | -; args: - | - |  |
| `specfact module show` | core | -; args: - | - |  |
| `specfact module uninstall` | core | --repo, --scope; args: - | - |  |
| `specfact module upgrade` | core | --all, --yes; args: - | - |  |
| `specfact project` | nold-ai/specfact-project | --install-completion, --show-completion; args: - | devops-flow, export, export-roadmap, health-check, import, init-personas, link-backlog, lock, locks, merge, regenerate, resolve-conflict, snapshot, sync, unlock, version |  |
| `specfact project devops-flow` | nold-ai/specfact-project | --action, --bundle, --no-interactive, --project-name, --repo, --stage, --verbose; args: - | - |  |
| `specfact project export` | nold-ai/specfact-project | --bundle, --list-personas, --no-interactive, --out, --output, --output-dir, --persona, --repo, --stdout, --template; args: - | - |  |
| `specfact project export-roadmap` | nold-ai/specfact-project | --bundle, --no-interactive, --output, --project-name, --repo; args: - | - |  |
| `specfact project health-check` | nold-ai/specfact-project | --bundle, --no-interactive, --project-name, --repo, --verbose; args: - | - |  |
| `specfact project import` | nold-ai/specfact-project | --bundle, --dry-run, --file, --input, --no-interactive, --persona, --repo; args: - | - |  |
| `specfact project init-personas` | nold-ai/specfact-project | --bundle, --no-interactive, --persona, --repo; args: - | - |  |
| `specfact project link-backlog` | nold-ai/specfact-project | --adapter, --bundle, --no-interactive, --project-id, --project-name, --repo, --template; args: - | - |  |
| `specfact project lock` | nold-ai/specfact-project | --bundle, --no-interactive, --persona, --repo, --section; args: - | - |  |
| `specfact project locks` | nold-ai/specfact-project | --bundle, --no-interactive, --repo; args: - | - |  |
| `specfact project merge` | nold-ai/specfact-project | --base, --bundle, --no-interactive, --ours, --out, --output, --persona-ours, --persona-theirs, --repo, --strategy, --theirs; args: - | - |  |
| `specfact project regenerate` | nold-ai/specfact-project | --bundle, --no-interactive, --project-name, --repo, --strict, --verbose; args: - | - |  |
| `specfact project resolve-conflict` | nold-ai/specfact-project | --bundle, --no-interactive, --path, --persona, --repo, --resolution; args: - | - |  |
| `specfact project snapshot` | nold-ai/specfact-project | --bundle, --no-interactive, --output, --project-name, --repo; args: - | - |  |
| `specfact project sync` | nold-ai/specfact-project | -; args: - | bridge, intelligent, repository |  |
| `specfact project sync bridge` | nold-ai/specfact-project | --adapter, --add-progress-comment, --ado-base-url, --ado-org, --ado-project, --ado-token, --ado-work-item-type, --all, --backlog-ids, --backlog-ids-file, --bidirectional, --bundle, --change-ids, --code-repo, --ensure-compliance, --export-to-tmp, --external-base-path, --feature, --github-token, --import-from-tmp, --include-archived, --interactive, --interval, --mode, --no-add-progress-comment, --no-gh-cli, --no-include-archived, --no-sanitize, --no-track-code-changes, --no-update-existing, --overwrite, --repo, --repo-name, --repo-owner, --sanitize, --target-repo, --tmp-file, --track-code-changes, --update-existing, --use-gh-cli, --watch; args: - | - |  |
| `specfact project sync intelligent` | nold-ai/specfact-project | --code-to-spec, --repo, --spec-to-code, --tests, --watch; args: - | - |  |
| `specfact project sync repository` | nold-ai/specfact-project | --confidence, --interval, --repo, --target, --watch; args: - | - |  |
| `specfact project unlock` | nold-ai/specfact-project | --bundle, --no-interactive, --repo, --section; args: - | - |  |
| `specfact project version` | nold-ai/specfact-project | -; args: - | bump, check, set |  |
| `specfact project version bump` | nold-ai/specfact-project | --bundle, --repo, --type; args: - | - |  |
| `specfact project version check` | nold-ai/specfact-project | --bundle, --repo; args: - | - |  |
| `specfact project version set` | nold-ai/specfact-project | --bundle, --repo, --version; args: - | - |  |
| `specfact spec` | nold-ai/specfact-spec | --install-completion, --show-completion; args: - | backward-compat, generate-tests, mock, validate |  |
| `specfact spec backward-compat` | nold-ai/specfact-spec | -; args: - | - |  |
| `specfact spec generate-tests` | nold-ai/specfact-spec | --bundle, --force, --out, --output; args: - | - |  |
| `specfact spec mock` | nold-ai/specfact-spec | --bundle, --examples, --no-interactive, --port, --spec, --strict; args: - | - |  |
| `specfact spec validate` | nold-ai/specfact-spec | --bundle, --force, --no-interactive, --previous; args: - | - |  |
| `specfact upgrade` | core | --check-only, --install-completion, --show-completion, --yes; args: - | - |  |
