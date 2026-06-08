#!/usr/bin/env python3
"""
Evaluate game results, apply cascade logic, update leaderboard, write PR comment.

Required environment variables:
  CHALLENGER        player name from the PR
  CHALLENGER_TIER   tier they entered (PRM or CH)
  PHASE             1, 2, or 3
  N_GAMES           games per run (int)
  TOP_N             league size cap (int)
"""
import json
import os
import yaml
from game.components.leaderboard import (
    apply_pending_relegation,
    get_tier_players,
    update_leaderboard,
)

TIER_LABELS = {
    "PRM": "Premier Division",
    "CH": "Championship",
    "L1": "League One",
    "inactive": "Inactive",
}


def load_results(prefix: str) -> dict[str, int] | None:
    path = f"{prefix}_results.json"
    return json.loads(open(path).read()) if os.path.exists(path) else None


def load_output(prefix: str) -> str:
    path = f"{prefix}_output.txt"
    return open(path).read().strip() if os.path.exists(path) else ""


def ranked(results: dict[str, int], lb_data: dict | None = None) -> list[tuple[str, int]]:
    """Sort by wins desc; tiebreak on total_games desc then tier_since asc."""
    players = (lb_data or {}).get("players", {})
    def _key(item: tuple[str, int]):
        name, wins = item
        p = players.get(name, {})
        return (-wins, -p.get("total_games", 0), p.get("tier_since", ""))
    return sorted(results.items(), key=_key)


def main():
    challenger = os.environ["CHALLENGER"]
    challenger_tier = os.environ["CHALLENGER_TIER"]
    phase = int(os.environ["PHASE"])
    n_games = int(os.environ["N_GAMES"])

    with open("leaderboard.yaml") as f:
        lb = yaml.safe_load(f) or {}
    lb = apply_pending_relegation(lb)

    entry_prefix = challenger_tier.lower()
    entry_results = load_results(entry_prefix)
    prm_results = load_results("prm") if challenger_tier == "CH" else None
    l1_results = load_results("l1")

    # Per-tier promotion/relegation decisions
    entry_promotions: dict[str, str] = {}
    entry_pending: list[dict] = []
    prm_pending: list[dict] = []
    l1_promotions: dict[str, str] = {}
    l1_pending: list[dict] = []
    last_in_l1: str | None = None

    # --- Entry league cascade ---
    if entry_results:
        r = ranked(entry_results, lb)
        winner, last = r[0][0], r[-1][0]
        existing = set(get_tier_players(lb, challenger_tier))

        if challenger_tier == "CH":
            # Winner → PRM
            entry_promotions[winner] = "PRM"

            # Challenger placement
            if challenger == winner:
                pass  # promoted to PRM, not admitted to CH
            elif phase == 3 and challenger == last:
                entry_promotions[challenger] = "L1"
            else:
                entry_promotions[challenger] = "CH"

            # Existing CH bottom → pending to L1 (Phase 3 only, not winner)
            if phase == 3 and existing:
                existing_results = {k: v for k, v in entry_results.items()
                                    if k in existing}
                if existing_results:
                    ch_bottom = min(existing_results, key=existing_results.get)
                    if ch_bottom != winner:
                        entry_pending.append({
                            "player": ch_bottom,
                            "from_tier": "CH",
                            "to_tier": "L1",
                        })

        else:  # Phase 1: challenger enters PRM
            entry_promotions[challenger] = "PRM"

    # --- PRM cascade ---
    if prm_results:
        r = ranked(prm_results, lb)
        prm_last = r[-1][0]
        prm_pending.append({
            "player": prm_last,
            "from_tier": "PRM",
            "to_tier": "CH",
        })

    # --- L1 cascade ---
    if l1_results:
        r = ranked(l1_results, lb)
        l1_winner, last_in_l1 = r[0][0], r[-1][0]
        l1_promotions[l1_winner] = "CH"
        l1_roster = set(get_tier_players(lb, "L1"))
        from_tier = "L1" if last_in_l1 in l1_roster else "inactive"
        l1_pending.append({
            "player": last_in_l1,
            "from_tier": from_tier,
            "to_tier": "inactive",
        })

    # --- Write leaderboard updates ---
    if entry_results:
        update_leaderboard(
            wins=entry_results,
            n_games=n_games,
            tier=challenger_tier,
            promotions=entry_promotions,
            pending_relegations=entry_pending,
        )
    if prm_results:
        update_leaderboard(
            wins=prm_results,
            n_games=n_games,
            tier="PRM",
            promotions={},
            pending_relegations=prm_pending,
        )
    if l1_results:
        update_leaderboard(
            wins=l1_results,
            n_games=n_games,
            tier="L1",
            promotions=l1_promotions,
            pending_relegations=l1_pending,
            last_place=last_in_l1,
        )

    _write_comment(
        challenger=challenger,
        challenger_tier=challenger_tier,
        entry_promotions=entry_promotions,
        entry_pending=entry_pending,
        prm_pending=prm_pending,
        l1_promotions=l1_promotions,
        l1_pending=l1_pending,
        entry_prefix=entry_prefix,
        prm_results=prm_results,
        l1_results=l1_results,
    )


def _write_comment(
    challenger, challenger_tier, entry_promotions, entry_pending,
    prm_pending, l1_promotions, l1_pending,
    entry_prefix, prm_results, l1_results,
):
    with open("leaderboard.yaml") as f:
        lb = yaml.safe_load(f) or {}
    players = lb.get("players", {})

    challenger_dest = entry_promotions.get(challenger, challenger_tier)
    summary = f"**{challenger}** → {TIER_LABELS[challenger_dest]}"

    all_pending = entry_pending + prm_pending + l1_pending
    pending_notes = [
        f"- {p['player']}: {TIER_LABELS[p['from_tier']]} → "
        f"{TIER_LABELS[p['to_tier']]} *(takes effect next PR)*"
        for p in all_pending
    ]

    table = ["| Player | Tier | Win % | Games | Tier Since |",
             "|--------|------|-------|-------|------------|"]
    for tier_key in ("PRM", "CH", "L1", "inactive"):
        tier_players = sorted(
            [(n, p) for n, p in players.items() if p.get("tier") == tier_key],
            key=lambda x: x[1].get("win_pct", 0), reverse=True,
        )
        for name, p in tier_players:
            bold = "**" if name == challenger else ""
            table.append(
                f"| {bold}{name}{bold} | {TIER_LABELS[tier_key]} | "
                f"{p.get('win_pct', 0)}% | {p.get('total_games', 0)} | "
                f"{str(p.get('tier_since', ''))[:10]} |"
            )

    fence = "```"
    sections = [f"## 🎲 {summary}\n"]

    if all_pending:
        sections.append("**Pending next PR:**\n" + "\n".join(pending_notes) + "\n")

    for prefix, label in [
        (entry_prefix, TIER_LABELS[challenger_tier]),
        ("prm", "Premier Division"),
        ("l1", "League One"),
    ]:
        output = load_output(prefix)
        if output:
            sections.append(
                f"<details><summary>{label} results</summary>\n\n"
                f"{fence}\n{output}\n{fence}\n</details>\n"
            )

    sections.append("### Full Leaderboard\n\n" + "\n".join(table))

    with open("comment.md", "w") as f:
        f.write("\n".join(sections))


if __name__ == "__main__":
    main()
