# Three-minute interview demonstration

Run `python -m streamlit run app/streamlit_app.py` in the activated project environment.
Use the default seed-42 snapshot. Open the app before the interview so the first refresh
has time to finish. To prepare the weekly Markdown report in advance, run
`python -m mcu_ops.reporting --refresh` with the local DuckDB app stopped.

## Minute 1 · Problem and architecture

> A fictional automotive MCU manufacturer needs to know which customer promises it missed
> and where outstanding units are accumulating. I built a reproducible pipeline that generates
> orders, tested lots, shipments and stock observations. Python validates the source files,
> preserves rejects for inspection, and publishes a transactional snapshot. A shared SQL layer
> powers PostgreSQL locally and DuckDB in a portable Streamlit demo.

Point at the source-to-dashboard flow in the [architecture](ARCHITECTURE.md).

## Minute 2 · SQL-backed investigation

1. Show March, June and September on the executive delivery chart. The simulated rates were
   100%, 46.0% and 78.0%. Point out the June gap between ordered and shipped units.
2. Select **Safety-Control MCUs**, set the end date to **2025-06-30**, and open **Orders and
   delivery**. Choose **Overdue at cutoff**. Show the promised date, shipped units and remaining
   units for a delayed order. The June cutoff had 768 overdue Safety-Control orders.
3. Explain the calculation in one example. If 80 of 100 units ship by the promise date,
   the order is one missed promise and contributes 20 outstanding units at that cutoff.
   The SQL aggregates shipments by order first, then left joins the one-row result to all
   eligible orders. The date filter uses the promised date for the on-time denominator.

## Minute 3 · Reliability and automation

1. Open **Data reliability** and click **Detect a duplicate order**. Point at the quarantined ID
   and the `duplicate_key` rule. Show that the loaded snapshot still reports its own 37,112 rows.
2. Open the generated weekly report. Explain how strict ETL prevents an invalid snapshot
   from reaching the database. A scheduled GitHub Actions job reruns the command and stores
   the Markdown report, quality evidence and execution status as artifacts.
3. Close with one finding. Safety-Control still had 47,932 open units at the end of September.
   Recommend reviewing lot availability and promise dates for its three SKUs.
