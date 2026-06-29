# Liar's Dice League

A Python engine for running Liar's Dice games between algorithmic players. Players compete in a tiered league — submit a PR to join, and a weekly scheduled run plays the games and updates standings (extra runs trigger automatically when a player file changes).

_This project is based on the foundational work and initial implementation by [Zach Austin](https://github.com/zachaustin01)._

Interested in competing? **[Visit the Wiki](https://github.com/after2400/liars-dice/wiki)** — rules, player API, and how to submit a bot. For local dev setup see [CONTRIBUTING.md](CONTRIBUTING.md).

## Current Standings

<!-- prettier-ignore-start -->
<!-- leaderboard-start -->
### Premier
| Player | Win % in PRM | Wins in PRM | Win % Total | Total Wins | Games |
|--------|----------------|----------------|-------------|------------|-------|
| Stewie | 18.0 | 3961 | 19.2 | 4614 | 24000 |
| Peter Beter | 16.8 | 1851 | 17.8 | 2142 | 12000 |
| Deep Thought | 16.2 | 1455 | 16.2 | 1455 | 9000 |
| EvilStewie | 16.0 | 1603 | 17.5 | 1924 | 11000 |
| Peter Griffin | 15.9 | 1908 | 15.9 | 1908 | 12000 |
| Sloane | 15.5 | 3720 | 18.5 | 7401 | 40000 |
| Nuke LaLoosh | 15.0 | 2848 | 17.8 | 3921 | 22000 |

### Championship
| Player | Win % in CH | Wins in CH | Win % Total | Total Wins | Games |
|--------|----------------|----------------|-------------|------------|-------|
| Columbo | 22.4 | 224 | 19.9 | 598 | 3000 |
| Eva | 20.7 | 4961 | 19.8 | 6339 | 32000 |
| Cal Culatid | 19.0 | 2093 | 18.3 | 3657 | 20000 |
| Zara | 18.6 | 3536 | 19.2 | 5951 | 31000 |
| Diego | 17.9 | 2154 | 18.0 | 5836 | 32350 |
| Finn | 14.0 | 2106 | 17.8 | 6291 | 35250 |
| Honest Abe | 13.6 | 2183 | 14.8 | 2656 | 18000 |

### Level 1
| Player | Win % in L1 | Wins in L1 | Win % Total | Total Wins | Games |
|--------|----------------|----------------|-------------|------------|-------|
| Remy | 22.4 | 3813 | 17.4 | 7488 | 43000 |
| Rick Sanchez | 17.3 | 2935 | 17.3 | 2935 | 17000 |
| Alice | 17.0 | 3741 | 15.9 | 4834 | 30450 |
| Bruno | 12.5 | 2745 | 12.6 | 3700 | 29450 |
| Topper | 8.5 | 2202 | 8.5 | 2202 | 26000 |
| Meg Griffin | 7.1 | 71 | 7.1 | 71 | 1000 |
| Cleo | 6.3 | 1629 | 5.4 | 1646 | 30450 |
| Liar², Pants on Fire | 4.1 | 863 | 4.1 | 863 | 21000 |

### Quarter Leaderboard

| Player | Tier | PRM W% | CH W% | L1 W% | Total W% | Games |
|--------|------|--------|-------|-------|----------|-------|
| Zara | Championship | 20.1 | 18.6 | — | 19.2 | 31000 |
| Diego | Championship | 18.1 | 17.9 | — | 18.0 | 32350 |
| Stewie | Premier | 18.0 | 36.5 | 28.8 | 19.2 | 24000 |
| Eva | Championship | 17.2 | 20.7 | — | 19.8 | 32000 |
| Peter Beter | Premier | 16.8 | 29.1 | — | 17.8 | 12000 |
| Deep Thought | Premier | 16.2 | — | — | 16.2 | 9000 |
| EvilStewie | Premier | 16.0 | 32.1 | — | 17.5 | 11000 |
| Peter Griffin | Premier | 15.9 | — | — | 15.9 | 12000 |
| Sloane | Premier | 15.5 | 23.0 | — | 18.5 | 40000 |
| Nuke LaLoosh | Premier | 15.0 | 27.6 | 52.1 | 17.8 | 22000 |
| Alice | Level 1 | 14.8 | 12.6 | 17.0 | 15.9 | 30450 |
| Finn | Championship | 14.0 | 14.0 | 21.9 | 17.8 | 35250 |
| Cal Culatid | Championship | 12.8 | 19.0 | 26.5 | 18.3 | 20000 |
| Bruno | Level 1 | 10.9 | 13.8 | 12.5 | 12.6 | 29450 |
| Remy | Level 1 | 10.6 | 14.4 | 22.4 | 17.4 | 43000 |
| Columbo | Championship | 8.1 | 22.4 | 29.3 | 19.9 | 3000 |
| Cleo | Level 1 | 1.1 | 0.3 | 6.3 | 5.4 | 30450 |
| Honest Abe | Championship | — | 13.6 | 23.6 | 14.8 | 18000 |
| Rick Sanchez | Level 1 | — | — | 17.3 | 17.3 | 17000 |
| Topper | Level 1 | — | — | 8.5 | 8.5 | 26000 |
| Meg Griffin | Level 1 | — | — | 7.1 | 7.1 | 1000 |
| Liar², Pants on Fire | Level 1 | — | — | 4.1 | 4.1 | 21000 |

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
