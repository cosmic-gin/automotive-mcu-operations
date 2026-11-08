import json

import pandas as pd

from mcu_ops.analytics import Analytics, Filters
from mcu_ops.config import settings
from mcu_ops.data_generation.generator import Simulation, write_sources
from mcu_ops.database import make_engine, replace_snapshot
from mcu_ops.etl import run_etl
from mcu_ops.tableau import export_tableau


def test_export_grains_and_additive_components(tmp_path, monkeypatch):
    monkeypatch.setenv("MCU_BACKEND", "duckdb")
    monkeypatch.setenv("MCU_DATA_DIR", str(tmp_path))
    source = tmp_path / "raw"
    write_sources(source, Simulation(months=6, daily_orders=4))
    engine = make_engine(settings())
    try:
        replace_snapshot(engine, run_etl(source, tmp_path / "etl"))
        analytics = Analytics(engine)
        output = tmp_path / "exports"
        rows = export_tableau(analytics, output, Filters(analytics.start, analytics.as_of))
    finally:
        engine.dispose()

    frames = {name: pd.read_csv(output / f"{name}.csv") for name in rows}
    assert rows == {name: len(frame) for name, frame in frames.items()}
    summary = frames["executive_kpis"].iloc[0]
    monthly = frames["monthly_delivery_performance"]
    assert len(frames["executive_kpis"]) == 1
    assert not monthly.duplicated(["month", "product_category", "product_family"]).any()
    assert monthly.month.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
    assert monthly.due_orders.sum() == summary.due_orders
    assert monthly.on_time_orders.sum() == summary.on_time_orders
    assert frames["product_performance"].product_id.is_unique
    assert frames["production_quality"].lot_id.is_unique
    assert frames["production_quality"].passed_units.sum() == summary.passed_units
    assert frames["order_backlog"].order_id.is_unique
    assert frames["order_backlog"].remaining_units.sum() == summary.backlog_units
    manifest = json.loads((output / "export_manifest.json").read_text(encoding="utf-8"))
    assert manifest["fictional"] is True
    assert manifest["row_counts"] == rows
