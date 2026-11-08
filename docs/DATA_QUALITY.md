# Data quality and quarantine

```powershell
python -m mcu_ops.etl
python -m mcu_ops.etl --source data/raw/faults --mode quarantine
python -m mcu_ops.etl --source data/raw/faults --mode strict
```

Strict mode exits nonzero for row, schema, or source freshness failures. Both modes retain
`quality/<run_id>/quality.json` and `quarantine.csv`. Quarantine mode additionally writes accepted
rows to `processed/<run_id>/`. A missing input file stops extraction and logs the filename.

The validator checks required columns and values, parses types, and then checks duplicate keys,
row-local rules and accepted-parent relationships. Duplicate detection keeps the first accepted
record. When a parent fails, dependent rows are quarantined with their own relationship rule.
Shipments are processed in ISO date and ID order and consume order and lot balances only after
all checks pass. This makes the treatment of cumulative over-shipment reproducible.

Each rejected row gets one primary rule, a UTC validation time and the original CSV field values.
The report counts rejected rows rather than summing overlapping validation failures.
Freshness compares the declared delivery date for each source against the simulated as-of date
with a seven-day default. Static SKU data can be unchanged while arriving in a fresh extract.
