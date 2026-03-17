# Design: Reward Ledger

## Supabase Schema

The reviewed SQL source is stored with the bundle at
`packages/specfact-code-review/src/specfact_code_review/resources/supabase/review_ledger_ddl.sql`
so the module owns its own persistence setup artifact.

```sql
CREATE TABLE ai_sync.review_runs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      text NOT NULL,
    issue_number    int,
    agent           text DEFAULT 'claude-code',
    changed_files   text[],
    score           int NOT NULL,
    reward_delta    int NOT NULL,
    verdict         text NOT NULL,  -- PASS | PASS_WITH_ADVISORY | FAIL
    findings_json   jsonb,
    house_rules_ver int DEFAULT 1,
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE ai_sync.reward_ledger (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent           text NOT NULL,
    session_id      text,
    cumulative_coins numeric(10,2) DEFAULT 0,
    last_delta      int,
    last_verdict    text,
    streak_pass     int DEFAULT 0,
    streak_block    int DEFAULT 0,
    updated_at      timestamptz DEFAULT now()
);
```

## LedgerClient Architecture

```python
class LedgerClient:
    def __init__(self):
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._local_path = Path.home() / ".specfact" / "ledger.json"

    @require(lambda self, report: isinstance(report, ReviewReport))
    @beartype
    def record_run(self, report: ReviewReport) -> None:
        if self._supabase_url:
            self._record_to_supabase(report)
        else:
            self._record_to_local(report)

    def _compute_coin_delta(self, report: ReviewReport) -> float:
        base = report.reward_delta / 10.0
        # streak bonuses applied after ledger state update
        return base
```

## Coin Update Logic

```python
def update_ledger_state(current: LedgerState, report: ReviewReport) -> LedgerState:
    if report.overall_verdict == "FAIL":
        new_streak_pass = 0
        new_streak_block = current.streak_block + 1
    else:
        new_streak_pass = current.streak_pass + 1
        new_streak_block = 0

    delta = report.reward_delta / 10.0
    if new_streak_pass >= 5:
        delta += 0.5  # consistency bonus
    if new_streak_block >= 3:
        delta -= 1.0  # regression penalty

    return LedgerState(
        cumulative_coins=current.cumulative_coins + delta,
        streak_pass=new_streak_pass,
        streak_block=new_streak_block,
        last_delta=report.reward_delta,
        last_verdict=report.overall_verdict,
    )
```

## Local JSON Fallback Structure

```json
{
  "agent": "claude-code",
  "cumulative_coins": 12.5,
  "streak_pass": 3,
  "streak_block": 0,
  "last_verdict": "PASS",
  "runs": [
    {"session_id": "...", "score": 85, "reward_delta": 5, "verdict": "PASS", "created_at": "..."}
  ]
}
```
