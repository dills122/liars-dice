# Relegation League System — Design Spec

## Overview

Replace the current single-tier admission model with a three-tier promotion/relegation pyramid inspired by European football leagues. New players are admitted to the system via pull request, placed in a tier based on their performance, and can move up or down over time through a deferred promotion/relegation mechanism triggered on every PR.

---

## Leagues

Three named tiers plus an inactive holding state:

| Tier | Name | Abbreviation |
|---|---|---|
| 1 | Premier Division | PRM |
| 2 | Championship | CH |
| 3 | League One | L1 |
| — | Inactive | inactive |

Each active league holds a maximum of **TOP_N** players (configured as a GitHub repository variable). `inactive` has no cap — it is a holding tier for players who have been hard-capped out of L1. Player files are never deleted; stats are always preserved.

---

## Phase Detection

The system determines which leagues are active based on the total number of players currently in the system (across all tiers including inactive). This is evaluated at the start of every workflow run, after pending relegations are applied.

| Total players | Challenger enters | Active leagues |
|---|---|---|
| < TOP_N | PRM | PRM only |
| > TOP_N and ≤ TOP_N×2 | CH | PRM + CH |
| > TOP_N×2 | CH | PRM + CH + L1 |

New challengers never enter L1 directly. L1 is populated exclusively by CH relegations.

**Phase 2 edge case:** If CH has fewer than 2 players (not enough for a meaningful run), the challenger is admitted to CH automatically without a run. PRM still runs to determine the deferred relegation that will populate CH next PR.

---

## PR Rules

- Every PR must contain exactly one new player file in `players/`
- PRs always merge — tier placement is the outcome, not pass/fail
- The challenger's finishing position in their run determines which tier they land in
- One player file per PR is enforced by the workflow (PR fails with an explanatory comment if multiple files are detected)

---

## Cascade Execution

### Step 0: Apply Pending Relegation

At the start of every workflow run, all entries in `pending_relegation` from `leaderboard.yaml` are applied: players are moved to their new tier. They compete in their new tier starting with this run.

### Step 1: CH Run (always, Phase 2/3)

Players: existing CH players + challenger.

| Result | Outcome |
|---|---|
| CH winner | Promoted to PRM immediately; triggers Step 2 |
| Challenger finishes last (Phase 3 only) | Placed directly in L1 (skips CH) |
| Challenger not last | Admitted to CH |
| CH bottom (non-challenger) | `pending_relegation` → L1 |

If the challenger wins CH, they are the promotion candidate for PRM. They do not stay in CH.

**Phase 2 note:** CH is never at full capacity in Phase 2 (total players ≤ TOP_N×2, PRM holds TOP_N, so CH has fewer than TOP_N). The challenger is always admitted to CH in Phase 2 regardless of finishing position. The "last place → L1" rule only applies in Phase 3 when CH is full.

**Same-PR competition rule:** A player whose tier changes during a PR run (challenger placed into L1, player promoted to PRM) does not compete in their new tier's run that same PR. They begin competing in their new tier on the next PR.

### Step 2: PRM Run (parallel-eligible, runs if CH produced a promotion)

Players: existing PRM players.

| Result | Outcome |
|---|---|
| PRM bottom | `pending_relegation` → CH |

Runs in parallel with Step 3 when both are triggered.

### Step 3: L1 Run (parallel-eligible, Phase 3 only, if pending L1 relegation exists)

Players: existing L1 players + **all inactive players**.

| Result | Outcome |
|---|---|
| Overall winner | Promoted to CH immediately |
| L1 bottom | `pending_relegation` → inactive |
| All inactive competitors | Stats updated regardless of finish position |

All inactive players compete in every L1 run. Their cumulative stats (`total_wins`, `total_games`, `win_pct`) update from each run, causing the inactive pool to self-sort over time — consistently weak algorithms naturally fall in the rankings.

`times_last_in_l1` is incremented for any player (L1 or inactive) that finishes last in an L1 run.

---

## Deferred Relegation

- Relegated players move to their new tier **immediately** in `leaderboard.yaml` but do not compete until the next PR's run
- Pending changes are stored in the `pending_relegation` list and applied at Step 0 of the next run
- Promotions are **immediate** — the promoted player competes in their new league starting next PR (no deferred promotion)
- A player can only have one pending relegation at a time

---

## Data Model

### `leaderboard.yaml`

