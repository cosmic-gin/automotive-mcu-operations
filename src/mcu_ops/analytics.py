"""Execute shared SQL with typed filters and turn calculated results into alerts."""
from dataclasses import dataclass, replace
from datetime import date, timedelta
from functools import lru_cache

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from mcu_ops.config import Settings
from mcu_ops.database import metadata, sql_source

QUERIES = {"performance", "monthly", "orders", "lots", "inventory", "lot_link"}


@dataclass(frozen=True)
class Filters:
    start: date
    end: date
    category: str = ""
    family: str = ""
    segment: str = ""

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("The start date must be on or before the end date")

    def previous(self) -> "Filters":
        length = self.end - self.start + timedelta(days=1)
        return replace(self, start=self.start - length, end=self.start - timedelta(days=1))


@dataclass(frozen=True)
class Alert:
    metric: str
    message: str
    investigation: str


@lru_cache
def _statement(query: str) -> str:
    return sql_source("kpis", "context.sql") + sql_source("kpis", f"{query}.sql")


class Analytics:
    """Query one loaded snapshot. Both engines use the same KPI SQL."""

    def __init__(self, bind: Engine | Connection):
        self.bind = bind
        self.quality = metadata(bind)
        self.start = date.fromisoformat(self.quality["start"])
        self.as_of = date.fromisoformat(self.quality["as_of"])

    def products(self) -> pd.DataFrame:
        return pd.read_sql_query(
            text("SELECT product_id, product_name, product_category, product_family " "FROM products ORDER BY product_category, product_family, product_id"),
            self.bind,
        )

    def query(self, query: str, filters: Filters, *, grain: str = "all",
              yield_target: float = 97) -> pd.DataFrame:
        if query not in QUERIES or grain not in {"all", "category", "family", "product"}:
            raise ValueError("Unknown analytical query or grouping")
        sql = text(_statement(query))
        params = {
            "start": max(filters.start, self.start), "cutoff": min(filters.end, self.as_of),
            "category": filters.category, "family": filters.family, "segment": filters.segment,
            "grain": grain, "yield_target": yield_target,
        }
        return pd.read_sql_query(sql, self.bind, params=params)

    def headline(self, filters: Filters) -> dict:
        frame = self.query("performance", filters)
        if frame.empty:
            return {}
        return {key: None if pd.isna(value) else value for key, value in frame.iloc[0].items()}


def alerts(current: dict, previous: dict, quality: dict, config: Settings) -> list[Alert]:
    """Compare observed values with fictional targets and equal-length prior periods."""
    result = []
    for key, name, target, action in (
        ("on_time_pct", "On-time delivery", config.otd_target, "Review due orders and split dispatches."),
        ("yield_pct", "Production yield", config.yield_target, "Review tested lots and affected families."),
        ("min_inventory_units", "SKU inventory", config.inventory_floor, "Review SKU stock observations."),
    ):
        value = current.get(key)
        if value is not None and value < target:
            unit = " units" if key == "min_inventory_units" else "%"
            result.append(Alert(name, f"{value:,.1f}{unit} is below the {target:g}{unit} target.", action))
    before = previous.get("backlog_units")
    after = current.get("backlog_units")
    if before and after is not None:
        growth = 100 * (after - before) / before
        if growth > config.backlog_growth_target:
            result.append(Alert("Backlog", f"Outstanding units rose {growth:.1f}% versus the prior cutoff.",
                                "Rank open orders by SKU and promise date."))
    stale = [item["table"] for item in quality["freshness"] if item["status"] == "failed"]
    if stale:
        result.append(Alert("Source freshness", ", ".join(stale), "Check the source delivery manifest."))
    if quality["schema_failures"]:
        result.append(Alert("Source schema", "Required columns were missing.", "Inspect the run audit."))
    rate = quality["rejection_pct"]
    if rate is not None and rate > config.dq_max:
        result.append(Alert("Data quality", f"{rate:.2f}% rejected against a {config.dq_max:g}% limit.",
                            "Inspect quarantined records and primary failure rules."))
    return result


def executive_summary(metrics: dict, categories: pd.DataFrame) -> str:
    if not metrics or not metrics["due_orders"]:
        return "The selected period has no due-order observations."
    summary = (
        f"{metrics['on_time_orders']:,.0f} of {metrics['due_orders']:,.0f} due orders shipped in full "
        f"by their promise date ({metrics['on_time_pct']:.1f}%). At cutoff, "
        f"{metrics['backlog_units']:,.0f} units remained open across "
        f"{metrics['open_orders']:,.0f} orders."
    )
    observed = categories.dropna(subset=["on_time_pct"])
    if not observed.empty:
        lowest = observed.loc[observed.on_time_pct.idxmin()]
        summary += f" {lowest.group_name} had the lowest observed on-time rate ({lowest.on_time_pct:.1f}%)."
    return summary
