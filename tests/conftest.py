import pytest


@pytest.fixture
def minimal_lb():
    """Two players, both in PRM. Phase 1 with TOP_N=4."""
    return {
        "total_runs": 2,
        "last_updated": "2026-01-01T00:00:00Z",
        "pending_relegation": [],
        "players": {
            "Alice": {
                "date_added": "2026-01-01T00:00:00Z",
                "total_wins": 40,
                "total_games": 100,
                "win_pct": 40.0,
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_last_in_l1": 0,
            },
            "Bruno": {
                "date_added": "2026-01-01T00:00:00Z",
                "total_wins": 30,
                "total_games": 100,
                "win_pct": 30.0,
                "tier": "PRM",
                "tier_since": "2026-01-01T00:00:00Z",
                "times_last_in_l1": 0,
            },
        },
    }


@pytest.fixture
def full_two_tier_lb():
    """Four players: 2 PRM, 2 CH. Phase 2 with TOP_N=2."""
    return {
        "total_runs": 5,
        "last_updated": "2026-01-01T00:00:00Z",
        "pending_relegation": [],
        "players": {
            "Alice": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 40,
                      "total_games": 100, "win_pct": 40.0, "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 30,
                      "total_games": 100, "win_pct": 30.0, "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Cleo": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 20,
                     "total_games": 100, "win_pct": 20.0, "tier": "CH",
                     "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Diego": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 10,
                      "total_games": 100, "win_pct": 10.0, "tier": "CH",
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }


@pytest.fixture
def lb_with_pending():
    """Leaderboard with a pending PRM→CH relegation."""
    return {
        "total_runs": 3,
        "last_updated": "2026-01-01T00:00:00Z",
        "pending_relegation": [
            {"player": "Alice", "from_tier": "PRM", "to_tier": "CH"}
        ],
        "players": {
            "Alice": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 40,
                      "total_games": 100, "win_pct": 40.0, "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
            "Bruno": {"date_added": "2026-01-01T00:00:00Z", "total_wins": 30,
                      "total_games": 100, "win_pct": 30.0, "tier": "PRM",
                      "tier_since": "2026-01-01T00:00:00Z", "times_last_in_l1": 0},
        },
    }


@pytest.fixture
def lb_file(tmp_path, minimal_lb):
    """Write minimal_lb to a temp file and return its path."""
    import yaml
    path = tmp_path / "leaderboard.yaml"
    path.write_text(yaml.dump(minimal_lb, default_flow_style=False, sort_keys=False))
    return str(path)
