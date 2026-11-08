from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine

from mcu_ops.analytics import Analytics, Filters
from mcu_ops.data_generation.generator import COLUMNS
from mcu_ops.database import replace_snapshot, snapshot_reader
from mcu_ops.etl import validate


@pytest.fixture
def hand_snapshot():
    values = {
        "products": [
            ("P1", "Aegis", "Safety-Control MCUs", "Safety", "1.00", "true"),
            ("P2", "Relay", "Body-Electronics MCUs", "Body", "2.00", "true"),
        ],
        "customer_orders": [
            ("A", "P1", "OEM", "2025-01-01", "2025-01-05", 100, "FULFILLED"),
            ("B", "P1", "Tier 1", "2025-01-01", "2025-01-05", 100, "FULFILLED"),
            ("C", "P1", "OEM", "2025-01-02", "2025-01-06", 100, "OPEN"),
            ("D", "P2", "OEM", "2025-01-10", "2025-02-01", 70, "OPEN"),
            ("E", "P2", "OEM", "2025-01-05", "2025-01-09", 50, "OPEN"),
        ],
        "shipments": [
            ("S1", "A", "L1", "2025-01-04", 80), ("S2", "A", "L1", "2025-01-05", 20),
            ("S3", "B", "", "2025-01-05", 40), ("S4", "B", "", "2025-01-08", 60),
            ("S5", "C", "", "2025-01-04", 25),
        ],
        "production_lots": [
            ("L1", "P1", "2025-01-01", 1000, 980, 20),
            ("L2", "P1", "2025-01-02", 10, 2, 8),
            ("L3", "P2", "2025-01-04", 0, 0, 0),
        ],
        "inventory_snapshots": [
            ("I1", "P1", "2025-01-01", 100), ("I2", "P1", "2025-01-10", 50),
            ("I3", "P2", "2025-01-10", 20),
        ],
    }
    frames = {
        name: pd.DataFrame(values[name], columns=columns.split()).astype(str)
        for name, columns in COLUMNS.items()
    }
    snapshot = validate(frames, {
        "start": "2025-01-01", "as_of": "2025-01-31",
        "source_dates": dict.fromkeys(COLUMNS, "2025-01-31"),
    })
    assert snapshot.quarantine.empty
    return snapshot


PERIOD = Filters(date(2025, 1, 1), date(2025, 1, 31))


def check_metrics(analytics):
    kpis = analytics.headline(PERIOD)
    assert kpis["due_orders"] == 4
    assert kpis["on_time_pct"] == 25
    assert kpis["fulfillment_pct"] == 40
    assert kpis["backlog_units"] == 195
    assert kpis["overdue_orders"] == 2
    assert kpis["partial_open_orders"] == 1
    assert kpis["late_dispatch_orders"] == 1
    assert kpis["yield_pct"] == pytest.approx(100 * 982 / 1010)
    assert kpis["defect_pct"] == pytest.approx(100 * 28 / 1010)
    assert kpis["avg_lead_days"] == 5.5
    assert kpis["inventory_units"] == 70
    body = analytics.headline(Filters(PERIOD.start, PERIOD.end, "Body-Electronics MCUs"))
    assert body["due_orders"] == 1
    assert body["yield_pct"] is None
    earlier = Filters(date(2025, 1, 5), date(2025, 1, 5), segment="OEM")
    assert analytics.headline(earlier)["on_time_pct"] == 100
    assert analytics.headline(earlier)["backlog_units"] == 125
    empty = Filters(PERIOD.start, PERIOD.end, "foo' OR 1=1 --")
    assert analytics.query("orders", empty).empty
    assert analytics.query("monthly", PERIOD).iloc[0].ordered_units == 420
    assert analytics.query("monthly", PERIOD).iloc[0].shipped_units == 225
    assert pd.isna(analytics.query("monthly", PERIOD).iloc[0].demand_growth_pct)
    assert len(analytics.query("lots", PERIOD)) == 3
    assert analytics.query("inventory", PERIOD).iloc[-1].inventory_units == 70
    assert analytics.query("lot_link", PERIOD).due_orders.sum() == 4
    return kpis


def test_duckdb_hand_calculated_kpis(hand_snapshot):
    engine = create_engine("duckdb:///:memory:")
    try:
        replace_snapshot(engine, hand_snapshot)
        check_metrics(Analytics(engine))
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_postgres_kpi_parity(hand_snapshot, postgres_engine):
    duck = create_engine("duckdb:///:memory:")
    try:
        replace_snapshot(duck, hand_snapshot)
        replace_snapshot(postgres_engine, hand_snapshot)
        expected = check_metrics(Analytics(duck))
        with snapshot_reader(postgres_engine) as connection:
            actual = check_metrics(Analytics(connection))
        assert actual.keys() == expected.keys()
        for key, value in expected.items():
            assert actual[key] == pytest.approx(value) if isinstance(value, float) else actual[key] == value
    finally:
        duck.dispose()
