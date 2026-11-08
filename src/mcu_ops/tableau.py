"""Export consistent SQL-derived datasets for a Tableau executive workbook."""
import argparse
import json
import logging
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from mcu_ops.analytics import Analytics, Filters
from mcu_ops.config import settings
from mcu_ops.database import make_engine, snapshot_reader

LOG = logging.getLogger(__name__)


def export_tableau(analytics: Analytics, destination: Path, period: Filters) -> dict[str, int]:
    """Keep each CSV at a documented grain and include additive KPI components."""
    if period.start < analytics.start or period.end > analytics.as_of:
        raise ValueError("Export dates must fall inside the loaded snapshot")
    if period.category or period.family or period.segment:
        raise ValueError("Tableau exports require an unfiltered product and customer population")
    dimensions = analytics.products()
    groups = dimensions[["product_category", "product_family"]].drop_duplicates()
    monthly = pd.concat([
        analytics.query("monthly", Filters(period.start, period.end, category, family)).assign(
            product_category=category, product_family=family
        )
        for category, family in groups.itertuples(index=False, name=None)
    ], ignore_index=True)
    sku = analytics.query("performance", period, grain="product").rename(
        columns={"group_name": "product_id"}
    ).merge(dimensions, on="product_id", validate="one_to_one")
    order = analytics.query("orders", period)
    backlog = order.loc[order.remaining_units > 0].sort_values(
        ["remaining_units", "order_id"], ascending=[False, True]
    )
    datasets = {
        "executive_kpis": pd.DataFrame([analytics.headline(period)]),
        "monthly_delivery_performance": monthly,
        "product_performance": sku,
        "production_quality": analytics.query("lots", period),
        "order_backlog": backlog,
    }
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in datasets.items():
        frame.assign(period_start=period.start, period_end=period.end).to_csv(
            destination / f"{name}.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8"
        )
    rows = {name: len(frame) for name, frame in datasets.items()}
    manifest = {
        "fictional": True, "validation_run_id": analytics.quality["run_id"],
        "period_start": period.start.isoformat(), "period_end": period.end.isoformat(),
        "row_counts": rows, "date_format": "YYYY-MM-DD",
        "ratio_format": "Percent columns use 0–100. Recompute grouped rates from additive fields.",
    }
    (destination / "export_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/exports/tableau"))
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        engine = make_engine(settings())
        try:
            with snapshot_reader(engine) as connection:
                analytics = Analytics(connection)
                window = Filters(args.start or analytics.start, args.end or analytics.as_of)
                print(export_tableau(analytics, args.output, window))
        finally:
            engine.dispose()
    except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        LOG.error("Tableau export failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
