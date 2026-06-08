import os
import yaml
from datetime import datetime, timezone

_LEADERBOARD_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "leaderboard.yaml")
)


def update_leaderboard(wins: dict[str, int], n_games: int, top_n: int = 4, path: str = _LEADERBOARD_PATH) -> None:
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data.setdefault("total_runs", 0)
    data["total_runs"] += 1
    data["last_updated"] = now
    data.setdefault("players", {})

    for name, win_count in wins.items():
        # Challengers must beat the lowest-ranked established player's win rate to be added
        if name not in data["players"]:
            if data["players"]:
                min_win_pct = min(p["win_pct"] for p in data["players"].values())
                if round(win_count / n_games * 100, 1) <= min_win_pct:
                    continue
            elif win_count == 0:
                continue
        player = data["players"].setdefault(name, {
            "date_added": now,
            "total_wins": 0,
            "total_games": 0,
            "win_pct": 0.0,
        })
        player["total_wins"] += win_count
        player["total_games"] += n_games
        player["win_pct"] = round(player["total_wins"] / player["total_games"] * 100, 1)

    # Sort by descending win_pct and mark top N as active
    ranked = sorted(data["players"], key=lambda n: data["players"][n]["win_pct"], reverse=True)
    top_n_names = set(ranked[:top_n])
    data["players"] = {
        name: {**data["players"][name], "is_active": name in top_n_names}
        for name in ranked
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
