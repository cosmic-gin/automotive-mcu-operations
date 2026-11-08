from datetime import date

import pandas as pd
import pytest

from mcu_ops.data_generation.generator import Simulation, generate, inject_faults


@pytest.fixture(scope="module")
def tables():
    return generate()


def test_reproducible(tables):
    for name, regenerated in generate().items():
        pd.testing.assert_frame_equal(tables[name], regenerated)


def test_quantity_and_relationships(tables):
    assert 20_000 <= sum(map(len, tables.values())) <= 100_000
    for table in tables.values():
        assert table.iloc[:, 0].is_unique
    orders = tables["customer_orders"]
    lots = tables["production_lots"]
    for name in ("customer_orders", "production_lots", "inventory_snapshots"):
        assert set(tables[name].product_id) <= set(tables["products"].product_id)
    traced = tables["shipments"].merge(orders, on="order_id", validate="many_to_one")
    traced = traced.merge(lots, on="lot_id", validate="many_to_one")
    assert len(traced) == len(tables["shipments"])
    assert (traced.product_id_x == traced.product_id_y).all()
    assert (traced.shipment_date >= traced.order_date).all()
    assert (traced.shipment_date >= traced.production_date).all()
    shipped_per_lot = traced.groupby("lot_id").shipped_quantity.sum()
    assert shipped_per_lot.le(lots.set_index("lot_id").passed_units).loc[shipped_per_lot.index].all()
    shipped_per_order = traced.groupby("order_id").shipped_quantity.sum()
    assert shipped_per_order.le(orders.set_index("order_id").ordered_quantity).loc[shipped_per_order.index].all()
    assert (lots.passed_units + lots.rejected_units == lots.tested_units).all()


def test_simulation_has_deterioration_and_recovery(tables):
    orders = tables["customer_orders"].copy()
    orders["month"] = pd.to_datetime(orders.promised_date).dt.month
    shipments = tables["shipments"].merge(orders, on="order_id")
    by_promise = shipments.loc[shipments.shipment_date <= shipments.promised_date]
    quantities = by_promise.groupby("order_id").shipped_quantity.sum()
    orders["met_promise"] = orders.order_id.map(quantities).fillna(0) >= orders.ordered_quantity
    rates = orders.loc[orders.promised_date <= date(2025, 9, 30)].groupby("month").met_promise.mean()
    assert rates.loc[2] > rates.loc[6]
    assert rates.loc[9] > rates.loc[6]
    assert (orders.order_date >= date(2025, 1, 1)).all()
    assert Simulation().end == date(2025, 9, 30)


def test_faults_do_not_mutate_clean_data(tables):
    faults = inject_faults(tables, 43)
    assert not faults["customer_orders"].order_id.is_unique
    assert faults["customer_orders"].product_id.isna().any()
    assert (faults["shipments"].shipped_quantity == 1_000_000).any()
    assert tables["customer_orders"].order_id.is_unique
    assert tables["customer_orders"].product_id.notna().all()
