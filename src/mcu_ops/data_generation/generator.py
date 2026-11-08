"""Simulate demand, tested lots, and FIFO order dispatch for a fictional MCU supplier."""
import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

CATEGORIES = (
    "Safety-Control MCUs",
    "Body-Electronics MCUs",
    "Powertrain-Control MCUs",
    "Automotive Connectivity MCUs",
)
FAMILIES = ("Aegis", "Relay", "Torque", "Signal")
SEGMENTS = ("OEM", "Tier 1", "Distributor")
COLUMNS = {
    "products": "product_id product_name product_category product_family standard_unit_cost active_status",
    "customer_orders": "order_id product_id customer_segment order_date promised_date ordered_quantity order_status",
    "production_lots": "lot_id product_id production_date tested_units passed_units rejected_units",
    "inventory_snapshots": "snapshot_id product_id snapshot_date available_stock",
    "shipments": "shipment_id order_id lot_id shipment_date shipped_quantity",
}
DAY = timedelta(days=1)


@dataclass(frozen=True)
class Simulation:
    seed: int = 42
    start: date = date(2025, 1, 1)
    months: int = 9
    daily_orders: int = 45

    def __post_init__(self):
        if self.start.day != 1 or self.months < 6 or self.daily_orders < 4:
            raise ValueError("Start on the first of a month, use at least six months and four daily orders")

    @property
    def end(self) -> date:
        return (pd.Timestamp(self.start) + pd.DateOffset(months=self.months)).date() - DAY


@dataclass
class OpenOrder:
    index: int
    remaining: int
    ready_date: date


@dataclass
class StockLot:
    lot_id: str
    remaining: int


