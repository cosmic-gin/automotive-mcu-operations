# Fictional source generation

Run from the repository with the virtual environment active.

```powershell
python -m mcu_ops.data_generation.generator
python -m mcu_ops.data_generation.generator --corrupt --output data/raw/faults
```

The seed is 42 by default. The reference window is January to September 2025. Use `--start`,
`--months`, `--daily-orders` and `--seed` to change the simulation. Dates come from the manifest,
which decouples the business timeline from the computer clock.

Faker produces fictional SKU labels. A seeded NumPy generator varies the number of orders, SKU
mix, lot quantities and test results. The simulator adds passed units to a dated stock queue.
Orders wait for a dispatch release date and consume available stock in FIFO order. A lot boundary
or limited dispatch budget can split an order into multiple events. Stock observations are taken
at the end of each Sunday and the final simulated day.

During the middle months, assumed supplier interruptions reduce lot starts and yield for Safety
and Powertrain products. A dispatch cap overlaps the disruption. Safety demand is also weighted
up during this interval. Later, higher production and Saturday lots allow an operational recovery.
The simulator cannot isolate the effects of overlapping changes.

Fault injection copies the clean tables and applies seeded edits. The stale inventory delivery is
represented by the manifest's source date. Fault files live separately from clean sources.
