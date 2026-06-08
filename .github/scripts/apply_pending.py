"""Apply pending_relegation entries to leaderboard.yaml in the current workspace."""
import yaml

with open("leaderboard.yaml") as f:
    data = yaml.safe_load(f) or {}

from game.components.leaderboard import apply_pending_relegation
data = apply_pending_relegation(data)

with open("leaderboard.yaml", "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
