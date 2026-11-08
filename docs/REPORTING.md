# Reporting and monitoring

```powershell
python -m mcu_ops.reporting --refresh
python -m mcu_ops.reporting --source data/raw/clean --end 2025-09-14
```

The refresh uses the standard seed and business timeline. The default report compares the final
seven simulated days with the preceding seven days. `--end` selects an earlier simulated cutoff.
KPI changes in rates are percentage points. Backlog compares the outstanding balance at each
cutoff, including orders created before both windows. Each successful run writes
`reports/<execution_id>/weekly-<cutoff>.md`. Execution status and stage are recorded in
`data/etl/executions/`. Row and freshness checks live separately under `data/etl/quality/`.

GitHub Actions tests pushes and pull requests using DuckDB and a temporary PostgreSQL service.
The scheduled reporting job runs Mondays at 07:17 UTC and supports manual dispatch. It regenerates
the fictional snapshot using DuckDB on the runner and stores reports and quality evidence as
30-day run artifacts. Each rerun has its own artifact name. Schedule timing is controlled by
GitHub and applies to the default branch. [GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

A production scheduler would ingest a real delivered snapshot, set an explicit reporting cutoff,
and route run failures to an operations owner. The portfolio schedule intentionally repeats the
seeded business period to demonstrate reproducibility.
