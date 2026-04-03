## Context

docs.specfact.io is a Jekyll static site (GitHub Pages). Source: `docs/`, front-matter required
on every page. Homepage is `docs/index.md`. Sidebar navigation in `docs/_layouts/default.html`.

Two distinct user cohorts arrive at the docs:
- **Vibe coders**: non-Python-expert, heard "validate your vibe code", want results in seconds,
  will not read installation guides. Their mental model: run one command, see something useful.
- **Experienced developers**: understand pip, virtual envs, module systems. Current docs already
  work for this group. They are NOT the audience being lost.

Testing confirms the real vibe-coder "wow" sequence:
```bash
uvx specfact-cli init --profile solo-developer           # ~5 seconds, user-level module install
uvx specfact-cli code review run --path . --scope full   # ~4 seconds, scored review output
```
Total time to first result: ~10 seconds, zero pip install, zero virtual environment.

This sequence works because `uvx specfact-cli init` installs modules at user level, and
subsequent `uvx specfact-cli` invocations detect and use them.

**Friction points identified through direct testing:**
1. Running `uvx specfact-cli code review run --path .` without `--scope full` gives a confusing
   git-diff error ("Unable to determine changed tracked files"). Vibe coders will stop here.
2. Running `uvx specfact-cli code review run` without init gives "Command 'code' is not installed"
   — acceptable message but the fix ("specfact init --profile <profile>") uses jargon.
3. The `code review run` command is not mentioned anywhere on the homepage.
4. The uvx path on the installation page is labelled "CLI-only Mode" and immediately warns about
   "limited results" — this actively discourages the primary vibe-coder path.

This is a docs change plus a minor CLI UX improvement (error message and `--scope` default).

## Goals / Non-Goals

**Goals:**
- Homepage leads with the 2-command vibe-coder sequence and names `code review run` explicitly
- uvx is the hero install method; pip is secondary for users who want a persistent installation
- "Command 'code' is not installed" error tells the user the exact init command to run
- `code review run --path .` works without requiring the user to know about `--scope full`
  (either by defaulting to full scope when git diff is unavailable, or with a helpful inline hint)
- 3 action-oriented path cards; no persona or product-dimension labels
- Progressive disclosure: vibe coder hits wow in 10 seconds, then finds depth if curious
- All current advanced content remains — just reordered

**Non-Goals:**
- Redesigning the Jekyll theme or sidebar
- Adding new CLI commands beyond a minor error-message improvement
- Rewriting modules.specfact.io
- Changing any URL permalink
- Explaining what "contracts", "icontract", or "beartype" mean on entry-level pages

## Decisions

**Decision 1: uvx as hero path, not "Option 1 with limitations"**

The current framing "CLI-only Mode (uvx) — Limitations: may show limited results" actively
discourages the exact path vibe coders need. The `code review run` command produces full output
via uvx (all tools: ruff, radon, semgrep, basedpyright, pylint, contracts). The "limitations"
note referred to early-stage behaviour that no longer applies.

Replacement: uvx is the first thing a new visitor sees on the installation page, labelled
"Try it now — no install required". pip is presented below as "Install for persistent use".

**Decision 2: 2-command hero block on homepage, not a 4-command "quickstart"**

The previous proposal embedded a 4-command block (pip install → init → code import → repro).
For a vibe coder, `code import` and `repro` are unknown commands. The new block is 2 commands:
init → code review run. The output (score + findings) is described inline so the user knows
what they'll see before they run it.

**Decision 3: `--scope full` guidance — docs fix, CLI default as stretch goal**

The confusing git-diff error when running `code review run --path .` needs to be fixed.
Primary approach: document the correct invocation clearly and consistently as
`code review run --path . --scope full`. Stretch goal: if the CLI can default to full scope
when not in a git repo or when no diff is available, that is a small quality-of-life win worth
a separate one-line fix in `review_run_command` — but it is not blocking this change.

**Decision 4: Module-not-found error message improvement is in scope**

The error "Command 'code' is not installed. Install workflow bundles with specfact init
--profile <profile>..." is technically correct but uses jargon. Change: add the literal command
`uvx specfact-cli init --profile solo-developer` as the suggested fix when running via uvx,
alongside the generic message. This is a minor string change in the registry/bootstrap error path.

**Decision 5: Path cards — 3 outcome cards ordered by frequency of first intent**

1. "See what's wrong with your code right now" (code review run — the vibe-coder path)
2. "Set up IDE slash-command workflows" (init ide — the power-user path)
3. "Add a pre-commit or CI gate" (repro / GitHub Action — the team path)

The old Greenfield/Brownfield/Backlog/Team taxonomy maps to internal product dimensions, not to
user intents at first contact. Users can be routed to those dimensions from within the cards.

## Risks / Trade-offs

[Risk]: Reordering uvx above pip on the installation page may confuse Python developers who
expect pip as the standard install path.
→ Mitigation: pip section remains immediately after uvx with a clear "For persistent installation"
label. No content is removed.

[Risk]: Improving the module-not-found error message touches production CLI code.
→ Mitigation: it is a string change in the error output path, no logic change. If it misses this
PR it can ship as a tiny follow-up fix; the docs improvement is independent.

[Risk]: "See what's wrong with your code right now" as the primary card might create
expectations that the tool is AI-powered.
→ Mitigation: the card body clarifies "deterministic analysis: naming, complexity, contracts,
types — no AI, no cloud" so the expectation is set correctly.

## Migration Plan

1. Update `docs/index.md`: hero + 2-command uvx block + 3 cards + reordered sections
2. Update `docs/getting-started/installation.md`: uvx hero → pip secondary → other options
3. Update `docs/getting-started/quickstart.md`: reframe opening, lead with uvx path
4. (Minor CLI) Improve module-not-found error message in registry bootstrap error path
5. No URL changes, no redirects needed
6. Local build: `bundle exec jekyll serve` — verify rendering
7. PR to `dev` branch

## Open Questions

- Should `code review run --path .` default to `--scope full` when a git diff is unavailable,
  or show an inline help hint? Decision deferred to implementer — either fix is acceptable.
  The docs MUST document `--scope full` explicitly regardless.
