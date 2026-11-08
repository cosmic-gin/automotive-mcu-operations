"""Simulate demand, tested lots, and FIFO order dispatch for a fictional MCU supplier."""
import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
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
DEFAULT_DAILY_ORDERS = 95
DAY_DEMAND = (1.10, 1.18, 1.16, 1.14, 1.00, 0.52, 0.36)
# Channel, carton range and minimum promise days. Each carton holds 20 MCUs.
ORDER_MIX = (("OEM", 7, 23, 8), ("Tier 1", 5, 18, 7), ("Distributor", 2, 12, 6))


@dataclass(frozen=True)
class Simulation:
    seed: int = 42
    start: date = date(2025, 1, 1)
    months: int = 9
    daily_orders: int = DEFAULT_DAILY_ORDERS
    cutoff: date | None = None

    def __post_init__(self):
        if self.start.day != 1 or self.months < 6 or self.daily_orders < 4:
            raise ValueError("Start on the first of a month, use at least six months and four daily orders")
        if self.cutoff is not None and not self.start <= self.cutoff <= self.planned_end:
            raise ValueError("Cutoff must be inside the planned simulation")

    @classmethod
    def rolling(
        cls, cutoff: date | None = None, *, seed: int = 42, months: int = 9,
        daily_orders: int = DEFAULT_DAILY_ORDERS,
    ) -> "Simulation":
        """Replay a moving calendar window through the last complete UTC day by default."""
        cutoff = cutoff or (datetime.now(UTC).date() - DAY)
        start = (pd.Timestamp(cutoff.replace(day=1)) - pd.DateOffset(months=months - 1)).date()
        return cls(seed, start, months, daily_orders, cutoff)

    @property
    def end(self) -> date:
        return self.cutoff or self.planned_end

    @property
    def planned_end(self) -> date:
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
    on_hand = dict.fromkeys(products, 0)
    current = spec.start
    nominal = spec.daily_orders * 235 / len(products)
    weekly_pressure = 0.0

    while current <= end:
        month = (current.year - spec.start.year) * 12 + current.month - spec.start.month
        progress = month / (spec.months - 1)
        stressed = 0.35 <= progress < 0.75
        recovering = progress >= 0.75
        weekday = current.weekday()
        if current == spec.start or weekday == 0:
            weekly_pressure = float(np.clip(0.55 * weekly_pressure + rng.normal(0, 0.12), -0.3, 0.3))
        seasonal = 1 + 0.07 * np.sin((current.month - 1) * np.pi / 3)
        quarter_pull = 1.16 if current.month % 3 == 0 and current.day >= 23 else 1.0
        arrivals = rng.poisson(
            spec.daily_orders * (1 + 0.42 * progress) * seasonal * DAY_DEMAND[weekday]
            * quarter_pull * (1 + weekly_pressure)
        )
        weights = np.tile([1.13, 1.0, 0.87], 4)
        if stressed:
            weights[:3] *= 1.28
        product_indices = rng.choice(len(products), size=arrivals, p=weights / weights.sum())
        channels = rng.choice(len(ORDER_MIX), size=arrivals, p=(0.28, 0.53, 0.19))
        for index, channel in zip(product_indices, channels, strict=True):
            product = products[index]
            segment, low, high, standard_lead = ORDER_MIX[channel]
            units = int(rng.integers(low, high + 1)) * 20
            promise = current + (standard_lead + int(rng.integers(0, 5))) * DAY
            release = current + int(rng.integers(1, 5)) * DAY
            order_id = f"ORD-{len(orders) + 1:07}"
            pending[product].append(OpenOrder(len(orders), units, release))
            orders.append([order_id, product, segment, current, promise, units, "OPEN"])

        for index, product in enumerate(products):
            # An assumed supplier interruption constrains safety and powertrain lot starts.
            supplier_delay = stressed and index in {0, 1, 2, 6, 7, 8}
            outage = rng.random() < (0.13 if supplier_delay else 0.025)
            if not outage and (weekday < 5 or (recovering and weekday == 5)):
                capacity = 1.12 if supplier_delay else (2.05 if recovering else 1.78)
                tested = max(1, int(nominal * capacity * rng.uniform(0.80, 1.20)))
                target = 0.945 if supplier_delay else (0.985 if recovering else 0.977)
                target = float(np.clip(target + rng.normal(0, 0.009), 0.87, 0.998))
                passed = int(rng.binomial(tested, target))
                lot_id = f"LOT-{len(lots) + 1:07}"
                lots.append((lot_id, product, current, tested, passed, tested - passed))
                if passed:
                    stock[product].append(StockLot(lot_id, passed))
                    on_hand[product] += passed

            queue = pending[product]
            inventory = stock[product]
            available = on_hand[product]
            dispatch_capacity = 0.85 if supplier_delay else (2.40 if recovering else 1.85)
            shift = (1.0, 1.05, 1.0, 1.03, 0.94, 0.55, 0.12)[weekday]
            budget = min(available, int(nominal * dispatch_capacity * shift * rng.uniform(0.88, 1.12)))
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
            on_hand[product] = available
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
        "cutoff": spec.end.isoformat(),
        "simulation_mode": "rolling" if spec.cutoff else "reference",
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
    horizon = parser.add_mutually_exclusive_group()
    horizon.add_argument("--start", type=date.fromisoformat)
    horizon.add_argument("--live", action="store_true", help="Roll through the last complete UTC day")
    parser.add_argument("--months", type=int, default=9)
    parser.add_argument("--daily-orders", type=int, default=DEFAULT_DAILY_ORDERS)
    parser.add_argument("--corrupt", action="store_true")
    args = parser.parse_args()
    if args.corrupt and args.output.name != "faults":
        parser.error("Use a separate directory named faults for corrupted data")
    if args.live:
        spec = Simulation.rolling(seed=args.seed, months=args.months, daily_orders=args.daily_orders)
    else:
        spec = Simulation(args.seed, args.start or Simulation().start, args.months, args.daily_orders)
    print(write_sources(args.output, spec, args.corrupt))


if __name__ == "__main__":
    main()
