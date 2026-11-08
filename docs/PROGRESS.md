# Development progress

| Phase | Status |
| --- | --- |
| 0. Initialization | Verified in an isolated Python 3.12.4 environment |
| 1. Requirements and model | Business grain, keys and KPI contract reviewed |
| 2. Synthetic data | 67,366 clean reference rows, with a verified rolling replay |
| 3. ETL and data quality | Clean, quarantine and strict modes verified |
| 4. Databases | DuckDB and Docker Compose PostgreSQL 17 verified |
| 5. SQL KPIs | Hand-calculated fixture and cross-backend parity verified |
| 6. Streamlit | Four pages, filters and centered reliability tables verified |
| 7. Reporting and monitoring | Local cycle and workflow files verified |
| 8. Tableau exports | Five reconciled CSVs and workbook guide delivered |
| 9. Deployment preparation | Clean wheel installation and fresh demo boot verified |
| 10. Integration and interview preparation | Full local suite and documentation verified |

## Acceptance evidence

| Criterion | Local evidence |
| --- | --- |
| Set up from README | Installed a fresh environment using the deployment requirements and started the app |
| Reproducible fictional sources | Seeded tables compare equal in the generator tests |
| Detect intended failures | Fault snapshot flagged stale inventory and rejected 31 rows |
| Inspect rejected records | Quarantine CSV preserves rules, identifiers and original fields |
| Store in PostgreSQL | Full Compose load and SQL counts of 29,454 orders, 32,252 shipments and 3,276 stock observations |
| Run the DuckDB demo | Final wheel booted the app without a prebuilt database |
| Test SQL KPIs | Hand fixtures and live PostgreSQL parity passed |
| Display calculated dashboard metrics | AppTest and browser verified the SQL-backed overview and reliability view |
| Filter by date and product | AppTest compared the filtered card with the SQL result |
| Implement scheduled reporting | GitHub workflow calls the rolling replay. Its local command wrote a report through 2026-11-06 |
| Export for Tableau | Five CSVs generated and matched across databases |
| Document automated checks | 18 pytest tests passed with Compose PostgreSQL enabled. Ruff, pip checks and compilation passed |
| Label fictional data | Disclaimer on the app, reports and README |
| Keep a build journal | [Phase journal](PROJECT_BUILD_JOURNAL.md) records every checkpoint |
| Provide an interview walkthrough | [Three-minute demonstration](INTERVIEW_DEMO.md) uses working controls and measured fictional results |

## External verification still open

- GitHub Actions and Streamlit Community Cloud require publishing the repository and selecting
  the app. The workflow files and local equivalent were verified. Hosted execution remains pending.
  The [GitHub push guide](GITHUB_PUSH.md) has the exact review and publication sequence.
- Tableau workbook authoring and publication remain manual. The [workbook guide](TABLEAU_GUIDE.md)
  specifies the layout, calculations, filters and publication steps.
