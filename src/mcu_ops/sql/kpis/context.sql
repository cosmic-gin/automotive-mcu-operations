WITH RECURSIVE
selected_products AS (
    SELECT * FROM products
    WHERE (:category = '' OR product_category = :category)
      AND (:family = '' OR product_family = :family)
),
selected_orders AS (
    SELECT o.*, p.product_name, p.product_category, p.product_family
    FROM customer_orders o JOIN selected_products p USING (product_id)
    WHERE o.order_date <= :cutoff AND (:segment = '' OR o.customer_segment = :segment)
),
dispatch AS (
    SELECT s.order_id, COUNT(*) AS shipment_count, SUM(s.shipped_quantity) AS shipped_units,
           SUM(CASE WHEN s.shipment_date <= o.promised_date THEN s.shipped_quantity ELSE 0 END)
               AS shipped_by_promise,
           MAX(s.shipment_date) AS last_dispatch,
           MAX(CASE WHEN s.shipment_date > o.promised_date THEN 1 ELSE 0 END) AS has_late_shipment
    FROM shipments s JOIN selected_orders o USING (order_id)
    WHERE s.shipment_date <= :cutoff
    GROUP BY s.order_id
),
order_facts AS (
    SELECT o.*, COALESCE(d.shipment_count, 0) AS shipment_count,
           COALESCE(d.shipped_units, 0) AS shipped_units,
           o.ordered_quantity - COALESCE(d.shipped_units, 0) AS remaining_units,
           CASE WHEN d.shipped_units = o.ordered_quantity THEN d.last_dispatch END AS completed_on,
           CASE WHEN o.promised_date BETWEEN :start AND :cutoff THEN 1 ELSE 0 END AS due,
           CASE WHEN o.promised_date BETWEEN :start AND :cutoff
                     AND d.shipped_by_promise >= o.ordered_quantity THEN 1 ELSE 0 END AS on_time,
           CASE WHEN o.promised_date < :cutoff AND COALESCE(d.shipped_units, 0) < o.ordered_quantity
                THEN 1 ELSE 0 END AS overdue,
           COALESCE(d.has_late_shipment, 0) AS has_late_shipment
    FROM selected_orders o LEFT JOIN dispatch d USING (order_id)
),
selected_lots AS (
    SELECT l.*, p.product_name, p.product_category, p.product_family
    FROM production_lots l JOIN selected_products p USING (product_id)
    WHERE l.production_date BETWEEN :start AND :cutoff
),
ranked_inventory AS (
    SELECT i.*, ROW_NUMBER() OVER (PARTITION BY i.product_id ORDER BY i.snapshot_date DESC) AS rank
    FROM inventory_snapshots i JOIN selected_products p USING (product_id)
    WHERE i.snapshot_date <= :cutoff
)
