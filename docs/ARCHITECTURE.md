# Architecture

```mermaid
flowchart LR
    A[Seeded fictional sources] --> B[Raw CSV and manifest]
    B --> C[Python ETL and validation]
    C --> D[Quarantine and quality history]
    C --> E[Validated snapshot]
    E --> F[PostgreSQL local]
    E --> G[DuckDB demo]
    F --> H[Shared parameterized SQL]
    G --> H
    H --> I[Streamlit and Plotly]
    H --> J[Weekly report and Tableau CSVs]
    D --> I
    D --> J
```

```mermaid
erDiagram
    PRODUCTS ||--o{ CUSTOMER_ORDERS : requested
    PRODUCTS ||--o{ PRODUCTION_LOTS : produced
    PRODUCTS ||--o{ INVENTORY_SNAPSHOTS : stocked
    CUSTOMER_ORDERS ||--o{ SHIPMENTS : fulfilled
    PRODUCTION_LOTS o|--o{ SHIPMENTS : traced
```

A primary key uniquely identifies a row. A foreign key points to the primary key of a related
row. Both links from shipments are many-to-one. Joining raw shipments directly to orders before
counting orders can multiply split orders, so the analytics layer first aggregates by order ID.

The dependency order is products, orders and lots, inventory, then shipments. Parent entities
are validated first. Database constraints provide a second layer for keys and row-local rules.
Cross-table chronology, product compatibility, cumulative quantities and freshness are enforced in ETL.
