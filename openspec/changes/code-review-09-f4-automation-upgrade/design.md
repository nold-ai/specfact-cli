# Design: F-4 Automation Upgrade

## n8n F-4 Workflow Changes

### Before (current)
```
[F-4: Code Review]
  → Run Codex Review (generic)
  → Parse codex output (custom parser)
  → Branch: pass/fail
```

### After (new)
```
[F-4: Code Review]
  → Run specfact code review run --json (changed files)
  → Parse ReviewReport JSON (SP-001 models)
  → Branch: PASS / PASS_WITH_ADVISORY / FAIL
  → [always] Update Reward Ledger (pipe to ledger update)
  → [FAIL branch] Notify human, stop workflow
  → [PASS/WARN branch] Run specfact code review run --fix (if WARN)
  → Continue to commit
```

## n8n Node Replacement Pseudocode

```javascript
// Node: Run specfact code review
const changedFiles = $input.item.json.changed_files.join(" ");
const result = await $helpers.executeCommand(
  `specfact code review run --json ${changedFiles}`
);
const report = JSON.parse(result.stdout);

// Route based on verdict
if (report.overall_verdict === "FAIL") {
  return { verdict: "BLOCK", report };
} else if (report.overall_verdict === "PASS_WITH_ADVISORY") {
  return { verdict: "WARN", report };
} else {
  return { verdict: "PASS", report };
}
```

## F-2 house_rules Injection

At container startup (before coding session begins):
```javascript
const skillPath = process.env.SKILLS_DIR + "/specfact-code-review/SKILL.md";
let houseRules = "";
if (fs.existsSync(skillPath)) {
  // Extract Markdown body (after YAML frontmatter)
  const content = fs.readFileSync(skillPath, "utf-8");
  houseRules = content.split("---").slice(2).join("---").trim();
  if (houseRules.length > 2000) {
    houseRules = houseRules.substring(0, 2000);
  }
}
process.env.HOUSE_RULES = houseRules;
```

Stage 5 stdin JSON:
```json
{
  "context": {
    "house_rules": "<HOUSE_RULES content>",
    "issue_number": 123,
    "session_id": "abc123"
  }
}
```

## Stage 6 Pre-Commit Gate (coding-workflow.js)

```javascript
// Stage 6: Pre-commit gate
const changedFiles = getChangedFiles();  // git diff --name-only
const gateResult = await runCommand(
  `specfact code review run --score-only ${changedFiles.join(" ")}`
);

if (gateResult.exitCode === 1) {
  // BLOCK — do not commit
  await fireCallback("REVIEW_BLOCKED", {
    session_id: sessionId,
    score: parseInt(gateResult.stdout.trim()),
    changed_files: changedFiles,
  });
  process.exit(1);
}
// PASS or WARN (exit code 0) — proceed with commit
await runGitCommit(...);
```

## Open Questions (tracked)

1. Confirm `crosshair` is in `specfact-coding-worker` Docker image
2. Confirm Supabase service role key covers new `review_runs` and `reward_ledger` tables
3. Define max concurrent `specfact code review run` processes per VPS run (semgrep + crosshair are CPU-heavy)
4. Confirm `codex` CLI is fully replaced (not parallel) — current plan: full replacement
