# Scheduled League Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the Liars Dice league from PR-triggered game runs to a scheduled daily runner with a separate, validation-only player registration workflow.

**Architecture:** Two GitHub Actions workflows replace the current one: `register-player.yml` validates PRs and writes the player into `leaderboard.yaml` (no games run), while `run-season.yml` fires on a daily cron, runs each active tier bottom-up with immediate promotion/relegation applied between tiers, and commits a single leaderboard update. The game engine switches from using `p.name` (the display name attribute) to `type(p).__name__` (the class name) as the stable leaderboard key, enabling players to update their display name without breaking their history.

**Tech Stack:** Python 3.11, uv, PyYAML, GitHub Actions, gh CLI

**Spec:** `docs/specs/2026-06-08-scheduled-league-redesign.md`

**Run all tests with:** `uv run pytest tests/ -v`

---

## File Map

### Modified

- `players/alice.py` — rename `class Player` → `class Alice`, move `name` to class attribute
- `players/bruno.py` — same pattern as alice.py
- `players/cleo.py` — same pattern
- `players/diego.py` — same pattern
- `players/finn.py` — same pattern
- `game/components/utils.py` — find player class by filename match instead of `class Player`
- `game/components/series.py` — use `type(p).__name__` as win-tracking key
- `game/__main__.py` — use `type(p).__name__` for leaderboard lookups
- `game/components/leaderboard.py` — add `display_name`/`github_username` fields, rename `times_last_in_l1` → `times_inactive`, add `apply_season_results()`
- `leaderboard.yaml` — migrate to new schema, apply pending Cleo relegation
- `tests/conftest.py` — update fixtures to new schema
- `tests/test_leaderboard.py` — update `times_last_in_l1` → `times_inactive` references
- `tests/test_main.py` — update inline leaderboard dicts to new schema

### Created

- `.github/scripts/register_player.py` — validates player file, detects entry tier, writes leaderboard entry
- `.github/workflows/register-player.yml` — PR validation + registration + auto-merge
- `.github/scripts/run_season.py` — orchestrates bottom-up daily tier runs with immediate promotion/relegation
- `.github/workflows/run-season.yml` — daily scheduled trigger for run_season.py

### Deleted (Task 9)

- `.github/workflows/liars-dice.yml`
- `.github/scripts/detect_phase.py`
- `.github/scripts/evaluate.py`
- `.github/scripts/evaluate_v1.py`
- `.github/scripts/apply_pending.py`
- `.github/scripts/check_ch_promoted.py`

---

## Task 1: Rename player classes

All five player files use `class Player` with `self.name` set in `__init__`. Rename to the class name matching the file, move `name` to a class-level attribute, and drop `__init__` (it only set `self.name`). `self.name` in `algo` and `Bet` calls still works because Python resolves class attributes through `self`.

**Files:** `players/alice.py`, `players/bruno.py`, `players/cleo.py`, `players/diego.py`, `players/finn.py`

- [ ] **Step 1: Update alice.py**

Replace:

```python
class Player:
    ...
    def __init__(self):
        self.name = "Alice"
```

With:

```python
class Alice:
    name = "Alice"
```

Remove the `__init__` method entirely (it only set `self.name`). Keep all other methods unchanged.

- [ ] **Step 2: Update bruno.py**

Replace:

```python
class Player:
    ...
    def __init__(self):
        self.name = "Bruno"
```

With:

```python
class Bruno:
    name = "Bruno"
```

Remove `__init__`. Keep all other methods unchanged.

- [ ] **Step 3: Update cleo.py**

Replace:

```python
class Player:
    ...
    def __init__(self):
        self.name = "Cleo"
```

With:

```python
class Cleo:
    name = "Cleo"
```

Remove `__init__`. Keep all other methods unchanged.

- [ ] **Step 4: Update diego.py**

Replace:

```python
class Player:
    ...
    def __init__(self):
        self.name = "Diego"
```

With:

```python
class Diego:
    name = "Diego"
```

Remove `__init__`. Keep all other methods unchanged.

- [ ] **Step 5: Update finn.py**

Replace:

```python
class Player:
    ...
    def __init__(self):
        self.name = "Finn"
```

With:

```python
class Finn:
    name = "Finn"
```

Remove `__init__`. Keep all other methods unchanged.

- [ ] **Step 6: Commit**

```bash
git add players/
git commit -m "refactor: rename Player classes to match filenames"
```

---

## Task 2: Update import utility and game engine to use class name as key

`import_player_classes_from_dir` currently looks for `class Player`. Change it to find a class whose lowercase name matches the module name (filename without `.py`). Update `series.py` and `__main__.py` to use `type(p).__name__` as the leaderboard key instead of `p.name`.

**Files:** `game/components/utils.py`, `game/components/series.py`, `game/__main__.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_main.py`:

```python
def test_class_name_used_as_leaderboard_key(tmp_path):
    """Game results dict uses class name (type(p).__name__), not p.name attribute."""
    lb = {
        "total_runs": 1,
        "players": {
            "Alice": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "tier_since": "2026-01-01T00:00:00Z", "times_inactive": 0,
                      "display_name": "Alice", "github_username": "",
                      "tier_stats": {"PRM": {"wins": 40, "games": 100, "win_pct": 40.0}}},
            "Bruno": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "tier_since": "2026-01-01T00:00:00Z", "times_inactive": 0,
                      "display_name": "Bruno", "github_username": "",
                      "tier_stats": {"PRM": {"wins": 30, "games": 100, "win_pct": 30.0}}},
        },
    }
    results = run_game(["--tier", "PRM", "5", "4"], lb, tmp_path)
    # Keys must be class names "Alice" and "Bruno", not any instance attribute
    assert set(results.keys()) == {"Alice", "Bruno"}
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_main.py::test_class_name_used_as_leaderboard_key -v
```

Expected: FAIL (wrong schema — `times_last_in_l1` instead of `times_inactive`, leaderboard key lookup fails)

- [ ] **Step 3: Update `game/components/utils.py`**

Replace `import_player_classes_from_dir`:

