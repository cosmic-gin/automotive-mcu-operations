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


## Phase 4 — Analytical storage

[Database layer](../src/mcu_ops/database.py) reads the [shared DDL](../src/mcu_ops/sql/schema/snapshot.sql)
and writes typed rows, SQL constraints, indexes and snapshot metadata inside one transaction.
[Database guide](DATABASE.md) explains the full-refresh design and the Compose commands.
PostgreSQL provides independent server sessions. DuckDB runs inside the demo process.

Ran `python -m mcu_ops.database` against DuckDB. SQL counted 12 products, 15,954 orders,
2,496 lots, 480 inventory observations and 18,170 shipments. Ten tests passed, including
repeated load, orphan checks and rollback after a foreign-key violation. The PostgreSQL test
skipped because there was no active test connection. Compose syntax validated with a temporary
configuration-only password. Docker startup was requested for runtime verification.

Interview answer — I commit the operational tables and their quality metadata together so
an unsuccessful reload leaves the last valid snapshot intact. The next phase builds shared
SQL metrics over these tables.


## Phase 5 — SQL analytics and KPI engine

[Analytics](../src/mcu_ops/analytics.py) binds filters and reads packaged SQL. The shared order
CTE reduces all dispatch events to one row per order before KPI calculations. Monthly demand
and throughput use separate date dimensions. Rule-based alerts compare measured values with
fictional targets. [SQL walkthrough](SQL_WALKTHROUGH.md) explains three queries clause by clause.

Ran `python -m pytest -q` (11 passed, two PostgreSQL checks skipped) and Ruff (passed).
The hand fixture produced 25% OTD, 195 units of backlog, 2 overdue orders and 97.23% weighted
yield. Queried the full DuckDB snapshot and observed monthly OTD fall from 100% in March
to 45.99% in June and recover to 78.04% in September. The aggregate rate was 71.42%.

Interview answer — I use left joins to preserve due orders with no dispatch and aggregate
independent facts before joining them. I test metric semantics with hand-computed cases.
The next phase uses these exact SQL results in Streamlit.


## Phase 6 — Streamlit dashboards

[Streamlit entry point](../app/streamlit_app.py) registers four file-based pages and keeps one
set of filters in the sidebar. Plotly charts and downloads use the same SQL service as the
headline metrics. The quality page groups each due order once by observed lot links.
The reliability page reads committed metadata and runs the duplicate demo on an isolated sample.

Ran `python -m streamlit run app/streamlit_app.py --server.headless true --server.port 8517`.
The local health endpoint returned `ok`. Browser verification confirmed the executive values
and the duplicate detection message. Captures are in [screenshots](screenshots).
`python -m pytest -q` passed 12 tests and skipped two PostgreSQL checks. Ruff passed.
AppTest initially interpreted an `app/pages` directory as legacy navigation on rerun.
Moving the explicitly registered views out of that directory preserved the sidebar.
The test confirmed all four pages, date and category filters against SQL, and duplicate detection.

Interview answer — I can follow an executive delivery alert to missed promises, inspect shipped
and remaining units, and download the exact rows behind the investigation. Next, reporting
will use the same business logic on a schedule.


## Phase 7 — Automated reporting and monitoring

[Reporting module](../src/mcu_ops/reporting.py) regenerates or ingests sources, validates them,
reloads the database and compares adjacent seven-day windows. The report and execution
records have unique run IDs. [Reporting guide](REPORTING.md) explains GitHub scheduling and artifact retention.

Ran `python -m pytest -q tests/test_reporting.py` (1 passed) and `python -m ruff check .`
(passed after fixing the execution-history import). The first full refresh logged the expected
DuckDB file lock while Streamlit held the same database. Using `MCU_DATA_DIR=data/scheduled`,
`python -m mcu_ops.reporting --refresh` exited 0 and wrote a weekly Markdown report,
a succeeded execution record and quality evidence. The report showed 80.74% vs 76.97% OTD
and 101,999 vs 94,134 backlog units. Both workflow files parsed as YAML. GitHub-hosted
execution requires a published repository.

