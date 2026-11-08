import pytest

from mcu_ops.data_generation.generator import Simulation, add_duplicate, write_sources
from mcu_ops.etl import ValidationFailed, extract, failed, run_etl, validate


@pytest.fixture(scope="module")
def sources(tmp_path_factory):
    root = tmp_path_factory.mktemp("etl")
    spec = Simulation(months=6, daily_orders=9)
    write_sources(root / "clean", spec)
    write_sources(root / "faults", spec, corrupt=True)
    return root


def test_clean_and_faulted_snapshot(sources, tmp_path):
    clean = run_etl(sources / "clean", tmp_path, strict=True)
    assert not failed(clean.quality)
    assert clean.quarantine.empty
    bad = run_etl(sources / "faults", tmp_path, strict=False)
    assert failed(bad.quality)
    assert {
        "duplicate_key", "required", "product_fk", "order_quantity", "before_order",
        "lot_balance", "inventory_quantity", "order_overshipment",
    } <= set(bad.quality["rules"])
    assert bad.quality["accepted"] + bad.quality["rejected"] == bad.quality["processed"]
    assert bad.quality["rejected"] == len(bad.quarantine)
    assert bad.quality["freshness"][3]["status"] == "failed"
    assert bad.tables["customer_orders"].order_id.is_unique
    assert set(bad.tables["shipments"].order_id) <= set(bad.tables["customer_orders"].order_id)
    assert (tmp_path / "quality" / bad.quality["run_id"] / "quarantine.csv").is_file()
    assert (tmp_path / "processed" / bad.quality["run_id"] / "shipments.csv").is_file()


def test_strict_keeps_evidence_without_publishing_processed_tables(sources, tmp_path):
    with pytest.raises(ValidationFailed, match="Strict validation failed"):
        run_etl(sources / "faults", tmp_path)
    assert list(tmp_path.glob("quality/*/quality.json"))
    assert not (tmp_path / "processed").exists()


def test_duplicate_demo_keeps_first_accepted_order(sources):
    frames, manifest = extract(sources / "clean")
    frames["customer_orders"] = add_duplicate(frames["customer_orders"])
    result = validate(frames, manifest)
    assert result.quality["rules"] == {"duplicate_key": 1}
    assert len(result.tables["customer_orders"]) == len(frames["customer_orders"]) - 1


def test_missing_column_quarantines_affected_rows(sources):
    frames, manifest = extract(sources / "clean")
    frames["production_lots"] = frames["production_lots"].drop(columns="passed_units")
    result = validate(frames, manifest)
    assert result.quality["schema_failures"] == [
        {"table": "production_lots", "missing_columns": ["passed_units"]}
    ]
    assert result.tables["production_lots"].empty
    assert "lot_fk" in result.quality["rules"]