```python
def import_player_classes_from_dir(directory):
    player_objects = []
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            module_path = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            player_class = next(
                (getattr(module, name) for name in dir(module)
                 if name.lower() == module_name.lower()
                 and isinstance(getattr(module, name), type)),
                None,
            )
            if player_class is not None:
                player_objects.append(player_class())
    return player_objects
```

- [ ] **Step 4: Update `game/components/series.py`**

In `run_series`, change:

```python
wins = {p.name: 0 for p in players}
```

to:

```python
wins = {type(p).__name__: 0 for p in players}
```

Change:

```python
wins[winner.name] += 1
logger.info(f"Game {game_num}/{n_games}: {winner.name} wins")
```

to:

```python
wins[type(winner).__name__] += 1
logger.info(f"Game {game_num}/{n_games}: {type(winner).__name__} wins")
```

- [ ] **Step 5: Update `game/__main__.py`**

Change all four `p.name` references to `type(p).__name__`:

```python
if args.tier in ("PRM", "CH"):
    players = [p for p in all_players
               if _lb_players.get(type(p).__name__, {}).get("tier") in include_tiers
               or type(p).__name__ not in _lb_players]
else:
    players = [p for p in all_players
               if _lb_players.get(type(p).__name__, {}).get("tier") in include_tiers]
...
players = [p for p in all_players if type(p).__name__ in _lb_players] or all_players

print(f"Playing: {[type(p).__name__ for p in players]}")
```

- [ ] **Step 6: Run the new test (will still fail until schema updated in Task 3)**

```bash
uv run pytest tests/test_main.py::test_class_name_used_as_leaderboard_key -v
```

Expected: still FAIL — leaderboard fixture still uses `times_last_in_l1`. That's fixed in Task 3.

- [ ] **Step 7: Run the full test suite to check for regressions**

```bash
uv run pytest tests/ -v
```

Expected: most tests pass; `test_class_name_used_as_leaderboard_key` and any tests using `times_last_in_l1` in `test_main.py` fail. Note failures — they are addressed in Task 3/4.

- [ ] **Step 8: Commit**

```bash
git add game/components/utils.py game/components/series.py game/__main__.py
git commit -m "refactor: use class name as leaderboard key in game engine"
```

---

## Task 3: Update leaderboard.py schema

Add `display_name` and `github_username` to the default player entry. Rename `times_last_in_l1` → `times_inactive`. Add `apply_season_results()` — a new function for immediate (non-deferred) promotion/relegation used by `run_season.py`. Keep the existing functions intact since `liars-dice.yml` still uses them until Task 9.

**Files:** `game/components/leaderboard.py`, `tests/test_leaderboard.py`

- [ ] **Step 1: Write failing tests for the new schema**

Add to `tests/test_leaderboard.py`:

```python
def test_new_player_entry_has_display_name_and_github_username(lb_file):
    """update_leaderboard creates new players with display_name and github_username."""
    update_leaderboard(
        wins={"NewPlayer": 40},
        n_games=100,
        tier="CH",
        path=lb_file,
    )
    with open(lb_file) as f:
        result = yaml.safe_load(f)
    np = result["players"]["NewPlayer"]
    assert np["display_name"] == "NewPlayer"
    assert np["github_username"] == ""
    assert "times_inactive" in np
    assert "times_last_in_l1" not in np


def test_times_inactive_incremented_on_l1_last_place(lb_file):
    """times_inactive increments when a player finishes last in L1."""
    update_leaderboard(
        wins={"Alice": 60, "Bruno": 40},
        n_games=100,
        tier="L1",
        last_place="Bruno",
        path=lb_file,
    )
    with open(lb_file) as f:
        result = yaml.safe_load(f)
    assert result["players"]["Bruno"]["times_inactive"] == 1


def test_apply_season_results_promotes_top_to_tier_above(tmp_path):
    """apply_season_results moves the top player up immediately."""
    from game.components.leaderboard import apply_season_results
    lb = {
        "total_runs": 1,
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "", "tier": "CH",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
            "Bruno": {"display_name": "Bruno", "github_username": "", "tier": "CH",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
        "last_updated": "2026-01-01T00:00:00Z",
    }
    path = str(tmp_path / "lb.yaml")
    import yaml as _yaml
    (tmp_path / "lb.yaml").write_text(_yaml.dump(lb))

    apply_season_results(
        wins={"Alice": 70, "Bruno": 30},
        n_games=100,
        tier="CH",
        top_n=2,
        path=path,
    )
    with open(path) as f:
        result = _yaml.safe_load(f)
    assert result["players"]["Alice"]["tier"] == "PRM"   # top CH → PRM
    assert result["players"]["Bruno"]["tier"] == "CH"    # stays


def test_apply_season_results_promotes_even_when_tier_above_at_capacity(tmp_path):
    """Promotion is unconditional — capacity in tier above is not checked."""
    from game.components.leaderboard import apply_season_results
    lb = {
        "total_runs": 1,
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "", "tier": "CH",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
            "Bruno": {"display_name": "Bruno", "github_username": "", "tier": "CH",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
            # PRM is already at capacity (top_n=2)
            "Cleo": {"display_name": "Cleo", "github_username": "", "tier": "PRM",
                     "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                     "times_inactive": 0, "tier_stats": {}},
            "Diego": {"display_name": "Diego", "github_username": "", "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
        "last_updated": "2026-01-01T00:00:00Z",
    }
    path = str(tmp_path / "lb.yaml")
    import yaml as _yaml
    (tmp_path / "lb.yaml").write_text(_yaml.dump(lb))

    apply_season_results(
        wins={"Alice": 70, "Bruno": 30},
        n_games=100,
        tier="CH",
        top_n=2,
        path=path,
    )
    with open(path) as f:
        result = _yaml.safe_load(f)
    # Alice promotes to PRM even though PRM was already full
    assert result["players"]["Alice"]["tier"] == "PRM"


def test_apply_season_results_relegates_bottom(tmp_path):
    """apply_season_results moves the bottom player down immediately."""
    from game.components.leaderboard import apply_season_results
    lb = {
        "total_runs": 1,
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "", "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
            "Bruno": {"display_name": "Bruno", "github_username": "", "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
        "last_updated": "2026-01-01T00:00:00Z",
    }
    path = str(tmp_path / "lb.yaml")
    import yaml as _yaml
    (tmp_path / "lb.yaml").write_text(_yaml.dump(lb))

    apply_season_results(
        wins={"Alice": 70, "Bruno": 30},
        n_games=100,
        tier="PRM",
        top_n=2,
        path=path,
    )
    with open(path) as f:
        result = _yaml.safe_load(f)
    assert result["players"]["Bruno"]["tier"] == "CH"    # bottom PRM → CH
    assert result["players"]["Alice"]["tier"] == "PRM"   # stays
```

