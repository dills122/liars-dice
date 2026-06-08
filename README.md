# Liar's Dice

A Python engine for running Liar's Dice games between algorithmic players. Drop in a player file, implement one method, and compete.

## Running

```bash
uv run python -m game [N_GAMES] [TOP_N]
```

- `N_GAMES` - number of games to play (default: 1)
- `TOP_N` - how many top-ranked leaderboard players to include (default: 4)

Console shows one result line per game followed by a summary table. Full debug logs (including all rolled hands) are written to `gamelog.log`, overwritten each game.

## Rules

Each player starts with **5 dice**. Each round:

1. All active players roll their dice in secret.
2. Starting from a random player, players take turns bidding - claiming there are at least *N* dice showing face *F* across all hands combined.
3. Each bid must raise the previous one: either increase the quantity, or keep the quantity and increase the face value.
4. Instead of bidding, any player may call **liar** on the previous bid.
5. All dice are revealed. If the bid holds (total matching dice ≥ claimed quantity), the challenger loses a die. If it fails, the bidder loses a die.
6. The **winner** of each challenge leads the next round.
7. A player eliminated when their dice reach 0. Last player standing wins.

### 1s as wilds

By default, **1s count as wild** - they satisfy any non-1 bid. However, if the opening bid of a round is on face 1, then:
- 1s are **not** wild for that round (they are only counted literally).
- 1s **cannot** be bid at all if the opening bid was on any other face.

## CI / Leaderboard

The workflow runs automatically on any PR that changes `players/*`.

**Player selection per run:** the top `TOP_N` (default 4) players by all-time win rate are selected from `leaderboard.yaml`, plus any challengers (players whose file is in `players/` but not yet in the leaderboard).

**Challenger admission:** a new player is added to `leaderboard.yaml` only if their win rate in the run **strictly exceeds** the lowest-ranked established player's all-time win rate. If they qualify, the leaderboard is committed back to the PR branch and the PR is merged automatically. If they don't clear the bar, the workflow fails and the PR is left open.

**Configurable variables:** `N_GAMES` and `TOP_N` can be set as repository variables (Settings → Secrets and variables → Actions → Variables) to tune each run without touching the workflow file.

## Adding a Player

Create a `.py` file in `players/` with a `Player` class:

```python
from game.components.bets import Bet

class Player:
    def __init__(self):
        self.name = "YourName"

    def algo(
        self,
        hand: list[int],
        prior_bet: Bet | None,
        total_dice: int,
        bet_history: list[dict],
        outcomes: list[dict],
    ) -> Bet | None:
        ...
```

The engine loads all `Player` classes from `players/` and selects the active field based on leaderboard rank (see CI / Leaderboard above).

### `algo` inputs

| Parameter | Type | Description |
|---|---|---|
| `hand` | `list[int]` | Your current dice (values 1–6) |
| `prior_bet` | `Bet \| None` | The last bid placed, or `None` if you are opening the round |
| `total_dice` | `int` | Total dice in play across all active players |
| `bet_history` | `list[dict]` | Every accepted bid this game, oldest first |
| `outcomes` | `list[dict]` | Revealed hands and results from all completed rounds |

### Return value

- Return a `Bet(quantity, face, self.name)` to place a bid.
- Return `None` to call liar. *(Not allowed on the opening bid.)*

Returning an invalid bid (one that doesn't raise the prior bet, or bids 1s when the round didn't open on 1s) is penalised - you lose a die.

### `Bet`

```python
Bet(quantity: int, face: int, player: str)

bet.quantity  # int  - claimed number of matching dice
bet.face      # int  - claimed face value (1–6)
bet.player    # str  - name of the player who placed it
```

### `bet_history` entries

```python
{
    "round":  int,  # round number
    "player": str,  # player name
    "bet":    Bet,  # the bid placed
}
```

### `outcomes` entries

One entry is appended per round, at the moment liar is called and hands are revealed.

```python
{
    "round":      int,        # round number
    "hands":      dict,       # {player_name: [dice]} for all players that round
    "final_bet":  Bet,        # the bid that was challenged
    "bidder":     str,        # who placed the final bet
    "challenger": str,        # who called liar
    "bet_held":   bool,       # True if the bid held up
    "loser":      str,        # who lost a die
}
```

Both structures also carry a `"game"` field. When running a series, `bet_history` and `outcomes` persist across all games - join on `("game", "round")` to reconstruct any past round in full.

## Project structure

```
game/
  __main__.py          # entry point, logging config, player selection
  components/
    script.py          # game loop and orchestration
    bets.py            # Bet class, bet_validator, bet_grader
    series.py          # series runner and results formatter
    leaderboard.py     # leaderboard read/write with challenger gating
    utils.py           # dice rolling, player loader

players/
  alice.py             # balanced strategy
  bruno.py             # aggressive strategy
  cleo.py              # cautious strategy
  diego.py             # hand-anchored strategy

leaderboard.yaml       # persistent rankings across CI runs
gamelog.log            # full debug log from last run (not committed)
```
