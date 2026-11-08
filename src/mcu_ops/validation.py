"""Row, relationship, and cumulative-dispatch rules for raw CSV records."""
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from mcu_ops.data_generation.generator import CATEGORIES, SEGMENTS

KEYS = {
    "products": "product_id",
    "customer_orders": "order_id",
    "production_lots": "lot_id",
    "inventory_snapshots": "snapshot_id",
    "shipments": "shipment_id",
}
DATES = {"order_date", "promised_date", "production_date", "snapshot_date", "shipment_date"}
COUNTS = {
    "ordered_quantity", "tested_units", "passed_units", "rejected_units",
    "available_stock", "shipped_quantity",
}


class RuleViolation(ValueError):
    """A validation failure with a stable rule identifier."""

    def __init__(self, rule: str, message: str):
        super().__init__(message)
        self.rule = rule


def require(condition: bool, rule: str, message: str) -> None:
    if not condition:
        raise RuleViolation(rule, message)


def parse_record(raw: dict[str, str], *, nullable_lot: bool = False) -> dict:
    """Convert CSV strings to application types and report the first type or null failure."""
    row = {}
    for name, raw_value in raw.items():
        value = raw_value.strip()
        if nullable_lot and name == "lot_id" and not value:
            row[name] = None
            continue
        require(bool(value), "required", f"{name} is required")
        try:
            if name in DATES:
                day = date.fromisoformat(value)
                if day.isoformat() != value:
                    raise ValueError
                row[name] = day
            elif name in COUNTS:
                number = int(value)
                if not -(2**31) <= number < 2**31:
                    raise ValueError
                row[name] = number
            elif name == "standard_unit_cost":
                cost = Decimal(value)
                if not cost.is_finite() or cost >= Decimal("10000000000") or cost.as_tuple().exponent < -2:
                    raise ValueError
                row[name] = cost
            elif name == "active_status":
                row[name] = {"true": True, "false": False}[value.lower()]
            else:
                row[name] = value
        except (ValueError, InvalidOperation, KeyError) as exc:
            raise RuleViolation("data_type", f"{name} has an invalid value or format") from exc
    return row


class Validator:
    """Track accepted parent keys and shipment balances within one snapshot."""

    def __init__(self, as_of: date):
        self.as_of = as_of
        self.rows = {table: {} for table in KEYS}
        self.inventory_days = set()
        self.order_units = defaultdict(int)
        self.lot_units = defaultdict(int)

    def local(self, table: str, row: dict) -> None:
        for name in DATES.intersection(row) - {"promised_date"}:
            require(row[name] <= self.as_of, "future_event", f"{name} follows the extract date")
        if table == "products":
            require(row["product_category"] in CATEGORIES, "category", "Unknown product category")
            require(row["standard_unit_cost"] >= 0, "unit_cost", "Unit cost must be nonnegative")
        elif table == "customer_orders":
            require(row["ordered_quantity"] > 0, "order_quantity", "Order quantity must be positive")
            require(row["promised_date"] >= row["order_date"], "promise_date", "Promise precedes order")
            require(row["customer_segment"] in SEGMENTS, "customer_segment", "Unknown customer segment")
            require(row["order_status"] in {"OPEN", "FULFILLED"}, "order_status", "Unknown source status")
        elif table == "production_lots":
            tested, passed, rejected = (row[k] for k in ("tested_units", "passed_units", "rejected_units"))
            require(
                0 <= passed <= tested and 0 <= rejected <= tested and passed + rejected == tested,
                "lot_balance",
                "Passed and rejected units must be nonnegative and sum to tested units",
            )
        elif table == "inventory_snapshots":
            require(row["available_stock"] >= 0, "inventory_quantity", "Stock must be nonnegative")
        elif table == "shipments":
            require(row["shipped_quantity"] > 0, "shipment_quantity", "Shipped quantity must be positive")

    def accept(self, table: str, row: dict) -> None:
        """Check accepted-parent relationships before registering the row."""
        key = row[KEYS[table]]
        require(key not in self.rows[table], "duplicate_key", "Primary key is already accepted")
        self.local(table, row)
        if table in {"customer_orders", "production_lots", "inventory_snapshots"}:
            require(row["product_id"] in self.rows["products"], "product_fk", "Product is unavailable")
        if table == "inventory_snapshots":
            product_day = (row["product_id"], row["snapshot_date"])
            require(product_day not in self.inventory_days, "inventory_grain", "Duplicate SKU and date")
            self.inventory_days.add(product_day)
        if table == "shipments":
            self._accept_dispatch(row)
        self.rows[table][key] = row

    def _accept_dispatch(self, row: dict) -> None:
        order_id, lot_id, shipment_date, units = (
            row[name] for name in ("order_id", "lot_id", "shipment_date", "shipped_quantity")
        )
        order = self.rows["customer_orders"].get(order_id)
        require(order is not None, "order_fk", "Order is unavailable")
        require(shipment_date >= order["order_date"], "before_order", "Shipment precedes order")
        require(self.order_units[order_id] + units <= order["ordered_quantity"],
                "order_overshipment", "Cumulative shipment exceeds ordered units")
        if lot_id is not None:
            lot = self.rows["production_lots"].get(lot_id)
            require(lot is not None, "lot_fk", "Production lot is unavailable")
            require(lot["product_id"] == order["product_id"], "lot_product", "Lot and order products differ")
            require(shipment_date >= lot["production_date"], "before_lot", "Shipment precedes production")
            require(self.lot_units[lot_id] + units <= lot["passed_units"],
                    "lot_overshipment", "Cumulative dispatch exceeds passed lot units")
            self.lot_units[lot_id] += units
        self.order_units[order_id] += units
