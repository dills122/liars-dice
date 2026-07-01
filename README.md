# Liar's Dice League

A Python engine for running Liar's Dice games between algorithmic players. Players compete in a tiered league — submit a PR to join, and a weekly scheduled run plays the games and updates standings (extra runs trigger automatically when a player file changes).

_This project is based on the foundational work and initial implementation by [Zach Austin](https://github.com/zachaustin01)._

Interested in competing? **[Visit the Wiki](https://github.com/after2400/liars-dice/wiki)** — rules, player API, and how to submit a bot. For local dev setup see [CONTRIBUTING.md](CONTRIBUTING.md).

## Current Standings

<!-- prettier-ignore-start -->
<!-- leaderboard-start -->
### Premier
| Player | Season W% | Wins in PRM | Win % Total | Total Wins | Games |
|--------|-----------|----------------|-------------|------------|-------|
| The Merovingian | 20.7 | 466 | 31.7 | 1268 | 4000 |
| EvilStewie | 18.0 | 2194 | 18.0 | 2515 | 14000 |
| Deep Thought | 12.7 | 1863 | 15.5 | 1863 | 12000 |
| Stewie | 10.2 | 4280 | 18.3 | 4933 | 27000 |
| Peter Beter | 9.8 | 2173 | 16.4 | 2464 | 15000 |
| Peter Griffin | 7.7 | 2174 | 14.5 | 2174 | 15000 |
| Sloane | 7.5 | 3980 | 17.8 | 7661 | 43000 |
| Nuke LaLoosh | 7.2 | 3081 | 16.6 | 4154 | 25000 |

### Championship
| Player | Season W% | Wins in CH | Win % Total | Total Wins | Games |
|--------|-----------|----------------|-------------|------------|-------|
| Columbo | Relegated | 762 | 15.9 | 1271 | 8000 |
| Zara | 14.7 | 3919 | 18.6 | 6334 | 34000 |
| Cal Culatid | 14.5 | 2468 | 17.5 | 4032 | 23000 |
| Diego | 13.4 | 2538 | 17.6 | 6220 | 35350 |
| Eva | 12.5 | 5311 | 19.1 | 6689 | 35000 |
| Honest Abe | 11.1 | 2497 | 14.1 | 2970 | 21000 |
| Remy | 7.2 | 3606 | 17.2 | 8259 | 48000 |

### Level 1
| Player | Season W% | Wins in L1 | Win % Total | Total Wins | Games |
|--------|-----------|----------------|-------------|------------|-------|
| Finn | Relegated | 3730 | 16.9 | 6470 | 38250 |
| Meg Griffin | 16.5 | 450 | 11.2 | 450 | 4000 |
| Alice | 15.9 | 4145 | 15.7 | 5238 | 33450 |
| Rick Sanchez | 15.5 | 3368 | 16.8 | 3368 | 20000 |
| Bruno | 13.9 | 3123 | 12.6 | 4078 | 32450 |
| Topper | 5.9 | 2342 | 8.1 | 2342 | 29000 |
| Liar², Pants on Fire | 5.1 | 976 | 4.1 | 976 | 24000 |
| Cleo | 2.6 | 1686 | 5.1 | 1703 | 33450 |

### Quarter Leaderboard

| Player | Tier | PRM W% | CH W% | L1 W% | Total W% | Games |
|--------|------|--------|-------|-------|----------|-------|
| The Merovingian | Premier | 23.3 | 33.4 | 46.8 | 31.7 | 4000 |
| Zara | Championship | 20.1 | 17.8 | — | 18.6 | 34000 |
| Diego | Championship | 18.1 | 16.9 | — | 17.6 | 35350 |
| Eva | Championship | 17.2 | 19.7 | — | 19.1 | 35000 |
| Stewie | Premier | 17.1 | 36.5 | 28.8 | 18.3 | 27000 |
| EvilStewie | Premier | 16.9 | 32.1 | — | 18.0 | 14000 |
| Peter Beter | Premier | 15.5 | 29.1 | — | 16.4 | 15000 |
| Deep Thought | Premier | 15.5 | — | — | 15.5 | 12000 |
| Alice | Level 1 | 14.8 | 12.6 | 16.6 | 15.7 | 33450 |
| Sloane | Premier | 14.7 | 23.0 | — | 17.8 | 43000 |
| Peter Griffin | Premier | 14.5 | — | — | 14.5 | 15000 |
| Nuke LaLoosh | Premier | 14.0 | 27.6 | 52.1 | 16.6 | 25000 |
| Finn | Level 1 | 14.0 | 12.7 | 21.9 | 16.9 | 38250 |
| Cal Culatid | Championship | 12.8 | 17.6 | 26.5 | 17.5 | 23000 |
| Bruno | Level 1 | 10.9 | 13.8 | 12.5 | 12.6 | 32450 |
| Remy | Championship | 10.6 | 13.9 | 22.2 | 17.2 | 48000 |
| Columbo | Championship | 7.2 | 19.1 | 29.3 | 15.9 | 8000 |
| Cleo | Level 1 | 1.1 | 0.3 | 5.8 | 5.1 | 33450 |
| Honest Abe | Championship | — | 13.1 | 23.6 | 14.1 | 21000 |
| Rick Sanchez | Level 1 | — | — | 16.8 | 16.8 | 20000 |
| Meg Griffin | Level 1 | — | — | 11.2 | 11.2 | 4000 |
| Topper | Level 1 | — | — | 8.1 | 8.1 | 29000 |
| Liar², Pants on Fire | Level 1 | — | — | 4.1 | 4.1 | 24000 |

<!-- leaderboard-end -->
<!-- prettier-ignore-end -->

_Updated weekly (Mondays at 9am UTC) or whenever a player file is added/modified. Full history in the [season tracking issue](https://github.com/after2400/liars-dice/issues/4)._

---

## How It Works

Two workflows replace the old per-PR game model:

**`register-player.yml`** — triggered when a PR touches `players/`

- Validates the player file (class name matches filename, display name ≤ 25 chars)
- Registers the player in `leaderboard.yaml` at the appropriate entry tier
- Commits the leaderboard update and auto-merges the PR
- No games run immediately

**`run-season.yml`** — cron fires daily at 9am UTC; a guard job decides whether to actually run

- Runs on Mondays (weekly cadence) or when any `players/*.py` file was added/modified in the last 24h; `workflow_dispatch` always runs
- Plays `N_GAMES` (default 1000) games in each active tier, bottom-up: `inactive → L1 → CH → PRM`
- Promotions and relegations are applied between tiers (so a player promoted from L1 can compete in CH the same day)
- Commits the updated leaderboard and posts a summary to the season tracking issue

A tier is skipped if it has fewer than 2 players.

---

## Tier Structure

Capacities scale with `TOP_N` (repo variable, default 4, max 8):

| Tier     | Capacity    | Notes                                 |
| -------- | ----------- | ------------------------------------- |
| PRM      | `TOP_N`     | Premier Division — top of the table   |
| CH       | `TOP_N`     | Championship                          |
| L1       | `2 × TOP_N` | League One                            |
| inactive | unlimited   | Plays separately; top player promotes |

**Entry tier:** new players enter the lowest active tier that has capacity (L1 if possible, else CH, else PRM). A player registered mid-day plays in the next scheduled run.

**Promotion / relegation (per season run):**

- Top player in each tier promotes to the tier above
- Bottom player(s) relegate to the tier below
- `times_inactive` increments each time a player is relegated to inactive

---

## Project Structure

```
game/
  __main__.py          # entry point, logging, player selection, --tier filter
  validate.py          # player file validator (python -m game.validate <file>)
  components/
    script.py          # game loop and round orchestration
    bets.py            # Bet class, bet_validator, bet_grader
    series.py          # series runner and results formatter
    leaderboard.py     # leaderboard read/write, apply_season_results
    stats.py           # GameStats incremental stats (optional algo arg, opt-in by name)
    utils.py           # player loader
  season/
    utils.py           # shared helpers: _load_lb, _save_lb, date/quarter utilities
  simulation/
    quarter.py         # simulate a full quarter locally (uv run python -m game.simulation.quarter)

players/               # one .py file per player — see full list on GitHub
  ...                  # https://github.com/after2400/liars-dice/tree/main/players

.github/
  workflows/
    register-player.yml      # PR validation, registration, auto-merge
    run-monday.yml           # weekly/conditional season runner (guard + run jobs)
    update-leaderboard.yml   # updates README standings on player file changes
    guard-non-player-prs.yml # blocks non-admin non-player PRs from auto-merge
    release.yml              # PSR — bumps version, regenerates CHANGELOG, creates GitHub Release
    lint.yml                 # ruff + commitlint on push/PR
  scripts/
    register_player.py   # validates player file, writes leaderboard entry
    run_season.py        # bottom-up tier runner, writes season summary
    reset_season.py      # quarterly tournament reset and pool runner
    lb_owner.py          # looks up github_username by class name
    lb_has_player.py     # checks whether a class name is registered
    lb_delete.py         # removes players from leaderboard by file path
    lb_update_name.py    # validates and updates display_name on modification

.Justfile                # local dev recipes (just develop / pytest / lint / simulate-*)
leaderboard.yaml         # source of truth — tier, stats, github_username per player
```