- [ ] **Step 2: Run to verify failures**

```bash
uv run pytest tests/test_leaderboard.py::test_new_player_entry_has_display_name_and_github_username tests/test_leaderboard.py::test_times_inactive_incremented_on_l1_last_place tests/test_leaderboard.py::test_apply_season_results_promotes_top_to_tier_above tests/test_leaderboard.py::test_apply_season_results_relegates_bottom -v
```

Expected: all four FAIL

- [ ] **Step 3: Update `game/components/leaderboard.py`**

In `update_leaderboard`, update the default player entry:

```python
player = data["players"].setdefault(name, {
    "display_name": name,
    "github_username": "",
    "date_added": now,
    "tier": tier,
    "tier_since": now,
    "times_inactive": 0,
    "tier_stats": {},
})
```

Update the `times_last_in_l1` block:

```python
if tier == "L1" and last_place and last_place in data["players"]:
    data["players"][last_place]["times_inactive"] = (
        data["players"][last_place].get("times_inactive", 0) + 1
    )
```

Add `apply_season_results` at the bottom of the file:

```python
_TIER_ABOVE = {"L1": "CH", "CH": "PRM", "inactive": "L1"}
_TIER_BELOW = {"PRM": "CH", "CH": "L1", "L1": "inactive"}
_TIER_CAPACITY = lambda tier, top_n: (
    top_n if tier in ("PRM", "CH") else top_n * 2 if tier == "L1" else float("inf")
)


def apply_season_results(
    wins: dict[str, int],
    n_games: int,
    tier: str,
    top_n: int,
    path: str = _LEADERBOARD_PATH,
) -> None:
    """Update stats and apply immediate promotions/relegations for a scheduled run.

    Promotes the top player to the tier above (if space exists).
    Relegates enough players from the bottom to restore capacity.
    No pending_relegation — all moves are immediate.
    """
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    now = _now()
    data.setdefault("total_runs", 0)
    data["total_runs"] += 1
    data["last_updated"] = now
    data.setdefault("players", {})

    # Update cumulative tier_stats for competing players
    for name, win_count in wins.items():
        if name not in data["players"]:
            continue
        player = data["players"][name]
        ts = player.setdefault("tier_stats", {})
        ts_tier = ts.setdefault(tier, {"wins": 0, "games": 0, "win_pct": 0.0})
        ts_tier["wins"] += win_count
        ts_tier["games"] += n_games
        ts_tier["win_pct"] = round(ts_tier["wins"] / ts_tier["games"] * 100, 1)

    # Rank by wins desc; tiebreak on historical tier games desc, then tier_since asc
    def _rank_key(item):
        name, w = item
        p = data["players"].get(name, {})
        tier_games = p.get("tier_stats", {}).get(tier, {}).get("games", 0)
        return (-w, -tier_games, p.get("tier_since", ""))

    ranked = sorted(wins.items(), key=_rank_key)
    players_in_tier = [name for name, _ in ranked]

    tier_above = _TIER_ABOVE.get(tier)
    tier_below = _TIER_BELOW.get(tier)

    # Promote top player unconditionally — bottom-up run order means the tier above
    # will shed a player later in the same daily cycle, resolving any temporary overcapacity.
    promoted = None
    if tier_above and players_in_tier:
        promoted = players_in_tier[0]
        data["players"][promoted]["tier"] = tier_above
        data["players"][promoted]["tier_since"] = now

    # Relegate enough from the bottom to restore this tier to capacity
    # (always at least 1 if tier_below exists and we have ≥2 players)
    if tier_below:
        capacity = _TIER_CAPACITY(tier, top_n)
        remaining = [p for p in players_in_tier if p != promoted]
        excess = max(1, len(remaining) - capacity) if remaining else 0
        for name in reversed(remaining):
            if excess <= 0:
                break
            data["players"][name]["tier"] = tier_below
            data["players"][name]["tier_since"] = now
            if tier_below == "inactive":
                data["players"][name]["times_inactive"] = (
                    data["players"][name].get("times_inactive", 0) + 1
                )
            excess -= 1

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

- [ ] **Step 4: Run the four new tests**

```bash
uv run pytest tests/test_leaderboard.py::test_new_player_entry_has_display_name_and_github_username tests/test_leaderboard.py::test_times_inactive_incremented_on_l1_last_place tests/test_leaderboard.py::test_apply_season_results_promotes_top_to_tier_above tests/test_leaderboard.py::test_apply_season_results_relegates_bottom -v
```

Expected: all four PASS

- [ ] **Step 5: Commit**

```bash
git add game/components/leaderboard.py tests/test_leaderboard.py
git commit -m "feat: update leaderboard schema and add apply_season_results"
```

---

## Task 4: Migrate leaderboard.yaml and update all test fixtures

Update the real `leaderboard.yaml` to the new schema. Update all test fixtures in `conftest.py` and inline leaderboard dicts in `test_main.py` and `test_leaderboard.py` to match.

**Files:** `leaderboard.yaml`, `tests/conftest.py`, `tests/test_leaderboard.py`, `tests/test_main.py`

- [ ] **Step 1: Rewrite `leaderboard.yaml`**

Apply the pending Cleo relegation (PRM → CH), add `display_name`/`github_username`, rename `times_last_in_l1` → `times_inactive`, remove `pending_relegation`:

```yaml
total_runs: 3
last_updated: "2026-06-08T20:41:19Z"
players:
  Alice:
    display_name: Alice
    github_username: ""
    date_added: "2026-05-22T15:47:31Z"
    tier: PRM
    tier_since: "2026-05-22T15:47:31Z"
    times_inactive: 0
    tier_stats:
      PRM:
        wins: 127
        games: 450
        win_pct: 28.2
  Bruno:
    display_name: Bruno
    github_username: ""
    date_added: "2026-05-22T15:47:31Z"
    tier: PRM
    tier_since: "2026-05-22T15:47:31Z"
    times_inactive: 0
    tier_stats:
      PRM:
        wins: 90
        games: 450
        win_pct: 20.0
  Cleo:
    display_name: Cleo
    github_username: ""
    date_added: "2026-05-22T15:47:31Z"
    tier: CH
    tier_since: "2026-06-08T20:41:19Z"
    times_inactive: 0
    tier_stats:
      PRM:
        wins: 5
        games: 450
        win_pct: 1.1
  Diego:
    display_name: Diego
    github_username: ""
    date_added: "2026-05-22T16:10:13Z"
    tier: PRM
    tier_since: "2026-05-22T16:10:13Z"
    times_inactive: 0
    tier_stats:
      PRM:
        wins: 160
        games: 350
        win_pct: 45.7
  Finn:
    display_name: Finn
    github_username: after2400
    date_added: "2026-06-08T20:41:19Z"
    tier: PRM
    tier_since: "2026-06-08T20:41:19Z"
    times_inactive: 0
    tier_stats:
      PRM:
        wins: 68
        games: 250
        win_pct: 27.2
