# Development progress

| Phase | Status |
| --- | --- |
| 0. Initialization | Verified in an isolated Python 3.12.4 environment |
| 1. Requirements and model | Business grain, keys and KPI contract reviewed |
| 2. Synthetic data | 37,112 clean rows generated reproducibly |
| 3. ETL and data quality | Clean, quarantine and strict modes verified |
| 4. Databases | DuckDB and native PostgreSQL 17.8 verified |
| 5. SQL KPIs | Hand-calculated fixture and cross-backend parity verified |
| 6. Streamlit | Four pages and date and category filters verified |
| 7. Reporting and monitoring | Local cycle and workflow files verified |
| 8. Tableau exports | Five reconciled CSVs and workbook guide delivered |
| 9. Deployment preparation | Clean wheel installation and fresh demo boot verified |
| 10. Integration and interview preparation | Full local suite and documentation verified |

## Acceptance evidence

| Criterion | Local evidence |
| --- | --- |
| Set up from README | Installed a fresh environment using the deployment requirements and started the app |
| Reproducible fictional sources | Seeded tables compare equal in the generator tests |
| Detect intended failures | Fault snapshot flagged stale inventory and rejected 20 rows |
| Inspect rejected records | Quarantine CSV preserves rules, identifiers and original fields |
| Store in PostgreSQL | Full load and SQL count of 15,954 orders on PostgreSQL 17.8 |
| Run the DuckDB demo | Final wheel booted the app without a prebuilt database |
| Test SQL KPIs | Hand fixtures and live PostgreSQL parity passed |
| Display calculated dashboard metrics | AppTest and browser verified the SQL-backed overview and reliability view |
| Filter by date and product | AppTest compared the filtered card with the SQL result |
| Implement scheduled reporting | GitHub workflow is present. Equivalent local job produced report and status artifacts |
| Export for Tableau | Five CSVs generated and matched across databases |
| Document automated checks | 17 pytest tests passed with PostgreSQL enabled. Ruff, pip checks and compilation passed |
| Label fictional data | Disclaimer on the app, reports and README |
| Keep a build journal | [Phase journal](PROJECT_BUILD_JOURNAL.md) records every checkpoint |
| Provide an interview walkthrough | [Three-minute demonstration](INTERVIEW_DEMO.md) uses working controls and measured fictional results |

## External verification still open

- Docker Compose configuration parsed successfully. Docker Desktop timed out on this machine,
  so PostgreSQL runtime verification used a temporary native 17.8 server. With a working Docker
  engine, run `docker compose up -d --wait postgres` and `python -m mcu_ops.database` as described
  in the [deployment guide](DEPLOYMENT.md).
- GitHub Actions and Streamlit Community Cloud require publishing the repository and selecting
  the app. The workflow files and local equivalent were verified. Hosted execution remains pending.
- Tableau workbook authoring and publication remain manual. The [workbook guide](TABLEAU_GUIDE.md)
  specifies the layout, calculations, filters and publication steps.
