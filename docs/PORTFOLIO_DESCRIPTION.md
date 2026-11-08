# Portfolio and résumé material

## Project description

Built an end-to-end operations intelligence platform for a fictional automotive
microcontroller supplier. The project follows orders from promise through split shipments,
relates shipments to tested lots, and highlights delivery, backlog, yield and data-quality risks.
It combines reproducible synthetic data, transactional loading, SQL metrics and BI presentation.

## GitHub repository description

Fictional automotive MCU operations analytics with Python ETL, PostgreSQL, DuckDB,
Streamlit, weekly KPI reports and Tableau extracts.

## Résumé bullets

- Designed a seeded simulation of 37,112 fictional operational records across orders,
  shipments, product SKUs, tested lots and stock snapshots.
- Built a Python ETL pipeline with typed validation, cumulative shipment checks, dependency
  handling, and inspectable quarantine records.
- Implemented parameterized SQL for promise-date delivery, point-in-time backlog and
  weighted production yield using shared PostgreSQL and DuckDB queries.
- Developed four Streamlit dashboards with Plotly visualizations, date and product filters,
  order drilldown, CSV downloads and a controlled duplicate demonstration.
- Automated weekly KPI and data-quality reporting with Python and configured GitHub Actions
  for lint, tests, PostgreSQL parity and scheduled report artifacts.

## LinkedIn project description

I built an automotive MCU operations intelligence platform to practice the complete BI
workflow. It simulates a fictional supplier, checks raw data before loading it, reconstructs
order fulfillment from split shipments, and presents operational KPIs in Streamlit. It
also produces weekly Markdown reports and exports Tableau-ready datasets. The data,
targets and findings are simulated.

## Architecture in one paragraph

NumPy and Faker produce a version-pinned seeded operational snapshot. pandas extracts the
CSV sources and typed Python rules validate them. SQLAlchemy commits accepted rows and
quality metadata to PostgreSQL or DuckDB. Shared SQL derives order and lot measures and feeds
Streamlit, reporting and exports. CI checks the code and a scheduled job produces auditable
reports over a temporary DuckDB database.

## 60-second pitch

> I built a BI platform for a fictional automotive microcontroller supplier. The operations
> problem is deciding which promises were missed when an order can ship in several parts.
> I generated realistic orders, lots and shipments, built a Python pipeline that quarantines
> invalid rows, and stored accepted records in PostgreSQL and DuckDB. SQL calculates
> on-time delivery, weighted yield and backlog at a selected cutoff. In the simulation, on-time
> delivery fell to 46% in June and partially recovered by September. In Streamlit I can
> trace that signal to Safety-Control orders, inspect remaining units and demonstrate a
> detected duplicate. The same KPI layer generates a weekly report and Tableau extracts.
