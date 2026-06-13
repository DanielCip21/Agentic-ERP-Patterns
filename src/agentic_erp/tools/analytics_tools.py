"""Simulated game analytics tools: player cohorts, revenue breakdown, AI revenue forecasting."""

from __future__ import annotations

import uuid
import random
from datetime import datetime
from typing import Any


_GAMES: dict[str, dict] = {
    "GAME-01": {"game_id": "GAME-01", "title": "Realm Siege Online", "genre": "MMORPG", "regions": ["NA", "EU", "APAC"], "launch_date": "2024-03-01"},
    "GAME-02": {"game_id": "GAME-02", "title": "Mech Blitz Arena", "genre": "Battle Royale", "regions": ["NA", "APAC"], "launch_date": "2025-01-15"},
    "GAME-03": {"game_id": "GAME-03", "title": "Fantasy Draft Manager", "genre": "Sports Strategy", "regions": ["NA", "EU", "AU"], "launch_date": "2023-09-10"},
}

_COHORTS: dict[str, dict] = {
    "C-2024Q1": {"cohort_id": "C-2024Q1", "game_id": "GAME-01", "players": 142_000, "day7_retention": 0.42, "day30_retention": 0.21, "avg_ltv_usd": 48.50, "churn_rate_monthly": 0.18},
    "C-2025Q1": {"cohort_id": "C-2025Q1", "game_id": "GAME-02", "players": 89_000, "day7_retention": 0.55, "day30_retention": 0.29, "avg_ltv_usd": 31.20, "churn_rate_monthly": 0.12},
    "C-2023Q3": {"cohort_id": "C-2023Q3", "game_id": "GAME-03", "players": 34_000, "day7_retention": 0.38, "day30_retention": 0.18, "avg_ltv_usd": 62.00, "churn_rate_monthly": 0.22},
}

_REVENUE_DATA: dict[str, dict] = {
    "GAME-01": {
        "2026-Q1": {"iap_usd": 4_200_000, "subscriptions_usd": 1_100_000, "ads_usd": 320_000, "battle_pass_usd": 890_000},
        "2026-Q2": {"iap_usd": 3_950_000, "subscriptions_usd": 1_180_000, "ads_usd": 295_000, "battle_pass_usd": 1_020_000},
    },
    "GAME-02": {
        "2026-Q1": {"iap_usd": 2_100_000, "subscriptions_usd": 450_000, "ads_usd": 180_000, "battle_pass_usd": 670_000},
        "2026-Q2": {"iap_usd": 2_480_000, "subscriptions_usd": 520_000, "ads_usd": 210_000, "battle_pass_usd": 780_000},
    },
    "GAME-03": {
        "2026-Q1": {"iap_usd": 980_000, "subscriptions_usd": 220_000, "ads_usd": 95_000, "battle_pass_usd": 0},
        "2026-Q2": {"iap_usd": 860_000, "subscriptions_usd": 240_000, "ads_usd": 88_000, "battle_pass_usd": 0},
    },
}


def get_player_cohort(cohort_id: str) -> dict[str, Any]:
    cohort = _COHORTS.get(cohort_id)
    if not cohort:
        return {"error": f"Cohort {cohort_id} not found"}
    game = _GAMES.get(cohort["game_id"], {})
    return {
        **cohort,
        "game_title": game.get("title", "Unknown"),
        "total_cohort_value_usd": round(cohort["players"] * cohort["avg_ltv_usd"], 2),
        "health": "STRONG" if cohort["day30_retention"] >= 0.25 else "WEAK",
    }


def get_revenue_breakdown(game_id: str, period: str) -> dict[str, Any]:
    game = _GAMES.get(game_id)
    if not game:
        return {"error": f"Game {game_id} not found"}
    periods = _REVENUE_DATA.get(game_id, {})
    data = periods.get(period)
    if not data:
        return {"error": f"No revenue data for game {game_id} in period {period}. Available: {list(periods)}"}
    total = sum(data.values())
    breakdown = {k: {"amount_usd": v, "pct_of_total": round(v / total * 100, 1) if total else 0} for k, v in data.items()}
    return {
        "game_id": game_id,
        "game_title": game["title"],
        "period": period,
        "total_revenue_usd": total,
        "breakdown": breakdown,
    }


def forecast_game_revenue(game_id: str, horizon_months: int = 12) -> dict[str, Any]:
    game = _GAMES.get(game_id)
    if not game:
        return {"error": f"Game {game_id} not found"}
    all_periods = _REVENUE_DATA.get(game_id, {})
    if not all_periods:
        return {"error": f"No historical revenue data for {game_id}"}
    latest = list(all_periods.values())[-1]
    base_monthly = sum(latest.values()) / 3  # quarterly → monthly
    growth_rates = {"MMORPG": 0.015, "Battle Royale": 0.022, "Sports Strategy": 0.008}
    monthly_growth = growth_rates.get(game["genre"], 0.012)
    forecasts = []
    for i in range(1, horizon_months + 1):
        projected = round(base_monthly * ((1 + monthly_growth) ** i) * (1 + random.uniform(-0.04, 0.04)), 2)
        forecasts.append({"month_offset": i, "projected_revenue_usd": projected})
    return {
        "game_id": game_id,
        "game_title": game["title"],
        "genre": game["genre"],
        "horizon_months": horizon_months,
        "monthly_growth_rate_pct": round(monthly_growth * 100, 2),
        "forecast": forecasts,
        "total_projected_usd": round(sum(f["projected_revenue_usd"] for f in forecasts), 2),
        "forecast_generated_at": datetime.utcnow().isoformat(),
    }
