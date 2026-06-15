"""Pattern: AI forecasting agent — demand forecasting, anomaly detection, forecast publishing."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_HISTORICAL_SALES: dict[str, list[dict]] = {
    "PROD-001": [
        {"period": "2026-01", "units": 320},
        {"period": "2026-02", "units": 295},
        {"period": "2026-03", "units": 410},
        {"period": "2026-04", "units": 388},
        {"period": "2026-05", "units": 430},
    ],
    "PROD-002": [
        {"period": "2026-01", "units": 80},
        {"period": "2026-02", "units": 75},
        {"period": "2026-03", "units": 90},
        {"period": "2026-04", "units": 85},
        {"period": "2026-05", "units": 110},
    ],
}

_PUBLISHED_FORECASTS: dict[str, dict] = {}


def _get_historical_sales(product_id: str, periods: int = 6) -> dict[str, Any]:
    history = _HISTORICAL_SALES.get(product_id)
    if not history:
        return {"error": f"Product {product_id} not found"}
    return {
        "product_id": product_id,
        "history": history[-periods:],
        "periods_returned": min(periods, len(history)),
    }


def _run_demand_forecast(product_id: str, horizon_days: int) -> dict[str, Any]:
    history = _HISTORICAL_SALES.get(product_id)
    if not history:
        return {"error": f"Product {product_id} not found"}
    avg_monthly = sum(p["units"] for p in history) / len(history)
    daily_avg = avg_monthly / 30
    forecast_units = round(daily_avg * horizon_days)
    trend = "increasing" if history[-1]["units"] > history[0]["units"] else "stable"
    return {
        "product_id": product_id,
        "horizon_days": horizon_days,
        "forecasted_units": forecast_units,
        "daily_average": round(daily_avg, 2),
        "trend": trend,
        "confidence_interval": {
            "lower": round(forecast_units * 0.85),
            "upper": round(forecast_units * 1.15),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


def _detect_anomalies(metric: str, data_points: list[float]) -> dict[str, Any]:
    if len(data_points) < 3:
        return {"error": "Need at least 3 data points for anomaly detection"}
    mean = sum(data_points) / len(data_points)
    variance = sum((x - mean) ** 2 for x in data_points) / len(data_points)
    std = variance**0.5
    threshold = 2.0 * std
    anomalies = [
        {"index": i, "value": v, "deviation": round(abs(v - mean), 2)}
        for i, v in enumerate(data_points)
        if abs(v - mean) > threshold
    ]
    return {
        "metric": metric,
        "data_points": len(data_points),
        "mean": round(mean, 2),
        "std_dev": round(std, 2),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def _publish_forecast(product_id: str, forecast: dict) -> dict[str, Any]:
    _PUBLISHED_FORECASTS[product_id] = {
        "product_id": product_id,
        "forecast": forecast,
        "published_at": datetime.utcnow().isoformat(),
        "status": "published",
    }
    return _PUBLISHED_FORECASTS[product_id]


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "get_historical_sales",
        "description": "Retrieve historical sales data for a product over a number of past periods.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. PROD-001)",
                },
                "periods": {
                    "type": "integer",
                    "description": "Number of historical periods to retrieve (default 6)",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "run_demand_forecast",
        "description": "Run a demand forecast for a product over a given horizon in days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID"},
                "horizon_days": {
                    "type": "integer",
                    "description": "Forecast horizon in days",
                },
            },
            "required": ["product_id", "horizon_days"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Detect statistical anomalies in a list of numeric data points for a given metric.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Name of the metric being analysed",
                },
                "data_points": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numeric values to analyse for anomalies",
                },
            },
            "required": ["metric", "data_points"],
        },
    },
    {
        "name": "publish_forecast",
        "description": "Publish a validated forecast to the demand planning system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID"},
                "forecast": {
                    "type": "object",
                    "description": "Forecast data dict to publish",
                },
            },
            "required": ["product_id", "forecast"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Demand Forecasting Agent for supply chain and inventory planning.
Your responsibilities:
1. Retrieve historical sales data to understand demand patterns
2. Run forward-looking demand forecasts for the required horizon
3. Detect anomalies in sales data that may indicate data quality issues or unexpected events
4. Publish validated forecasts to the demand planning system

Always retrieve historical data before running forecasts. Flag anomalies for review before publishing.
Include confidence intervals in all published forecasts."""


class ForecastingAgent(BaseERPAgent):
    """Generates and publishes demand forecasts with anomaly detection."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_historical_sales":
                return _get_historical_sales(**inputs)
            case "run_demand_forecast":
                return _run_demand_forecast(**inputs)
            case "detect_anomalies":
                return _detect_anomalies(**inputs)
            case "publish_forecast":
                return _publish_forecast(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
