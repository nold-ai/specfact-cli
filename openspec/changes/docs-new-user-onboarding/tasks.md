## 1. Investigate and locate bug roots

- [x] 1.1 Find where `specfact init --profile <name>` is handled in the init module source
       and confirm it is NOT calling the module installer (Bug 1 root cause)
- [x] 1.2 Find the module installer path and confirm why it fails under uvx
       ("No module named pip") — identify whether the fix is in the installer or in how
       uvx-bundled environments should be detected (Bug 2 root cause)
- [x] 1.3 Find the canonical profile → bundle mapping definition and confirm it does not
       include `specfact-code-review` for `solo-developer` (Bug 3 root cause)
- [x] 1.4 Find the `code review run --path .` error path and confirm it does not suggest
       `--scope full` as the corrective action (Bug 4 root cause)
- [x] 1.5 Record baseline failing test evidence in `TDD_EVIDENCE.md`:
       - run `specfact init --profile solo-developer` → confirm no modules installed
       - run `specfact code review run --path . --scope full` → confirm "Command not installed"
       - run `specfact module install nold-ai/specfact-code-review` under uvx → confirm pip error
       - run `specfact code review run --path .` → confirm unhelpful git-diff error
       *(superseded by post-fix evidence in `TDD_EVIDENCE.md`)*

## 2. Fix `init --profile` module installation (Bug 1)

- [x] 2.1 Write failing test: `init --profile solo-developer` installs `specfact-codebase`
       and `specfact-code-review` and they appear in `module list` output
- [x] 2.2 Implement fix: `init --profile` MUST call `module install` for each bundle in the
       profile's canonical set after runtime bootstrap
- [x] 2.3 Ensure `init` outputs a confirmation line per installed bundle:
       "Installed: specfact-codebase, specfact-code-review"
- [x] 2.4 Ensure `init --profile` does NOT report "Bootstrap complete" until all bundles
       are installed and their commands are registered

## 3. Fix module install under uvx (Bug 2)

- [x] 3.1 Write failing test: `specfact module install nold-ai/specfact-code-review` in a
       uvx-isolated environment succeeds (does not require pip)
- [x] 3.2 Implement fix: module installation SHALL use a pip-free path when running under uvx
       (use bundled package artifacts or uv-native install, not `pip install`)
- [ ] 3.3 Verify `module install` succeeds in a clean uvx context with no user-level pip
       *(manual / CI smoke; not automated in this repo)*

## 4. Add `specfact-code-review` to `solo-developer` profile (Bug 3)

- [x] 4.1 Write failing test: `solo-developer` profile canonical set includes both
       `specfact-codebase` and `specfact-code-review`
- [x] 4.2 Update the profile canonical bundle mapping to add `specfact-code-review` to
       `solo-developer`
- [ ] 4.3 Verify end-to-end: after `specfact init --profile solo-developer`, running
       `specfact code review run --path . --scope full` in a git repo produces a scored result
       *(manual verification after PR; requires marketplace modules)*

## 5. Fix `code review run --path .` scope error (Bug 4)

**Note:** `code review run` is implemented in the **specfact-code-review** module (`nold-ai/specfact-cli-modules`); scope/diff behaviour should be fixed there. Docs now steer users to `--scope full` on the uvx path.

- [ ] 5.1 Write failing test: running `specfact code review run --path .` in a git repo with
       no staged changes produces an error that includes `--scope full` as the corrective command
- [ ] 5.2 Implement fix: either (a) default to `--scope full` when no git diff is available,
       OR (b) emit a specific error: "No changed files detected. Run with `--scope full` to
       review all tracked files."
- [ ] 5.3 Verify the error or default behaviour is consistent between uvx and pip-installed CLI

## 6. Improve module-not-found error message (UX)

- [x] 6.1 Write failing test: running `uvx specfact-cli code review run` with no modules
       installed produces an error that includes `uvx specfact-cli init --profile solo-developer`
