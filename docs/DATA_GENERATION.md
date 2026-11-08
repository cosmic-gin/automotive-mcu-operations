# Fictional source generation

Run from the repository with the virtual environment active.

```powershell
python -m mcu_ops.data_generation.generator
python -m mcu_ops.data_generation.generator --corrupt --output data/raw/faults
python -m mcu_ops.data_generation.generator --live --output data/raw/rolling
```

The reference replay uses seed 42 and January to September 2025. It yields 67,366 rows,
including 29,454 orders, 32,252 shipments, 2,372 tested lots and 3,276 daily stock snapshots.
Use `--seed`, `--months`, `--daily-orders` and either `--start` or `--live` to vary the run.

The rolling replay ends on the last complete UTC day and starts at the first day of the
oldest month in the window. The same seed and cutoff replay the same event history.
Within a calendar month, a later cutoff adds transactions and can change order status.
When the window shifts to a new month, it starts a new replay. This is a clock-driven
synthetic refresh and uses no external operational feed.

## What varies

- Weekday profiles, calendar seasonality, quarter-end demand and persistent week-to-week
  changes drive order volume. Seeded Poisson noise produces different daily order counts.
- Customer segments use different order-size ranges and promise windows. Demand quantities
  are packed in 20-unit cartons, while individual dispatches can split across lot boundaries.
- Production varies with shifts, intermittent outages, supplier disruptions and lot-level
  yield variation. Recovery adds Saturday production and more dispatch capacity.
- Daily dispatch capacity and available passed stock limit FIFO fulfillment. Each day
  reconciles opening stock plus passed receipts minus dispatches for each SKU.

The model uses a fixed set of fictional products, starts with zero stock, and models
capacity and stock without replenishment optimization. Mid-window shocks affect Safety-Control
and Powertrain-Control. The measured performance reflects demand, production and dispatch
constraints acting together.

Fault injection copies the clean tables before making seeded edits. The manifest represents
stale source delivery separately from transaction dates. The dashboard duplicate sample
runs in an isolated temporary directory.
