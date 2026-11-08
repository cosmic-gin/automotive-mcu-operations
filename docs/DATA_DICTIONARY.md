# Data dictionary

Identifiers and labels are text. Dates are ISO YYYY-MM-DD with calendar-day granularity, including
weekends in the simulation. Quantities count whole units. All fields are required except shipment lot ID.

| Table and grain | Fields and constraints | Proposed lookup indexes |
| --- | --- | --- |
| products, one SKU | product_id PK, product_name, product_category, product_family, standard_unit_cost decimal(12,2) >= 0 in fictional EUR, active_status boolean | product_category, product_family |
| customer_orders, one order line | order_id PK, product_id FK, customer_segment, order_date, promised_date >= order_date, ordered_quantity > 0, order_status OPEN or FULFILLED at extract | promised_date and product_id |
| production_lots, one tested lot | lot_id PK, product_id FK, production_date, tested_units >= 0, passed_units >= 0, rejected_units >= 0, passed_units + rejected_units = tested_units | production_date and product_id |
| inventory_snapshots, one SKU per date | snapshot_id PK, product_id FK, snapshot_date, available_stock >= 0, unique product_id and snapshot_date | snapshot_date and product_id |
| shipments, one dispatch event | shipment_id PK, order_id FK, nullable lot_id FK, shipment_date >= order date and >= lot production date when linked, shipped_quantity > 0 | order_id and shipment_date, shipment_date |

The four categories are Safety-Control MCUs, Body-Electronics MCUs, Powertrain-Control MCUs, and
Automotive Connectivity MCUs. Customer segments are OEM, Tier 1, and Distributor. Source order
status is descriptive. Historical status is always reconstructed from dated shipments. Inventory
is a simulated stock observation and the model has no complete inventory movement ledger.