- [x] 6.2 Implement fix: the module-not-found error for command groups SHALL include a
       copy-pasteable init command, not just the generic "install workflow bundles" message
- [x] 6.3 Verify the message is correct for both uvx and pip-installed CLI contexts

## 7. Run pre-docs TDD gate

- [ ] 7.1 Run `hatch run contract-test` — confirm passing *(run before PR merge)*
- [ ] 7.2 Run `hatch run smart-test` — confirm passing *(run before PR merge)*
- [x] 7.3 Run `hatch run format` and `hatch run type-check` — confirm zero errors
- [x] 7.4 Record post-fix passing evidence in `TDD_EVIDENCE.md`
- [ ] 7.5 End-to-end manual test on a clean machine: `uvx specfact-cli init --profile solo-developer`
       then `uvx specfact-cli code review run --path . --scope full` → confirm scored output

## 7b. Fix `module upgrade` output and add selective + breaking-change gate

- [x] 7b.1 Write failing test: `module upgrade` when all modules are at latest version outputs
       "All modules are up to date" and contains no `X -> X` lines
- [x] 7b.2 Write failing test: `module upgrade` when one module has a newer minor version shows
       it in "Upgraded:" and unchanged modules in "Already up to date:"
- [x] 7b.3 Write failing test: `module upgrade backlog codebase` upgrades only those two modules
- [x] 7b.4 Write failing test: major version bump (0.x → 1.x) in interactive mode prompts the
       user; declining skips the module; accepting upgrades it
- [x] 7b.5 Write failing test: major version bump with `--yes` upgrades without prompting
- [x] 7b.6 Write failing test: major version bump in CI/CD mode is skipped with a warning,
       exit 0 when remaining non-major modules succeed
- [x] 7b.7 Change `upgrade` Argument from `module_name: str | None` to `module_names: list[str]`
       with `typer.Argument(default=[])`; update `_upgrade_module_name_optional` guard;
       empty list = upgrade all (existing `--all` behaviour remains as alias)
- [x] 7b.8 Update `_resolve_upgrade_target_ids` to accept a list of names
- [x] 7b.9 Before calling `install_module`, look up `latest_version` from registry index;
       skip reinstall when `latest_version == current_version` (populate `up_to_date` list)
- [x] 7b.10 Add semver major-bump detection: if `int(latest.split('.')[0]) > int(current.split('.')[0])`,
        gate on `--yes` flag or interactive prompt; auto-skip in CI/CD mode with warning
- [x] 7b.11 Add `--yes` / `-y` flag to `upgrade` command for non-interactive major-bump approval
- [x] 7b.12 Update output sections: "Upgraded:", "Already up to date:", "Skipped (major bump):"
- [ ] 7b.13 Verify end-to-end: `module upgrade` with current modules → "All modules are up to date"
       *(manual smoke with real marketplace modules)*

## 7c. Multi-module install and uninstall

- [x] 7c.1 Write failing test: `specfact module install A B` installs both A and B
- [x] 7c.2 Write failing test: `specfact module install A B` where A is already installed —
       skips A, installs B, exits 0
- [x] 7c.3 Change `install` Argument from `module_id: str` to `module_ids: list[str]`;
       update `@require` guard; loop through each id using existing install logic
- [x] 7c.4 Exit non-zero only if at least one module failed (not if skipped/already installed)
- [x] 7c.5 Verify: single-module install still works identically; all existing flags apply
- [x] 7c.6 Write failing test: `specfact module uninstall A B` uninstalls both A and B
- [x] 7c.7 Write failing test: `specfact module uninstall A B` where A is not installed —
       reports A not found, still attempts B, exits non-zero
       *(Catches `click.exceptions.Exit` from `typer.Exit`; upgrade uses `Optional[list[str]]` for Click 8.1 + Typer 0.23.)*
- [x] 7c.8 Change `uninstall` Argument from `module_name: str` to `module_names: list[str]`;
       update `@require` guard; loop through each name using existing uninstall logic
- [x] 7c.9 Verify: single-module uninstall still works identically; `--scope`/`--repo` apply