```

- [ ] **Step 2: Update `tests/conftest.py`**

Replace all three fixtures. Change `times_last_in_l1` → `times_inactive` and add `display_name`/`github_username` to every player entry. Also remove `pending_relegation` from `lb_with_pending` (keep as a dict with empty list for backward compat with tests that check it explicitly):

```python
import pytest


@pytest.fixture
def minimal_lb():
    """Two players, both in PRM."""
    return {
        "total_runs": 2,
        "last_updated": "2026-01-01T00:00:00Z",
        "players": {
            "Alice": {
                "display_name": "Alice",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 40, "games": 100, "win_pct": 40.0}},
            },
            "Bruno": {
                "display_name": "Bruno",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 30, "games": 100, "win_pct": 30.0}},
            },
        },
    }


@pytest.fixture
def full_two_tier_lb():
    """Four players: 2 PRM, 2 CH."""
    return {
        "total_runs": 5,
        "last_updated": "2026-01-01T00:00:00Z",
        "players": {
            "Alice": {
                "display_name": "Alice",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 40, "games": 100, "win_pct": 40.0}},
            },
            "Bruno": {
                "display_name": "Bruno",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 30, "games": 100, "win_pct": 30.0}},
            },
            "Cleo": {
                "display_name": "Cleo",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "CH",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"CH": {"wins": 20, "games": 100, "win_pct": 20.0}},
            },
            "Diego": {
                "display_name": "Diego",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "CH",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"CH": {"wins": 10, "games": 100, "win_pct": 10.0}},
            },
        },
    }


@pytest.fixture
def lb_with_pending():
    """Leaderboard with a pending PRM→CH relegation for Alice."""
    return {
        "total_runs": 3,
        "last_updated": "2026-01-01T00:00:00Z",
        "pending_relegation": [
            {"player": "Alice", "from_tier": "PRM", "to_tier": "CH"}
        ],
        "players": {
            "Alice": {
                "display_name": "Alice",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 40, "games": 100, "win_pct": 40.0}},
            },
            "Bruno": {
                "display_name": "Bruno",
                "github_username": "",
                "date_added": "2026-01-01T00:00:00Z",
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_inactive": 0,
                "tier_stats": {"PRM": {"wins": 30, "games": 100, "win_pct": 30.0}},
            },
        },
    }


@pytest.fixture
def lb_file(tmp_path, minimal_lb):
    """Write minimal_lb to a temp file and return its path."""
    import yaml
    path = tmp_path / "leaderboard.yaml"
    path.write_text(yaml.dump(minimal_lb, default_flow_style=False, sort_keys=False))
    return str(path)
```

- [ ] **Step 3: Update `tests/test_leaderboard.py`**

Find and replace every `"times_last_in_l1"` with `"times_inactive"`. There are four occurrences — two test names and two assertions:

- `test_times_last_in_l1_incremented` → `test_times_inactive_incremented`
- `test_times_last_in_l1_not_incremented_for_other_tiers` → `test_times_inactive_not_incremented_for_other_tiers`
- `assert result["players"]["Bruno"]["times_last_in_l1"] == 1` → `assert result["players"]["Bruno"]["times_inactive"] == 1`
- `assert result["players"]["Bruno"]["times_last_in_l1"] == 0` → `assert result["players"]["Bruno"]["times_inactive"] == 0`

Also update `test_update_creates_new_player_with_defaults`:

```python
assert np["times_inactive"] == 0       # was times_last_in_l1
assert np["display_name"] == "NewPlayer"
assert np["github_username"] == ""
```

Remove the `assert np["times_last_in_l1"] == 0` line.

- [ ] **Step 4: Update inline leaderboard dicts in `tests/test_main.py`**

Each inline `lb` dict in `test_tier_prm_selects_only_prm_players`, `test_tier_l1_includes_inactive_players`, `test_results_file_written`, and `test_no_leaderboard_update_written` must be updated:

- Replace `"times_last_in_l1": 0` with `"times_inactive": 0`
- Add `"display_name": "<PlayerName>"` and `"github_username": ""`

Example for Alice in any test:

```python
"Alice": {"display_name": "Alice", "github_username": "",
          "tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
          "tier_since": "2026-01-01T00:00:00Z", "times_inactive": 0,
          "tier_stats": {"PRM": {"wins": 40, "games": 100, "win_pct": 40.0}}},
```

Apply this pattern to every player dict in every inline `lb` in `test_main.py`.

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add leaderboard.yaml tests/conftest.py tests/test_leaderboard.py tests/test_main.py
git commit -m "feat: migrate leaderboard schema and update all tests"
```

---

## Task 5: Write `register_player.py`

This script is called by `register-player.yml` to validate a player file and register it in `leaderboard.yaml`. It reads `PLAYER_FILE`, `GITHUB_USERNAME`, and `TOP_N` from environment variables and writes the entry tier to stdout for the workflow to capture.