```yaml
total_runs: 14
last_updated: '2026-06-08T00:00:00Z'
pending_relegation:
  - player: Alice
    from_tier: CH
    to_tier: L1
players:
  Diego:
    date_added: '2026-05-22T16:10:13Z'
    total_wins: 300
    total_games: 500
    win_pct: 60.0
    tier: PRM
    tier_since: '2026-05-22T16:10:13Z'
    times_last_in_l1: 0
  Alice:
    date_added: '2026-05-22T15:47:31Z'
    total_wins: 88
    total_games: 200
    win_pct: 44.0
    tier: CH
    tier_since: '2026-06-01T10:00:00Z'
    times_last_in_l1: 1
```

**Field changes from current schema:**
- `is_active: bool` → `tier: PRM | CH | L1 | inactive`
- `date_added` retained (original admission date)
- `tier_since` added (date of most recent tier change)
- `times_last_in_l1` added (count of last-place finishes in L1 runs)

---

## Game Engine Changes

### `__main__.py`

- Add `--tier` CLI argument (e.g. `python -m game --tier CH 500 6`)
- When `--tier` is provided, player selection filters to that tier only (plus inactive players when `--tier L1`)
- Existing positional arguments `N_GAMES` and `TOP_N` unchanged

### `leaderboard.py`

Rewrite `update_leaderboard` to:
- Accept `tier` (which league ran), `competing_players` (list of names in this run), and `results` (dict of name → wins)
- Update stats only for players who competed in this run
- Accept explicit `promotions` and `relegations` dicts from the workflow (tier logic lives in workflow, not here)
- Write `pending_relegation` entries for relegated players
- Update `times_last_in_l1` for the last-place finisher when `tier == L1`
- Leave players not in this run's roster untouched

---

## Workflow Structure

Four GitHub Actions jobs replacing the current single job:

```
setup
  ├─ Validates exactly 1 new player file in the PR
  ├─ Applies pending_relegation from leaderboard.yaml
  ├─ Detects phase and challenger entry tier
  └─ Outputs: phase, rosters per league, pending_l1_relegation flag

run-ch
  ├─ needs: setup
  ├─ Runs: uv run python -m game --tier CH $N_GAMES $TOP_N
  └─ Outputs: winner, last_place, challenger_result, game_output artifact

run-prm
  ├─ needs: run-ch
  ├─ if: run-ch outputs ch_promoted == true
  ├─ Runs: uv run python -m game --tier PRM $N_GAMES $TOP_N
  └─ Outputs: last_place, game_output artifact

run-l1
  ├─ needs: setup
  ├─ if: setup outputs phase == 3 AND pending_l1_relegation == true
  ├─ Runs: uv run python -m game --tier L1 $N_GAMES $TOP_N
  │   (L1 player selection includes all inactive automatically)
  └─ Outputs: winner, last_place, game_output artifact

evaluate
  ├─ needs: [run-ch, run-prm, run-l1] (all optional except run-ch)
  ├─ Reads all game_output artifacts
  ├─ Writes updated leaderboard.yaml (stats + tier changes + new pending_relegation)
  ├─ Commits leaderboard.yaml to PR branch
  ├─ Posts PR comment (see Comment Format below)
  └─ Triggers auto-merge (always)
```

`run-prm` and `run-l1` are independent and run in parallel when both are triggered.

League results (winner/loser names) are passed between jobs via GitHub Actions job outputs. Full game output text is passed via artifacts and consumed by `evaluate` for the PR comment.

---

## PR Comment Format

Every PR comment includes:

1. **Challenger result** — plain English: which tier they landed in and why
2. **Per-league results** — one `<details>` block per league that ran, containing the `format_results` table
3. **Full leaderboard** — all players across all tiers, grouped by tier, showing `win_pct`, `total_games`, `tier_since`
4. **Pending changes** — who is pending relegation and to which tier (takes effect next PR)

Example summary line:
> **Bruno** admitted to Championship. Diego promoted to Premier Division. Alice pending relegation to League One (takes effect next PR).

---

## Tiebreaking

When two players finish with equal `win_pct` in a run, the tiebreaker is `total_games` descending (more games = more reliable record). If still tied, `tier_since` ascending (longer tenure in the tier wins).

---

## Out of Scope

- Scheduled league runs (all runs are PR-triggered)
- A 4th tier below inactive
- Multiple player files per PR
- Player file deletion

