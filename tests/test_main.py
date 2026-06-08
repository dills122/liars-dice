import json
import os
import subprocess
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def run_game(args: list[str], leaderboard: dict, tmp_path: Path) -> dict:
    """Run `python -m game` with a temp leaderboard, return parsed results JSON."""
    lb_path = tmp_path / "leaderboard.yaml"
    lb_path.write_text(yaml.dump(leaderboard, default_flow_style=False, sort_keys=False))

    results_path = tmp_path / "results.json"
    cmd = [
        "uv", "run", "python", "-m", "game",
        *args,
        "--results-file", str(results_path),
    ]
    env = {**os.environ, "LEADERBOARD_PATH": str(lb_path)}
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr

    if results_path.exists():
        return json.loads(results_path.read_text())
    return {}


def test_tier_prm_selects_only_prm_players(tmp_path):
    """--tier PRM runs only PRM players."""
    lb = {
        "total_runs": 1,
        "pending_relegation": [],
        "players": {
            "Alice": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 40, "total_games": 100, "win_pct": 40.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"tier": "CH", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 30, "total_games": 100, "win_pct": 30.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }
    results = run_game(["--tier", "PRM", "10", "4"], lb, tmp_path)
    assert "Alice" in results
    assert "Bruno" not in results


def test_tier_l1_includes_inactive_players(tmp_path):
    """--tier L1 runs L1 and inactive players together."""
    lb = {
        "total_runs": 1,
        "pending_relegation": [],
        "players": {
            "Alice": {"tier": "L1", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 40, "total_games": 100, "win_pct": 40.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"tier": "inactive", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 30, "total_games": 100, "win_pct": 30.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 2},
            "Cleo": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                     "total_wins": 50, "total_games": 100, "win_pct": 50.0,
                     "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }
    results = run_game(["--tier", "L1", "10", "4"], lb, tmp_path)
    assert "Alice" in results
    assert "Bruno" in results
    assert "Cleo" not in results


def test_results_file_written(tmp_path):
    """--results-file writes a JSON dict of {player: wins}."""
    lb = {
        "total_runs": 1,
        "pending_relegation": [],
        "players": {
            "Alice": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 40, "total_games": 100, "win_pct": 40.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 30, "total_games": 100, "win_pct": 30.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }
    results = run_game(["--tier", "PRM", "5", "4"], lb, tmp_path)
    total = sum(results.values())
    assert total == 5  # exactly N_GAMES wins distributed


def test_no_leaderboard_update_written(tmp_path):
    """Running the game must NOT modify leaderboard.yaml."""
    lb = {
        "total_runs": 1,
        "pending_relegation": [],
        "players": {
            "Alice": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 40, "total_games": 100, "win_pct": 40.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"tier": "PRM", "date_added": "2026-01-01T00:00:00Z",
                      "total_wins": 30, "total_games": 100, "win_pct": 30.0,
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }
    lb_path = tmp_path / "leaderboard.yaml"
    lb_path.write_text(yaml.dump(lb, default_flow_style=False, sort_keys=False))
    original_content = lb_path.read_text()

    results_path = tmp_path / "results.json"
    env = {**os.environ, "LEADERBOARD_PATH": str(lb_path)}
    subprocess.run(
        ["uv", "run", "python", "-m", "game", "--tier", "PRM",
         "--results-file", str(results_path), "5", "4"],
        cwd=REPO_ROOT, capture_output=True, check=True, env=env,
    )
    assert lb_path.read_text() == original_content