**Files:** `.github/scripts/register_player.py`

- [ ] **Step 1: Write the script**

Create `.github/scripts/register_player.py`:

```python
#!/usr/bin/env python3
"""Validate a player file and register it in leaderboard.yaml.

Environment variables:
  PLAYER_FILE       path to the player .py file (e.g. players/fred.py)
  GITHUB_USERNAME   the PR author's GitHub login (github.actor)
  TOP_N             league capacity per tier (int, default 4)

Exits 0 on success, 1 on validation failure.
Prints "entry_tier=<tier>" to stdout for the workflow to capture.
"""
import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

LEADERBOARD_PATH = "leaderboard.yaml"
MAX_NAME_LEN = 20


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_lb():
    if os.path.exists(LEADERBOARD_PATH):
        with open(LEADERBOARD_PATH) as f:
            return yaml.safe_load(f) or {}
    return {"players": {}, "total_runs": 0, "last_updated": _now()}


def _save_lb(data):
    data["last_updated"] = _now()
    with open(LEADERBOARD_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _detect_entry_tier(lb: dict, top_n: int) -> str:
    players = lb.get("players", {})
    l1_count = sum(1 for p in players.values() if p.get("tier") == "L1")
    ch_count = sum(1 for p in players.values() if p.get("tier") == "CH")

    if l1_count >= 1:
        return "L1"
    if ch_count >= 1:
        return "CH"
    return "PRM"


def main():
    player_file = os.environ["PLAYER_FILE"]
    github_username = os.environ["GITHUB_USERNAME"]
    top_n = int(os.environ.get("TOP_N", "4"))

    module_name = Path(player_file).stem  # e.g. "fred" from "players/fred.py"

    spec = importlib.util.spec_from_file_location(module_name, player_file)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"ERROR: Failed to import {player_file}: {e}")
        sys.exit(1)

    # Find class matching filename (case-insensitive)
    player_class = next(
        (getattr(module, name) for name in dir(module)
         if name.lower() == module_name.lower()
         and isinstance(getattr(module, name), type)),
        None,
    )
    if player_class is None:
        print(f"ERROR: No class matching '{module_name}' found in {player_file}. "
              f"Class name must match filename (e.g. class Fred in fred.py).")
        sys.exit(1)

    class_name = player_class.__name__
    display_name = getattr(player_class, "name", class_name)

    # Validate display name
    if len(display_name) > MAX_NAME_LEN:
        print(f"ERROR: name attribute '{display_name}' exceeds {MAX_NAME_LEN} characters.")
        sys.exit(1)
    if "(" in display_name or ")" in display_name:
        print(f"ERROR: name attribute may not contain parentheses (reserved for username suffix).")
        sys.exit(1)

    lb = _load_lb()
    players = lb.setdefault("players", {})

    if class_name in players:
        print(f"Player {class_name} is already registered.")
        print(f"entry_tier={players[class_name]['tier']}")
        return

    entry_tier = _detect_entry_tier(lb, top_n)
    now = _now()
    players[class_name] = {
        "display_name": display_name,
        "github_username": github_username,
        "date_added": now,
        "tier": entry_tier,
        "tier_since": now,
        "times_inactive": 0,
        "tier_stats": {},
    }

    _save_lb(lb)
    print(f"Registered {class_name} (display: {display_name}) as {github_username} in {entry_tier}")
    print(f"entry_tier={entry_tier}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write tests for `register_player.py`**

Create `tests/test_register_player.py`:

```python
import os
import yaml
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def run_register(player_file: str, lb: dict, tmp_path: Path,
                 github_username: str = "testuser", top_n: int = 4) -> tuple[int, str]:
    """Run register_player.py in a temp dir. Returns (returncode, stdout)."""
    import subprocess
    lb_path = tmp_path / "leaderboard.yaml"
    lb_path.write_text(yaml.dump(lb, default_flow_style=False, sort_keys=False))

    env = {
        **os.environ,
        "PLAYER_FILE": str(player_file),
        "GITHUB_USERNAME": github_username,
        "TOP_N": str(top_n),
        "LEADERBOARD_PATH": str(lb_path),  # not used by script directly but good practice
    }
    # Override LEADERBOARD_PATH by running from tmp_path so script finds leaderboard.yaml
    result = subprocess.run(
        ["uv", "run", "python", str(REPO_ROOT / ".github/scripts/register_player.py")],
        cwd=str(tmp_path),
        env={**env, "PLAYER_FILE": str(player_file)},
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout + result.stderr


def test_register_new_player_enters_l1_when_l1_has_capacity(tmp_path):
    lb = {
        "total_runs": 0,
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "",
                      "tier": "L1", "tier_since": "2026-01-01T00:00:00Z",
                      "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
    }
    player_file = REPO_ROOT / "players" / "bruno.py"
    rc, out = run_register(player_file, lb, tmp_path, top_n=4)
    assert rc == 0, out
    lb_result = yaml.safe_load((tmp_path / "leaderboard.yaml").read_text())
    assert lb_result["players"]["Bruno"]["tier"] == "L1"


def test_register_new_player_enters_prm_when_all_tiers_empty(tmp_path):
    lb = {"total_runs": 0, "players": {}}
    player_file = REPO_ROOT / "players" / "alice.py"
    rc, out = run_register(player_file, lb, tmp_path, top_n=4)
    assert rc == 0, out
    lb_result = yaml.safe_load((tmp_path / "leaderboard.yaml").read_text())
    assert lb_result["players"]["Alice"]["tier"] == "PRM"


def test_register_stores_github_username(tmp_path):
    lb = {"total_runs": 0, "players": {}}
    player_file = REPO_ROOT / "players" / "alice.py"
    rc, out = run_register(player_file, lb, tmp_path, github_username="after2400")
    assert rc == 0, out
    lb_result = yaml.safe_load((tmp_path / "leaderboard.yaml").read_text())
    assert lb_result["players"]["Alice"]["github_username"] == "after2400"


def test_register_exits_0_if_already_registered(tmp_path):
    lb = {
        "total_runs": 0,
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "someone",
                      "tier": "PRM", "tier_since": "2026-01-01T00:00:00Z",
                      "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
    }
    player_file = REPO_ROOT / "players" / "alice.py"
    rc, out = run_register(player_file, lb, tmp_path)
    assert rc == 0
    # Leaderboard unchanged
    lb_result = yaml.safe_load((tmp_path / "leaderboard.yaml").read_text())
    assert lb_result["players"]["Alice"]["github_username"] == "someone"
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_register_player.py -v
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add .github/scripts/register_player.py tests/test_register_player.py
git commit -m "feat: add register_player.py script"
```

---

## Task 6: Write `register-player.yml`

The PR-triggered workflow. Validates the PR contents (addition, modification, or deletion), runs `register_player.py` for new players, commits the leaderboard update, and auto-merges.

**Files:** `.github/workflows/register-player.yml`

- [ ] **Step 1: Create the workflow**

```yaml
name: Register Player

on:
  pull_request:
    branches: [main]
    paths:
      - "players/*.py"

env:
  PYTHONPATH: .

jobs:
  register:
    if: github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          fetch-depth: 0

      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: uv sync --no-install-project

      - name: Classify PR changes
        id: classify
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git fetch origin main

          added=$(git diff --name-only --diff-filter=A origin/main HEAD -- 'players/*.py' || true)
          modified=$(git diff --name-only --diff-filter=M origin/main HEAD -- 'players/*.py' || true)
          deleted=$(git diff --name-only --diff-filter=D origin/main HEAD -- 'players/*.py' || true)

          n_added=$(echo "$added" | grep -c '.' || true)
          n_modified=$(echo "$modified" | grep -c '.' || true)
          n_deleted=$(echo "$deleted" | grep -c '.' || true)

          # Reject mixed deletions + additions/modifications
          if [ "$n_deleted" -gt 0 ] && [ "$((n_added + n_modified))" -gt 0 ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "❌ PRs may not mix deletions with additions or modifications. Please open separate PRs."
            exit 1
          fi

          # Reject multiple additions/modifications
          if [ "$n_deleted" -eq 0 ] && [ "$((n_added + n_modified))" -ne 1 ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "❌ Each PR must change exactly one player file. Found: $((n_added + n_modified)) files."
            exit 1
          fi

          echo "added=$added" >> "$GITHUB_OUTPUT"
          echo "modified=$modified" >> "$GITHUB_OUTPUT"
          echo "deleted=$deleted" >> "$GITHUB_OUTPUT"
          echo "n_added=$n_added" >> "$GITHUB_OUTPUT"
          echo "n_modified=$n_modified" >> "$GITHUB_OUTPUT"
          echo "n_deleted=$n_deleted" >> "$GITHUB_OUTPUT"

      - name: Check admin status
        id: admin
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          is_admin=$(gh api repos/${{ github.repository }}/collaborators/${{ github.actor }}/permission \
            --jq '.permission == "admin"' 2>/dev/null || echo "false")
          echo "is_admin=$is_admin" >> "$GITHUB_OUTPUT"

      - name: Handle addition
        if: steps.classify.outputs.n_added == '1'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TOP_N: ${{ vars.TOP_N || '4' }}
          PLAYER_FILE: ${{ steps.classify.outputs.added }}
          GITHUB_USERNAME: ${{ github.actor }}
        run: |
          class_name=$(python3 -c "
          import importlib.util, sys
          from pathlib import Path
          f = '$PLAYER_FILE'
          m = Path(f).stem
          spec = importlib.util.spec_from_file_location(m, f)
          mod = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(mod)
          cls = next((n for n in dir(mod) if n.lower() == m.lower() and isinstance(getattr(mod, n), type)), None)
          print(cls or '')
          ")
          if [ -z "$class_name" ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "❌ No class matching the filename found in \`$PLAYER_FILE\`. Class name must match filename."
            exit 1
          fi

          if python3 -c "import yaml, sys; lb = yaml.safe_load(open('leaderboard.yaml')) or {}; sys.exit(0 if '$class_name' in lb.get('players', {}) else 1)"; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "❌ A player named \`$class_name\` is already registered. Class names must be unique."
            exit 1
          fi

          uv run python .github/scripts/register_player.py

      - name: Handle modification
        if: steps.classify.outputs.n_modified == '1'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          file="${{ steps.classify.outputs.modified }}"
          class_name=$(basename "$file" .py)
          class_name="${class_name^}"

          registered_username=$(python3 -c "
          import yaml, sys
          lb = yaml.safe_load(open('leaderboard.yaml')) or {}
          p = lb.get('players', {}).get('$class_name', {})
          print(p.get('github_username', ''))
          ")

          actor="${{ github.actor }}"
          is_admin="${{ steps.admin.outputs.is_admin }}"

          if [ "$actor" != "$registered_username" ] && [ "$is_admin" != "true" ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "❌ Only the original author (\`$registered_username\`) or an admin may modify \`$class_name\`."
            exit 1
          fi

          # Update display_name if name attribute changed
          new_display=$(python3 -c "
          import importlib.util
          from pathlib import Path
          f = '$file'
          m = Path(f).stem
          spec = importlib.util.spec_from_file_location(m, f)
          mod = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(mod)
          cls = next((getattr(mod, n) for n in dir(mod) if n.lower() == m.lower() and isinstance(getattr(mod, n), type)), None)
          print(getattr(cls, 'name', cls.__name__) if cls else '')
          ")

          python3 -c "
          import yaml
          lb = yaml.safe_load(open('leaderboard.yaml')) or {}
          lb['players']['$class_name']['display_name'] = '$new_display'
          with open('leaderboard.yaml', 'w') as f:
              yaml.dump(lb, f, default_flow_style=False, sort_keys=False)
          "
          echo "Updated display_name for $class_name to: $new_display"

      - name: Handle deletion
        if: steps.classify.outputs.n_deleted != '0'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          is_admin="${{ steps.admin.outputs.is_admin }}"
          deleted_files="${{ steps.classify.outputs.deleted }}"
          actor="${{ github.actor }}"

          for file in $deleted_files; do
            class_name=$(basename "$file" .py)
            class_name="${class_name^}"
            owner=$(python3 -c "
          import yaml, sys
          lb = yaml.safe_load(open('leaderboard.yaml')) or {}
          p = lb.get('players', {}).get('$class_name', {})
          print(p.get('github_username', ''))
            ")
            if [ "$is_admin" != "true" ] && [ "$actor" != "$owner" ]; then
              gh pr comment ${{ github.event.pull_request.number }} \
                --body "❌ Only the original author (\`$owner\`) or an admin may delete \`$class_name\`."
              exit 1
            fi
          done

          # Remove all deleted players from leaderboard
          python3 -c "
          import yaml
          lb = yaml.safe_load(open('leaderboard.yaml')) or {}
          for f in '''$deleted_files'''.split():
              import os
              class_name = os.path.basename(f).replace('.py', '').capitalize()
              lb.get('players', {}).pop(class_name, None)
          with open('leaderboard.yaml', 'w') as f:
              yaml.dump(lb, f, default_flow_style=False, sort_keys=False)
          "

      - name: Commit leaderboard update
        run: |
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"
          git add leaderboard.yaml
          if ! git diff --cached --quiet; then
            git commit -m "ci: register player [skip ci]"
            git push
          fi

      - name: Post confirmation comment
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "✅ Player registered. They will play in the next scheduled league run."

      - name: Auto-merge
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: gh pr merge ${{ github.event.pull_request.number }} --auto --squash
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/register-player.yml
git commit -m "feat: add register-player.yml workflow"
```

---

## Task 7: Write `run_season.py`

Orchestrates the daily bottom-up season run. Runs each active tier via subprocess, applies promotions/relegations between tiers using `apply_season_results`, then writes a Markdown summary.

**Files:** `.github/scripts/run_season.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Orchestrate the daily league season run.

Runs each active tier bottom-up (inactive → L1 → CH → PRM), applies
immediate promotions/relegations between tiers via apply_season_results,
and writes a summary to summary.md.

Environment variables:
  TOP_N     league capacity per tier (int, default 4)
  N_GAMES   games per tier run (int, default 250)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
LEADERBOARD_PATH = REPO_ROOT / "leaderboard.yaml"
TIER_ORDER = ["inactive", "L1", "CH", "PRM"]
TIER_LABELS = {"PRM": "Premier Division", "CH": "Championship",
               "L1": "League One", "inactive": "Inactive"}


def _load_lb():
    with open(LEADERBOARD_PATH) as f:
        return yaml.safe_load(f) or {}


def _get_tier_players(lb, tier):
    if tier == "L1":
        return [n for n, p in lb.get("players", {}).items()
                if p.get("tier") in ("L1", "inactive")]
    return [n for n, p in lb.get("players", {}).items() if p.get("tier") == tier]


def _run_tier(tier, n_games, top_n):
    """Invoke python -m game for the given tier. Returns results dict or None."""
    results_file = REPO_ROOT / f"{tier.lower()}_results.json"
    cmd = [
        "uv", "run", "python", "-m", "game",
        "--tier", tier,
        "--results-file", str(results_file),
        str(n_games), str(top_n),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return None
    print(result.stdout)
    if results_file.exists():
        return json.loads(results_file.read_text())
    return None


_TIER_CAPACITIES = lambda top_n: {"PRM": top_n, "CH": top_n, "L1": top_n * 2}


def _write_summary(run_results: dict[str, dict], top_n: int):
    lb = _load_lb()
    players = lb.get("players", {})

    lines = ["# Daily League Run\n"]
    for tier in ("PRM", "CH", "L1", "inactive"):
        tier_players = [(n, p) for n, p in players.items() if p.get("tier") == tier]
        if not tier_players:
            continue
        lines.append(f"## {TIER_LABELS[tier]}\n")
        lines.append("| Player | Cumul Win% | This Run | Games |")
        lines.append("|--------|-----------|----------|-------|")
        results = run_results.get(tier, {})
        total_this_run = sum(results.values()) if results else 0
        for name, p in sorted(tier_players,
                               key=lambda x: x[1].get("tier_stats", {}).get(tier, {}).get("win_pct", 0),
                               reverse=True):
            ts = p.get("tier_stats", {}).get(tier, {})
            cumul_pct = ts.get("win_pct", 0.0)
            games = ts.get("games", 0)
            this_run_wins = results.get(name, 0)
            this_run_pct = round(this_run_wins / total_this_run * 100, 1) if total_this_run else 0.0
            display = p.get("display_name", name)
            username = p.get("github_username", "")
            label = f"{display} ({username})" if username else display
            lines.append(f"| {label} | {cumul_pct}% | {this_run_wins} ({this_run_pct}%) | {games} |")
        lines.append("")

    # Capacity report — warns about any tiers temporarily over capacity after overflow
    capacities = _TIER_CAPACITIES(top_n)
    lines.append("## Capacity Report\n")
    for tier, cap in capacities.items():
        count = sum(1 for p in players.values() if p.get("tier") == tier)
        icon = "⚠️" if count > cap else "✅"
        note = f" — will resolve next run" if count > cap else ""
        lines.append(f"{icon} {TIER_LABELS[tier]}: {count}/{cap}{note}")

    with open(REPO_ROOT / "summary.md", "w") as f:
        f.write("\n".join(lines))


def main():
    top_n = int(os.environ.get("TOP_N", "4"))
    n_games = int(os.environ.get("N_GAMES", "250"))

    from game.components.leaderboard import apply_season_results

    run_results = {}

    for tier in TIER_ORDER:
        lb = _load_lb()
        if tier == "inactive":
            tier_players = _get_tier_players(lb, "inactive")
            run_tier_key = "L1"  # __main__.py uses --tier L1 to include inactive
        else:
            tier_players = _get_tier_players(lb, tier)
            run_tier_key = tier

        if len(tier_players) < 2:
            print(f"[skip] {TIER_LABELS.get(tier, tier)}: only {len(tier_players)} player(s)")
            continue

        print(f"\n=== Running {TIER_LABELS.get(tier, tier)} ===")
        if tier == "inactive":
            results = _run_tier("L1", n_games, top_n)
        else:
            results = _run_tier(tier, n_games, top_n)

        if results is None:
            print(f"[error] {tier} run failed — skipping promotion/relegation for this tier")
            continue

        run_results[tier] = results

        apply_season_results(
            wins=results,
            n_games=n_games,
            tier=tier,
            top_n=top_n,
            path=str(LEADERBOARD_PATH),
        )

    _write_summary(run_results, top_n)
    print("\nSeason run complete. Summary written to summary.md.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write a smoke test**

Add to `tests/test_run_season.py`:

```python
import os
import subprocess
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_run_season_skips_tiers_with_one_player(tmp_path):
    """run_season.py skips tiers that have only 1 player (no game, no crash)."""
    lb = {
        "total_runs": 0,
        "last_updated": "2026-01-01T00:00:00Z",
        "players": {
            "Alice": {"display_name": "Alice", "github_username": "",
                      "tier": "PRM", "tier_since": "2026-01-01T00:00:00Z",
                      "date_added": "2026-01-01T00:00:00Z",
                      "times_inactive": 0, "tier_stats": {}},
        },
    }
    lb_path = tmp_path / "leaderboard.yaml"
    lb_path.write_text(yaml.dump(lb))

    env = {
        **os.environ,
        "TOP_N": "4",
        "N_GAMES": "5",
        "LEADERBOARD_PATH": str(lb_path),
    }
    # Patch LEADERBOARD_PATH into run_season.py by running from tmp_path
    # (run_season.py uses REPO_ROOT / "leaderboard.yaml" — copy lb there for test)
    import shutil
    shutil.copy(lb_path, REPO_ROOT / "_test_leaderboard.yaml")
    try:
        result = subprocess.run(
            ["uv", "run", "python", ".github/scripts/run_season.py"],
            cwd=REPO_ROOT, capture_output=True, text=True,
            env={**env, "LEADERBOARD_PATH": str(REPO_ROOT / "_test_leaderboard.yaml")},
        )
        assert result.returncode == 0, result.stderr
        assert "[skip]" in result.stdout
    finally:
        (REPO_ROOT / "_test_leaderboard.yaml").unlink(missing_ok=True)
        (REPO_ROOT / "summary.md").unlink(missing_ok=True)
```

> **Note:** `run_season.py` currently hardcodes `LEADERBOARD_PATH = REPO_ROOT / "leaderboard.yaml"`. For testability, update it to read `os.environ.get("LEADERBOARD_PATH", str(REPO_ROOT / "leaderboard.yaml"))` before writing the test.

- [ ] **Step 3: Add LEADERBOARD_PATH env support to `run_season.py`**

Change:

```python
LEADERBOARD_PATH = REPO_ROOT / "leaderboard.yaml"
```

to:

```python
LEADERBOARD_PATH = Path(os.environ.get("LEADERBOARD_PATH", str(REPO_ROOT / "leaderboard.yaml")))
```

- [ ] **Step 4: Run the smoke test**

```bash
uv run pytest tests/test_run_season.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/scripts/run_season.py tests/test_run_season.py
git commit -m "feat: add run_season.py orchestrator script"
```

---

## Task 8: Write `run-season.yml`

The scheduled workflow. Fires daily at 09:00 UTC (4am EST / 5am EDT), runs `run_season.py`, commits the leaderboard, and posts the summary to the configured tracking issue.

**Files:** `.github/workflows/run-season.yml`

- [ ] **Step 1: Create a tracking issue**

Before deploying this workflow, create a GitHub issue to receive daily summaries:

```bash
gh issue create --title "Daily League Results" \
  --body "This issue receives automated daily league run summaries." \
  --label ""
```

Note the issue number. Add it as a repo variable: `TRACKING_ISSUE=<number>` in GitHub → Settings → Variables → Actions.

- [ ] **Step 2: Create the workflow**

```yaml
name: Run Season

on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch: # allow manual trigger for testing

env:
  PYTHONPATH: .

jobs:
  run-season:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: uv sync --no-install-project

      - name: Run season
        env:
          TOP_N: ${{ vars.TOP_N || '4' }}
          N_GAMES: ${{ vars.N_GAMES || '250' }}
        run: uv run python .github/scripts/run_season.py

      - name: Commit leaderboard
        run: |
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"
          git add leaderboard.yaml
          if ! git diff --cached --quiet; then
            git commit -m "ci: daily league run [skip ci]"
            git push
          fi

      - name: Post summary to tracking issue
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TRACKING_ISSUE: ${{ vars.TRACKING_ISSUE }}
        run: |
          if [ -n "$TRACKING_ISSUE" ] && [ -f summary.md ]; then
            gh issue comment "$TRACKING_ISSUE" --body-file summary.md
          fi
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/run-season.yml
git commit -m "feat: add run-season.yml scheduled workflow"
```

---

## Task 9: Retire old workflow and scripts

Delete `liars-dice.yml` and all scripts that supported it. These are dead code once `register-player.yml` and `run-season.yml` are live.

**Files:** `.github/workflows/liars-dice.yml`, `.github/scripts/detect_phase.py`, `.github/scripts/evaluate.py`, `.github/scripts/evaluate_v1.py`, `.github/scripts/apply_pending.py`, `.github/scripts/check_ch_promoted.py`

- [ ] **Step 1: Delete old files**

```bash
rm .github/workflows/liars-dice.yml
rm .github/scripts/detect_phase.py
rm .github/scripts/evaluate.py
rm .github/scripts/evaluate_v1.py
rm .github/scripts/apply_pending.py
rm .github/scripts/check_ch_promoted.py
```

- [ ] **Step 2: Run full test suite to confirm nothing broke**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS (no tests imported from the deleted scripts)

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: retire liars-dice.yml and legacy evaluation scripts"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** class_name as key ✓ | display_name/github_username ✓ | times_inactive ✓ | register-player.yml ✓ | run-season.yml ✓ | bottom-up run order ✓ | immediate promotion/relegation ✓ | capacity-based movement ✓ | entry tier logic ✓ | PR validation cases (addition/modification/deletion) ✓ | admin check ✓ | retire old workflow ✓
- [x] **Placeholder scan:** All code blocks are complete. No TBDs.
- [x] **Type consistency:** `apply_season_results` signature used in Task 3 matches import in Task 7. `_TIER_ABOVE`/`_TIER_BELOW` dicts defined before use.
