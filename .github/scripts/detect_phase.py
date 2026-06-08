"""Detect phase, challenger tier, and pending L1 relegation. Writes to GITHUB_OUTPUT."""
import os
import yaml

with open("leaderboard.yaml") as f:
    lb = yaml.safe_load(f) or {}

top_n = int(os.environ["TOP_N"])
total = len(lb.get("players", {}))
phase = 1 if total < top_n else (2 if total <= top_n * 2 else 3)
challenger_tier = "PRM" if phase == 1 else "CH"
pending = lb.get("pending_relegation", [])
pending_l1 = any(p.get("to_tier") == "L1" for p in pending)

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"phase={phase}\n")
    f.write(f"challenger_tier={challenger_tier}\n")
    f.write(f"pending_l1_relegation={'true' if pending_l1 else 'false'}\n")