## 7d. Version-aware bundle dependency resolution

- [ ] 7d.1 Write failing test: installing a module whose `bundle_dependencies` lists a module
       not installed prompts the user and installs the dep on confirmation
- [ ] 7d.2 Write failing test: installing a module whose declared dep version specifier is
       not satisfied by the installed version prompts to upgrade, aborts on decline
- [ ] 7d.3 Write failing test: dep already satisfies specifier — no prompt, INFO log only
- [ ] 7d.4 Write failing test: `module install A --yes` auto-installs/upgrades all unmet deps
- [ ] 7d.5 Write failing test: CI/CD mode with unmet dep exits non-zero without silent install
- [ ] 7d.6 Write failing test: `module install A --dry-run` prints plan and exits 0 with no changes
- [ ] 7d.7 Write failing test: circular dep A→B→A is detected and aborts with clear message
- [ ] 7d.8 Write failing test: upgrade re-evaluates new version's deps; prompts if new dep
       requirements are introduced or tightened
- [x] 7d.9 Write failing test: `core_compatibility` mismatch prints version, required range,
       and corrective command — not a bare exception
- [x] 7d.10 Extend registry index parser: `_extract_bundle_dependencies` SHALL handle both
        plain string entries and `{"id": "...", "version": "..."}` object entries; return
        `list[tuple[str, str | None]]` (module_id, version_specifier_or_None)
- [ ] 7d.11 Add `resolve_module_dependencies(targets, installed_modules, registry_index)` to
        `dependency_resolver.py`: for each dep, check if installed and if version satisfies
        specifier; return `ResolutionPlan(to_install, to_upgrade, satisfied, conflicts)`
- [ ] 7d.12 Add circular dependency detection to `resolve_module_dependencies` using a
        visited-set DFS over the dependency graph
- [x] 7d.13 Add `--yes` flag to `install` and `upgrade` commands (if not already added in 7b.11)
        to enable non-interactive auto-resolution *(upgrade has `--yes`; install dep auto-resolve: TBD)*
- [ ] 7d.14 Add `--dry-run` flag to `install` and `upgrade`; print `ResolutionPlan` and exit 0
- [ ] 7d.15 Wire `resolve_module_dependencies` into `_install_bundle_dependencies_for_module`:
        call it before any install; prompt user for each `to_install` / `to_upgrade` entry;
        auto-resolve if `--yes`; abort if user declines or CI mode and deps unmet
- [ ] 7d.16 Wire dep re-evaluation into `_run_marketplace_upgrades`: after fetching new version
        manifest, call `resolve_module_dependencies` before placing the upgraded module
- [x] 7d.17 Replace the bare `ValueError("Module is incompatible with current SpecFact CLI version")`
        in `module_installer.py:726` with a structured message:
        `"<module> requires SpecFact CLI <range> but you have <version>. Run: specfact upgrade"`
- [ ] 7d.18 Update `registry/index.json` in specfact-cli-modules to use versioned
        `bundle_dependencies` objects where constraints exist (e.g. specfact-codebase → project)
- [ ] 7d.19 Run full contract-test and smart-test suite; confirm no regressions

## 8. Homepage Rewrite (`docs/index.md`)

- [x] 8.1 Replace the opening paragraph with a plain-language outcome-first hero statement
       ("Point it at your code. Get a score and a list of what to fix.")
- [x] 8.2 Add inline 2-command uvx fenced code block immediately after the hero:
       `uvx specfact-cli init --profile solo-developer` +
       `uvx specfact-cli code review run --path . --scope full`
- [x] 8.3 Add a description of the expected output adjacent to the block
       (e.g. "You'll see: Verdict: FAIL | Score: 0 | 64 findings")
- [x] 8.4 Add "Read the full quickstart →" link adjacent to the block
- [x] 8.5 Replace the 4-card "Choose Your Path" section with 3 outcome-oriented cards:
       "See what's wrong with your code right now" /
       "Set up IDE slash-command workflows" /
       "Add a pre-commit or CI gate"
