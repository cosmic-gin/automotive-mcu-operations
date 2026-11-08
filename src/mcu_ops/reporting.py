"""Refresh a validated analytical snapshot and write an auditable weekly KPI report."""
import argparse
import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from mcu_ops.analytics import Analytics, Filters, alerts, executive_summary
from mcu_ops.config import Settings, settings
from mcu_ops.data_generation.generator import Simulation, write_sources
from mcu_ops.database import make_engine, replace_snapshot, snapshot_reader
from mcu_ops.etl import failed, run_etl

LOG = logging.getLogger(__name__)
METRICS = (
    ("On-time delivery", "on_time_pct", "%"),
    ("Order fulfillment", "fulfillment_pct", "%"),
    ("Production test yield", "yield_pct", "%"),
    ("Open backlog", "backlog_units", "units"),
    ("Overdue orders", "overdue_orders", "orders"),
)


def _value(value, unit: str) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:.2f}%" if unit == "%" else f"{value:,.0f} {unit}"


def _change(current, previous, unit: str) -> str:
    if current is None or previous is None:
        return "Unavailable"
    return f"{current - previous:+.2f} pp" if unit == "%" else f"{current - previous:+,.0f} {unit}"


def weekly_report(analytics: Analytics, config: Settings, end: date | None = None) -> str:
    """Compare adjacent seven-day periods ending at a valid simulated cutoff."""
    end = end or analytics.as_of
    current_period = Filters(end - timedelta(days=6), end)
    previous_period = current_period.previous()
    if previous_period.start < analytics.start or end > analytics.as_of:
        raise ValueError("Report needs 14 days inside the simulated snapshot")
    current = analytics.headline(current_period)
    previous = analytics.headline(previous_period)
    categories = analytics.query("performance", current_period, grain="category")
    trend = analytics.query("monthly", Filters(analytics.start, end)).tail(3)
    quality = analytics.quality
    triggered = alerts(current, previous, quality, config)
    lines = [
        "# Weekly MCU operations report", "", "**Fictional data and operating targets.**", "",
        f"Current period **{current_period.start} through {end}**. "
        f"Comparison period **{previous_period.start} through {previous_period.end}**.",
        f"Validated snapshot `{quality['run_id']}` at {quality['validated_at']} UTC.",
        "", "## Executive summary", "", executive_summary(current, categories), "",
        "| KPI | Current | Previous | Change |", "| --- | ---: | ---: | ---: |",
    ]
    for name, key, unit in METRICS:
        value, prior = current.get(key), previous.get(key)
        lines.append(f"| {name} | {_value(value, unit)} | {_value(prior, unit)} | {_change(value, prior, unit)} |")
    lines += [
        "", "## Recent on-time delivery", "", "| Promise month | Due orders | On-time rate |",
        "| --- | ---: | ---: |",
    ]
    for row in trend.itertuples():
        rate = _value(row.on_time_pct if row.due_orders else None, "%")
        suffix = "" if row.full_month else " (partial)"
        lines.append(f"| {row.month:%b %Y}{suffix} | {row.due_orders:,} | {rate} |")
    lines += ["", "## Triggered alerts", ""]
    lines += [f"- **{item.metric}** · {item.message}" for item in triggered] or ["No threshold was breached."]
    status = "Review" if failed(quality) else "Passed"
    lines += [
        "", "## Data quality", "", f"**{status}** · {quality['processed']:,} rows processed, "
        f"{quality['accepted']:,} accepted and {quality['rejected']:,} rejected "
        f"({_value(quality['rejection_pct'], '%')}).", "",
    ]
    for entry in quality["freshness"]:
        lines.append(f"- {entry['table']} · {entry['status']} · source date {entry['source_date'] or 'unavailable'}")
    lines += ["", "## Investigations", ""]
    if triggered:
        lines += [f"- {item.investigation}" for item in triggered]
    else:
        lines.append("Review the due-order cohort and compare the largest SKU balances at the two cutoffs.")
    return "\n".join(lines) + "\n"


def run_cycle(config: Settings, source: Path, report_dir: Path, *,
              refresh: Simulation | None = None, end: date | None = None) -> Path:
    """Record success or failure and keep past runs addressable by ID."""
    identifier = uuid4().hex
    audit = config.data_dir / "etl"
    execution_dir = audit / "executions"
    execution_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    run = {"execution_id": identifier, "started_at": started.isoformat(), "backend": config.backend,
           "status": "failed", "stage": "generate" if refresh else "validate"}
    try:
        with TemporaryDirectory(prefix="mcu-refresh-") as scratch:
            if refresh is not None:
                source = Path(scratch) / "raw"
                write_sources(source, refresh)
            run["stage"] = "validate"
            snapshot = run_etl(source, audit)
        run["validation_run_id"] = snapshot.quality["run_id"]
        run["stage"] = "load"
        engine = make_engine(config)
        try:
            run["row_counts"] = replace_snapshot(engine, snapshot)
            run["stage"] = "report"
            with snapshot_reader(engine) as connection:
                analytics = Analytics(connection)
                if analytics.quality["run_id"] != snapshot.quality["run_id"]:
                    raise RuntimeError("A concurrent load replaced this execution's snapshot. Retry the report.")
                body = weekly_report(analytics, config, end)
                report_end = end or analytics.as_of
        finally:
            engine.dispose()
        output = report_dir / identifier / f"weekly-{report_end}.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
        run.update(status="succeeded", stage="complete", report=str(output))
        LOG.info("Report written to %s", output)
        return output
    except Exception as exc:
        run["error_type"] = type(exc).__name__
        raise
    finally:
        finished = datetime.now(UTC)
        run.update(finished_at=finished.isoformat(), duration_seconds=(finished - started).total_seconds())
        (execution_dir / f"{identifier}.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    raw = parser.add_mutually_exclusive_group()
    raw.add_argument("--refresh", action="store_true", help="Regenerate the standard fictional snapshot")
    raw.add_argument("--live", action="store_true", help="Regenerate through the last complete UTC day")
    raw.add_argument("--source", type=Path, help="Use an existing source folder with its manifest")
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument("--end", type=date.fromisoformat, help="End date on the fictional timeline")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = settings()
        source = args.source or config.data_dir / "raw" / "clean"
        refresh = Simulation.rolling() if args.live else Simulation() if args.refresh else None
        report = run_cycle(config, source, args.report_dir, refresh=refresh, end=args.end)
        print(report)
    except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        LOG.error("Reporting failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
