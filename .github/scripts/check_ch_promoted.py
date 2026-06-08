"""Check if the CH run produced a promotion candidate. Writes ch_promoted to GITHUB_OUTPUT."""
import json
import os
import yaml

tier = os.environ["CHALLENGER_TIER"]
prefix = tier.lower()

with open(f"{prefix}_results.json") as f:
    results = json.load(f)

with open("leaderboard.yaml") as f:
    lb = yaml.safe_load(f) or {}

tier_players = [n for n, p in lb.get("players", {}).items() if p.get("tier") == tier]
# CH promoted if at least one existing tier player competed (winner goes to PRM)
ch_promoted = tier == "CH" and len(tier_players) >= 1

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"ch_promoted={'true' if ch_promoted else 'false'}\n")
