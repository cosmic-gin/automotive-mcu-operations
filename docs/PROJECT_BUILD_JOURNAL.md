# Project build journal

Each entry records a verified checkpoint and an interview explanation. See [progress](PROGRESS.md)
for outstanding work.

## Phase 0 — Initialization

The repository separates the importable Python package in `src/mcu_ops`, automated checks in
`tests`, and business and learning material in `docs`. `pyproject.toml` defines editable
installation, dependencies, Ruff and pytest. Configuration is read from environment variables or
an optional `.env`. The checked-in example contains empty credential fields.

Executed `python --version` (3.12.4), `python -m venv .venv`, and `git init -b main`.
The first virtual environment install failed with Windows socket permission error 10013.
Using `$env:PYTHONPATH = 'src'` and the installed Anaconda environment, `python -m pytest -q`
passed one test, `ruff check .` passed and `python -m compileall -q src tests` succeeded.
Docker Compose is installed but the engine was unavailable during the first check.

Interview answer — I isolated project dependencies and built a smoke test for the configuration
entry point so a new contributor can catch setup errors before touching data. The next phase
defines the business rules that the generator, validator and KPI queries will share.


## Phase 1 — Business requirements and model

[Business requirements](BUSINESS_REQUIREMENTS.md) connects operations decisions to evidence.
[Architecture](ARCHITECTURE.md) shows the data flow and entity relationships.
[Data dictionary](DATA_DICTIONARY.md) specifies grains, keys, constraints and proposed indexes.
[KPI definitions](KPI_DEFINITIONS.md) records the event dates and null behavior.

Reviewed the split-shipment case by hand. For a 100-unit order due Friday, 80 units on Friday
and 20 on Monday produce one missed on-time order. Friday backlog is 20 and fulfillment
completes Monday. Reviewed the inventory uniqueness rule and the difference between a due
cohort and an order-entry cohort. Ran `python -m pytest -q` with `PYTHONPATH=src` (1 passed)
and `ruff check .` (passed). The SQL implementation and fixture-based checks follow later.

Interview answer — I defined the grain and date logic before writing SQL so a split shipment
cannot inflate an order count. Next, seeded business records will exercise those rules.


## Phase 2 — Synthetic data generation

[Generator](../src/mcu_ops/data_generation/generator.py) uses Faker for fictional SKU labels
and seeded NumPy for daily orders, product mix, lot volume and passed units. The stock queue
allocates only passed units from dated lots and naturally splits orders across lot boundaries.
[Generation guide](DATA_GENERATION.md) describes the supplier and recovery assumptions.

Ran `python -m mcu_ops.data_generation.generator` and
`python -m mcu_ops.data_generation.generator --corrupt --output data/raw/faults` in the
virtual environment. The clean run wrote 37,112 records across five CSVs and the fault run
added one row. The reference cutoff is 2025-09-30. The first lint run flagged an instantiated
default argument. Moved configuration creation into the function and reran the checks.
`python -m pytest -q` passed 5 tests, `python -m ruff check .` passed, and imports, bytecode
compilation and `python -m pip check` succeeded in the isolated environment.

Interview answer — I simulated changes to orders, production and dispatch capacity. KPI
deterioration and recovery emerge when SQL rolls up those transactions. The next phase
validates the raw records and separates invalid rows into quarantine.


Phase 0 follow-up — The approved package download completed. The isolated smoke test,
imports and pip dependency checks passed during Phase 2. The sandbox blocked git add
from creating .git/index.lock. Repository history is tracked separately from phase verification.

## Phase 3 — ETL and data quality

[ETL](../src/mcu_ops/etl.py) extracts raw strings, runs dependency-ordered checks, saves typed
accepted rows, and writes an audit folder for each run. [Validation](../src/mcu_ops/validation.py)
tracks accepted keys and cumulative order and lot quantities. [Data quality guide](DATA_QUALITY.md)
explains the quarantine fields and how to reproduce the controlled demonstration.

Ran `python -m mcu_ops.etl` (37,112 accepted, 0 rejected, exit 0),
`python -m mcu_ops.etl --source data/raw/faults --mode quarantine` (37,093 accepted,
20 rejected, stale inventory delivery, exit 0), and the same source in strict mode
(exit 1 with evidence retained). Nine pytest tests and Ruff passed. The tests confirmed the
isolated duplicate adds exactly one rejection, and invalid parents exclude dependent shipments.

Interview answer — I preserve rejected records and reasons so an analyst can distinguish a
process issue from a data issue. Processing valid parent records first keeps the accepted tables
referentially consistent. Next, the accepted snapshot will be loaded into both databases.

