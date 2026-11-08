# Interview questions and model answers

1. **Why did you build this project?** I wanted to demonstrate the full operational BI
   workflow, from raw order and lot records to traceable decisions about service and backlog.
2. **Why use Python and SQL together?** Python coordinates generation, validation, database
   loading and presentation. SQL defines cohort selection and aggregation close to the data.
3. **Why PostgreSQL?** It supports transactional data loads, database constraints and independent
   users. The project configures a local service through Compose.
4. **Why DuckDB for the public demo?** An embedded database runs without a separate service and
   executes the same analytical SQL. The app can build its snapshot in temporary storage.
5. **How does the ETL work?** It reads CSV strings, validates schema and types, applies
   business rules in dependency order, then publishes accepted rows and quarantine evidence.
6. **How are duplicates handled?** The first valid occurrence is accepted. A later occurrence
   with the same key is quarantined with its original values and the `duplicate_key` rule.
7. **Why weight production yield?** A 1,000-unit lot carries more information about production
   volume than a 10-unit lot. Total passed divided by total tested gives the unit-level rate.
8. **How are partial shipments handled?** Dispatches are aggregated per order through the
   cutoff. The outstanding balance is ordered units minus cumulative shipped units.
9. **How do you calculate on-time delivery?** The denominator contains orders due in the
   selected period by cutoff. The numerator contains those completely shipped by the promise date.
10. **How do you prevent double-counting?** I aggregate shipments to one row per order, then
    aggregate orders and lots independently to SKU before combining their results.
11. **Where did you use SQL joins?** I use an inner join to select valid product dimensions,
    and a left join from orders to dispatch totals to preserve orders with no shipment.
12. **What is a CTE?** A common table expression names an intermediate query result within
    a statement. The dispatch CTE documents where the grain changes from shipment to order.
13. **How do you handle missing data?** Required source fields are quarantined. Optional lot
    links are allowed. A zero metric denominator returns a SQL null and the app shows unavailable.
14. **How do you test the pipeline?** I test seeded reproducibility, fault handling, rollback,
    repeated loads and parity between engines. A hand fixture specifies the expected KPI results.
15. **How do GitHub Actions work?** Pushes and PRs run lint and tests with a disposable
    PostgreSQL service. The scheduled job builds a DuckDB snapshot and archives its report.
16. **How would you handle larger datasets?** I would stage batch inserts or use PostgreSQL
    COPY, measure query plans, and move toward incremental loads with dated source partitions.
17. **What would you change for production?** I would add least-privilege roles, stronger
    source contracts, explicit handling of corrections and late arrivals, alert routing and
    carrier delivery events for a true delivery measure.
18. **What are the limitations of synthetic data?** It tests workflow and metric semantics
    under constructed scenarios. It cannot establish real effect sizes or business impact.
19. **What did you find?** Simulated OTD fell from 99.97% in March to 46.83% in May.
    Backlog peaked at 774,015 units in June and fell to 269,913 by September.
20. **How could operations use the dashboard?** Start with the OTD alert, filter the affected
    category, rank overdue SKU balances and inspect the orders to decide what to investigate.
21. **How do you compare quality with delivery?** I link accepted shipments to tested lots and
    compare groups of due orders. Co-occurring capacity limits and timing limit causal interpretation.
22. **What happens on a failed load?** The transaction rolls back table replacement. Validation
    evidence and reporting execution status are retained independently in run-specific directories.
23. **How is Tableau different from Streamlit here?** Tableau consumes prepared extracts for
    interactive workbook analysis. Streamlit queries the database and can run a Python validation demo.
24. **How do you interpret a rising backlog with fewer overdue orders?** Backlog includes all
    unshipped units. Recent orders can increase open units even while older commitments are cleared.