Interview answer — CI tests a change before it is merged. A scheduled workflow runs the same
Python command with its own DuckDB file and retains reports and failure evidence as artifacts.
Next, the project will export dashboard-ready data at explicit grains for Tableau.


## Phase 8 — Tableau exports

[Tableau exporter](../src/mcu_ops/tableau.py) writes five grain-specific extracts with additive
numerators and denominators. [Workbook guide](TABLEAU_GUIDE.md) covers typing, calculations,
layout, filters and manual publication. Streamlit runs Python and SQL live. Tableau builds
visual worksheets over these prepared extracts.

Ran `python -m pytest -q tests/test_tableau.py` (1 passed), Ruff (passed) and
`python -m mcu_ops.tableau` against the complete DuckDB snapshot. Exports contained
1 executive row, 72 month-family rows, 12 SKUs, 2,496 tested lots and 482 open orders.
The test reconciled monthly due and on-time counts, lot passed units and order backlog
against the executive row. No Tableau workbook was authored or published here.

Interview answer — I export the counts needed to recalculate rates after Tableau filters.
I keep grains separate so a lot-to-order join cannot repeat measures. The next phase
verifies a clean package install and documents local and hosted deployment.


## Phase 9 — Deployment preparation

[README](../README.md) explains the walkthrough, repository map and local commands.
[Deployment guide](DEPLOYMENT.md) covers the PostgreSQL stack and the manual GitHub and
Streamlit Community Cloud steps. `requirements.txt` installs the project wheel and SQL
assets. The demo can generate and validate a snapshot in OS temporary storage. The two
stochastic dependencies were pinned to the versions that produced the reference results.

Created `.venv-clean` and installed with `python -m pip install -r requirements.txt`.
`pip check` passed. AppTest imported from `site-packages`, read packaged SQL, and started
the app with an unused data path. It displayed 71.4% OTD and 101,999 backlog units and left
the configured data path untouched. Git ignored `.env`, virtual environments, generated
data, database files and reports. Docker Desktop did not finish starting. A temporary
native PostgreSQL 17.8 server did start and the small KPI parity test passed. The full
external test attempt collided with a sandbox-owned pytest temp directory. Final verification
will use its own `--basetemp`.

Interview answer — I verify the installed wheel and its SQL files in a clean environment,
then test first launch with no prebuilt database. The last phase adds verified business
findings, a portfolio walkthrough and integration evidence.


## Phase 10 — Integration, findings and interview preparation

[Simulated findings](BUSINESS_INSIGHTS.md) reconcile delivery, demand, inventory, yield and
backlog from SQL. [Interview demo](INTERVIEW_DEMO.md), [model answers](INTERVIEW_QA.md) and
[portfolio copy](PORTFOLIO_DESCRIPTION.md) describe implemented behavior. The final review
fixed blank production lot IDs, added a targeted test, used the lowest observed SKU stock
for inventory alerts, and kept each dashboard, report or export read on one snapshot.

Ran the complete `pytest -q` suite with `MCU_TEST_POSTGRES_URL` and an isolated
`--basetemp` against PostgreSQL 17.8. All 17 tests passed. The full native PostgreSQL load,
Tableau export and weekly report ran successfully. The verification bundle did not include
the optional `psql` client. A follow-up run exited 0 after two PostgreSQL tests, a full load,
and a SQLAlchemy query returning 15,954 orders. The server was stopped after verification.

The DuckDB refresh and Tableau commands exited 0 against a separate verification database.
All five full-snapshot CSVs matched across engines within floating-point tolerance. Report
contents matched apart from the run metadata. The final quarantine run preserved 20 rejected
rows and the stale inventory flag. Strict mode returned exit 1 as intended. The final wheel
passed the fresh Streamlit startup check with no data directory and `pip check` succeeded.
Ruff, compilation, workflow YAML parsing, local documentation links and the Git staging
checks were verified. The first local Git checkpoint is `ddc7f0c`.

Interview answer — I can demonstrate a due-order metric from raw events through validation,
SQL, interactive drilldown and weekly reporting, and show how I checked backend parity.
Local project work is complete. The remaining external steps are to run Compose with an
available Docker engine and publish the reviewed repository, app or Tableau workbook when desired.