def _sku_rows(seed: int) -> list[tuple]:
    fake = Faker("en_US")
    fake.seed_instance(seed)
    return [
        (
            f"MCU-{index + 1:03}",
            f"{FAMILIES[index // 3]} {fake.bothify(text='??-###').upper()}",
            CATEGORIES[index // 3],
            f"{FAMILIES[index // 3]} {'Core' if index % 3 < 2 else 'Plus'}",
            round(2.40 + index * 0.29, 2),
            True,
        )
        for index in range(12)
    ]


def generate(spec: Simulation | None = None) -> dict[str, pd.DataFrame]:
    """Return clean tables. Only passed units from dated lots can be dispatched."""
    spec = spec or Simulation()
    end = spec.end
    rng = np.random.default_rng(spec.seed)
    tables = {table: [] for table in COLUMNS}
    tables["products"] = _sku_rows(spec.seed)
    orders = tables["customer_orders"]
    lots = tables["production_lots"]
    shipments = tables["shipments"]
    snapshots = tables["inventory_snapshots"]
    products = [row[0] for row in tables["products"]]
    pending = {product: deque() for product in products}
    stock = {product: deque() for product in products}
    current = spec.start

    while current <= end:
        month = (current.year - spec.start.year) * 12 + current.month - spec.start.month
        progress = month / (spec.months - 1)
        stressed = 0.35 <= progress < 0.75
        recovering = progress >= 0.75
        seasonal = 1 + 0.09 * np.sin(month * np.pi / 3)
        weekend = 0.70 if current.weekday() >= 5 else 1.10
        arrivals = rng.poisson(spec.daily_orders * (1 + 0.58 * progress) * seasonal * weekend)
        weights = [1.45 if stressed and i < 3 else 1.0 for i in range(len(products))]
        for index in rng.choice(len(products), size=arrivals, p=np.array(weights) / sum(weights)):
            product = products[index]
            units = int(rng.integers(35, 391))
            promise = current + int(rng.integers(6, 13)) * DAY
            release = current + int(rng.integers(2, 6)) * DAY
            order_id = f"ORD-{len(orders) + 1:07}"
            pending[product].append(OpenOrder(len(orders), units, release))
            orders.append([order_id, product, str(rng.choice(SEGMENTS)), current, promise, units, "OPEN"])

        for index, product in enumerate(products):
            # An assumed supplier interruption constrains safety and powertrain lot starts.
            supplier_delay = stressed and index in {0, 1, 2, 6, 7, 8}
            if current.weekday() < 5 or (recovering and current.weekday() == 5):
                nominal = spec.daily_orders * 210 / len(products) * 1.55
                capacity = 0.66 if supplier_delay else (1.68 if recovering else 1.08)
                tested = max(1, int(nominal * capacity * rng.uniform(0.74, 1.25)))
                target = 0.933 if supplier_delay else (0.985 if recovering else 0.977)
                passed = int(rng.binomial(tested, target))
                lot_id = f"LOT-{len(lots) + 1:07}"
                lots.append((lot_id, product, current, tested, passed, tested - passed))
                if passed:
                    stock[product].append(StockLot(lot_id, passed))

            queue = pending[product]
            inventory = stock[product]
            available = sum(lot.remaining for lot in inventory)
            budget = available
            # Simulated dispatch capacity drops during the same period as supplier delays.
            if supplier_delay:
                budget = min(available, int(spec.daily_orders * 210 / len(products) * 0.88))
            while queue and budget and queue[0].ready_date <= current:
                order = queue[0]
                lot = inventory[0]
                shipped = min(order.remaining, lot.remaining, budget)
                shipments.append((
                    f"SHP-{len(shipments) + 1:07}", orders[order.index][0], lot.lot_id, current, shipped
                ))
                order.remaining -= shipped
                lot.remaining -= shipped
                budget -= shipped
                available -= shipped
                if lot.remaining == 0:
                    inventory.popleft()
                if order.remaining == 0:
                    orders[order.index][-1] = "FULFILLED"
                    queue.popleft()
            if current.weekday() == 6 or current == end:
                snapshots.append((f"INV-{len(snapshots) + 1:07}", product, current, available))
        current += DAY

    return {
        name: pd.DataFrame(rows, columns=COLUMNS[name].split())
        for name, rows in tables.items()
    }


def inject_faults(frames: dict[str, pd.DataFrame], seed: int) -> dict[str, pd.DataFrame]:
    """Copy tables before injecting reproducible single-row faults."""
    rng = np.random.default_rng(seed)
    changed = {name: frame.copy() for name, frame in frames.items()}
    orders = changed["customer_orders"]
    missing, orphan, negative, blank = rng.choice(len(orders), 4, replace=False)
    orders.loc[missing, "product_id"] = None
    orders.loc[orphan, "product_id"] = "INVALID-SKU"
    orders.loc[negative, "ordered_quantity"] = -10
    orders.loc[blank, "customer_segment"] = None
    changed["customer_orders"] = add_duplicate(orders)
    shipments = changed["shipments"]
    bad_date, excess = rng.choice(len(shipments), 2, replace=False)
    shipments.loc[bad_date, "shipment_date"] = date(2000, 1, 1)
    shipments.loc[excess, "shipped_quantity"] = 1_000_000
    lots = changed["production_lots"]
    bad_lot = int(rng.integers(len(lots)))
    lots.loc[bad_lot, "passed_units"] = lots.loc[bad_lot, "tested_units"] + 1
    changed["inventory_snapshots"].loc[0, "available_stock"] = -1
    return changed


def add_duplicate(orders: pd.DataFrame) -> pd.DataFrame:
    """Return a separate order table with one extra copy of its first row."""
    return pd.concat([orders, orders.iloc[:1]], ignore_index=True)


def write_sources(root: Path, spec: Simulation, corrupt: bool = False) -> dict[str, int]:
    """Write one source snapshot and its fictional delivery manifest."""
    frames = generate(spec)
    if corrupt:
        frames = inject_faults(frames, spec.seed + 1)
    root.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(root / f"{name}.csv", index=False)
    freshness = dict.fromkeys(COLUMNS, spec.end.isoformat())
    if corrupt:
        freshness["inventory_snapshots"] = (spec.end - 14 * DAY).isoformat()
    manifest = {
        **asdict(spec),
        "start": spec.start.isoformat(),
        "as_of": spec.end.isoformat(),
        "source_dates": freshness,
        "scenario": "faults" if corrupt else "clean",
        "fictional": True,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {name: len(frame) for name, frame in frames.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw/clean"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2025, 1, 1))
    parser.add_argument("--months", type=int, default=9)
    parser.add_argument("--daily-orders", type=int, default=45)
    parser.add_argument("--corrupt", action="store_true")
    args = parser.parse_args()
    if args.corrupt and args.output.name != "faults":
        parser.error("Use a separate directory named faults for corrupted data")
    print(write_sources(args.output, Simulation(args.seed, args.start, args.months, args.daily_orders), args.corrupt))


if __name__ == "__main__":
    main()