- [x] 8.6 Rewrite the "Core Platform" section — remove the jargon bullet; keep init/module/upgrade
- [x] 8.7 Verify: no architectural jargon terms above the fold before path cards
- [x] 8.8 Verify: all existing Architecture/Reference/Migration section links still resolve

## 9. Installation Page Restructure (`docs/getting-started/installation.md`)

- [x] 9.1 Add "## Try it now — no install required" as the first H2, showing the uvx 2-command
       sequence with expected output description
- [x] 9.2 Add "## Install for persistent use" as the next H2 (pip path)
- [x] 9.3 Move Container and GitHub Action options to "## More options" section
- [x] 9.4 Remove the "Limitations" warning from the uvx section
- [x] 9.5 Move "Operational Modes", "Installed Command Topology", and profile table below
       "More options"
       *(Under `## First Steps`, immediately after Container/GitHub Action.)*
- [x] 9.6 Add visible anchor link "More options ↓" after the pip section
- [x] 9.7 Verify: front-matter unchanged; no broken links

## 10. Quickstart Reframe (`docs/getting-started/quickstart.md`)

- [x] 10.1 Rewrite the intro so it leads with the uvx path and the vibe-coder audience
- [x] 10.2 Ensure Step 1 is the uvx init command, not pip install
- [x] 10.3 Verify: front-matter, redirect_from, and all 6 steps are intact

## 11. Spec Sync

- [x] 11.0 GitHub backlog: issue [#476](https://github.com/nold-ai/specfact-cli/issues/476) with labels `enhancement`, `change-proposal`, `documentation`, `openspec`; parent feature [#356](https://github.com/nold-ai/specfact-cli/issues/356); related [#466](https://github.com/nold-ai/specfact-cli/issues/466) — `proposal.md` Source Tracking updated
- [ ] 11.1 Run `openspec sync --change docs-new-user-onboarding` to merge all 10 spec deltas
       *(blocked: OpenSpec CLI in this environment has no `sync` subcommand — use project workflow when available)*
- [ ] 11.2 Confirm `openspec/specs/docs-aha-moment-entry/spec.md` created
- [ ] 11.3 Confirm `openspec/specs/docs-vibecoder-entry-path/spec.md` created
- [ ] 11.4 Confirm `openspec/specs/dependency-resolution/spec.md` created
- [ ] 11.5 Confirm MODIFIED requirements in `entrypoint-onboarding`, `first-contact-story`,
       `first-run-selection`, `profile-presets`, and `module-installation` specs are updated

## 12. Final Validation and Evidence

- [ ] 12.1 Run `hatch run yaml-lint` — confirm zero failures *(before PR)*
- [ ] 12.2 Run `hatch run contract-test` — confirm passing *(before PR)*
- [ ] 12.3 Run `hatch run specfact code review run --json --out .specfact/code-review.json`
       and confirm zero findings on modified Python files *(before PR)*
- [ ] 12.4 Build docs locally (`bundle exec jekyll serve`) and manually verify:
       homepage hero + code block, 3 path cards, installation uvx-first, quickstart uvx-led
- [ ] 12.5 Manual end-to-end on a clean machine: full uvx wow path works in under 15 seconds
- [x] 12.6 Record final passing evidence in `TDD_EVIDENCE.md`
- [x] 12.7 Update `openspec/CHANGE_ORDER.md` with this change entry

## 13. PR and Cleanup

- [ ] 13.1 Create feature branch `feature/docs-new-user-onboarding` from `origin/dev`
- [ ] 13.2 Commit CLI fixes: `fix: init --profile installs profile modules, fix module-install under uvx`
- [ ] 13.3 Commit docs: `docs: vibe-coder entry path — uvx hero, code review wow moment`
- [ ] 13.4 Open PR against `dev` referencing this change and the three CLI bugs fixed
- [ ] 13.5 After merge, archive: `openspec archive docs-new-user-onboarding`
