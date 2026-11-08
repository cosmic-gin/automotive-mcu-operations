# Analytical storage

For a portable snapshot, leave `MCU_BACKEND=duckdb` and run the loader.

```powershell
python -m mcu_ops.database
```

For PostgreSQL, copy `.env.example` to `.env`, choose a local password, and set
`MCU_BACKEND=postgresql`. Use a dedicated project database.

```powershell
docker compose up -d --wait postgres
python -m mcu_ops.database
docker compose exec postgres psql -U mcu -d mcu -c "SELECT count(*) FROM customer_orders"
```

PostgreSQL is a server database with independent client connections. DuckDB runs inside the
Python process and stores a portable file, or an in-memory snapshot for hosted demos.

The loader atomically replaces project-owned tables in one transaction, using dependency order
and the same packaged SQL DDL on both engines. Readers see a committed snapshot. Invalid inserts
roll back the replacement. PostgreSQL additionally serializes concurrent loaders with a
transaction advisory lock. A DuckDB file is intended for one writer process. Stop the local
DuckDB dashboard before running a separate writer. The snapshot metadata and quality evidence
are committed with the operational tables. ETL audit files remain available for failed runs.

This is a full-refresh design for a small synthetic dataset. Existing views, grants tied to
replaced tables, and incremental history are outside this dedicated database model.
