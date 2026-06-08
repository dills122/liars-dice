import logging
import os
import yaml
from pathlib import Path

project_root = Path(__file__).parent.parent

N_GAMES = int(__import__("sys").argv[1]) if len(__import__("sys").argv) > 1 else 1
TOP_N = int(__import__("sys").argv[2]) if len(__import__("sys").argv) > 2 else 4

# File handler: full DEBUG trace for every game
file_handler = logging.FileHandler("gamelog.log", mode="w")
file_handler.setLevel(logging.DEBUG)

# Console handler: series progress only (one line per game)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_fmt = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_fmt)


class _GameFormatter(logging.Formatter):
    """Minimal console format: message only, level prefix for warnings."""

    def format(self, record):
        msg = record.getMessage()
        if not msg:
            return ""
        if record.levelno >= logging.WARNING:
            return f"[{record.levelname}] {msg}"
        return msg


class _SeriesConsoleFilter(logging.Filter):
    """Restricts console output to series-level progress only.
    File handler receives everything unfiltered.
    """
    def filter(self, record):
        return record.name == "game.components.series"


console_handler.setFormatter(_GameFormatter())
console_handler.addFilter(_SeriesConsoleFilter())

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

from game.components.series import run_series, format_results  # noqa: E402
from game.components.utils import import_player_classes_from_dir  # noqa: E402
from game.components.leaderboard import update_leaderboard  # noqa: E402

# Determine established players from leaderboard (ranked by win_pct)
_lb_path = project_root / "leaderboard.yaml"
_lb_data = yaml.safe_load(open(_lb_path)) if _lb_path.exists() else {}
_lb_players = _lb_data.get("players", {})
_ranked = sorted(_lb_players, key=lambda n: _lb_players[n].get("win_pct", 0), reverse=True)
_top_n = set(_ranked[:TOP_N])

# Load all player files; select top N established + any challengers (not yet in leaderboard)
all_players = import_player_classes_from_dir(str(project_root / "players"))
players = [p for p in all_players if p.name in _top_n or p.name not in _lb_players]

print(f"Playing: {[p.name for p in players]} (top {TOP_N} + challengers)")

wins = run_series(players, N_GAMES)
print(format_results(wins, N_GAMES))
update_leaderboard(wins, N_GAMES, TOP_N)
