import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from mcu_ops.data_generation.generator import Simulation, write_sources
from mcu_ops.database import metadata, replace_snapshot
from mcu_ops.etl import run_etl


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    root = tmp_path_factory.mktemp("snapshot")
    write_sources(root / "raw", Simulation(months=6, daily_orders=4))
    return run_etl(root / "raw", root / "etl")


def check_repeat_load(engine, snapshot):
    expected = {name: len(frame) for name, frame in snapshot.tables.items()}
    assert replace_snapshot(engine, snapshot) == expected
    assert replace_snapshot(engine, snapshot) == expected
    assert metadata(engine)["run_id"] == snapshot.quality["run_id"]
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM products")) == 12
        orphans = conn.scalar(text("""
            SELECT COUNT(*) FROM shipments s
            LEFT JOIN customer_orders o ON o.order_id = s.order_id
            LEFT JOIN production_lots l ON l.lot_id = s.lot_id
            WHERE o.order_id IS NULL OR (s.lot_id IS NOT NULL AND l.lot_id IS NULL)
        """))
        assert orphans == 0


def test_duckdb_repeat_load_and_rollback(snapshot):
    engine = create_engine("duckdb:///:memory:")
    try:
        check_repeat_load(engine, snapshot)
        original = snapshot.tables["shipments"]
        bad = original.copy()
        bad.loc[0, "order_id"] = "missing"
        snapshot.tables["shipments"] = bad
        try:
            with pytest.raises(SQLAlchemyError):
                replace_snapshot(engine, snapshot)
        finally:
            snapshot.tables["shipments"] = original
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT COUNT(*) FROM shipments")) == len(original)
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_postgres_repeat_load(snapshot, postgres_engine):
    check_repeat_load(postgres_engine, snapshot)
