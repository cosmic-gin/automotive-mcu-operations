CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    product_category VARCHAR NOT NULL CHECK (product_category IN (
        'Safety-Control MCUs', 'Body-Electronics MCUs', 'Powertrain-Control MCUs',
        'Automotive Connectivity MCUs'
    )),
    product_family VARCHAR NOT NULL,
    standard_unit_cost DECIMAL(12,2) NOT NULL CHECK (standard_unit_cost >= 0),
    active_status BOOLEAN NOT NULL
);

CREATE TABLE customer_orders (
    order_id VARCHAR PRIMARY KEY,
    product_id VARCHAR NOT NULL REFERENCES products(product_id),
    customer_segment VARCHAR NOT NULL CHECK (customer_segment IN ('OEM', 'Tier 1', 'Distributor')),
    order_date DATE NOT NULL,
    promised_date DATE NOT NULL CHECK (promised_date >= order_date),
    ordered_quantity INTEGER NOT NULL CHECK (ordered_quantity > 0),
    order_status VARCHAR NOT NULL CHECK (order_status IN ('OPEN', 'FULFILLED'))
);

CREATE TABLE production_lots (
    lot_id VARCHAR PRIMARY KEY,
    product_id VARCHAR NOT NULL REFERENCES products(product_id),
    production_date DATE NOT NULL,
    tested_units INTEGER NOT NULL CHECK (tested_units >= 0),
    passed_units INTEGER NOT NULL CHECK (passed_units >= 0),
    rejected_units INTEGER NOT NULL CHECK (rejected_units >= 0),
    CHECK (CAST(passed_units AS BIGINT) + rejected_units = tested_units)
);

CREATE TABLE inventory_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    product_id VARCHAR NOT NULL REFERENCES products(product_id),
    snapshot_date DATE NOT NULL,
    available_stock INTEGER NOT NULL CHECK (available_stock >= 0),
    UNIQUE (product_id, snapshot_date)
);

CREATE TABLE shipments (
    shipment_id VARCHAR PRIMARY KEY,
    order_id VARCHAR NOT NULL REFERENCES customer_orders(order_id),
    lot_id VARCHAR REFERENCES production_lots(lot_id),
    shipment_date DATE NOT NULL,
    shipped_quantity INTEGER NOT NULL CHECK (shipped_quantity > 0)
);

CREATE TABLE snapshot_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    run_id VARCHAR NOT NULL,
    start_date DATE NOT NULL,
    as_of DATE NOT NULL CHECK (as_of >= start_date),
    quality_json TEXT NOT NULL
);

CREATE INDEX products_category_family_idx ON products (product_category, product_family);
CREATE INDEX orders_promise_product_idx ON customer_orders (promised_date, product_id);
CREATE INDEX orders_entry_idx ON customer_orders (order_date);
CREATE INDEX lots_date_product_idx ON production_lots (production_date, product_id);
CREATE INDEX inventory_date_product_idx ON inventory_snapshots (snapshot_date, product_id);
CREATE INDEX shipments_order_date_idx ON shipments (order_id, shipment_date);
CREATE INDEX shipments_date_idx ON shipments (shipment_date);
CREATE INDEX shipments_lot_idx ON shipments (lot_id);
