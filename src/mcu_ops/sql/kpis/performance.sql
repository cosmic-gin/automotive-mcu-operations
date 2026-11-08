,
order_metrics AS (
    SELECT product_id, SUM(due) AS due_orders, SUM(on_time) AS on_time_orders,
           SUM(CASE WHEN order_date >= :start THEN 1 ELSE 0 END) AS orders_entered,
           SUM(CASE WHEN order_date >= :start AND completed_on IS NOT NULL THEN 1 ELSE 0 END) AS fulfilled_orders,
           SUM(CASE WHEN remaining_units > 0 THEN 1 ELSE 0 END) AS open_orders,
           SUM(CASE WHEN remaining_units > 0 AND shipped_units > 0 THEN 1 ELSE 0 END) AS partial_open_orders,
           SUM(remaining_units) AS backlog_units, SUM(overdue) AS overdue_orders,
           SUM(CASE WHEN completed_on BETWEEN :start AND :cutoff
                    THEN completed_on - order_date ELSE 0 END) AS lead_days_total,
           SUM(CASE WHEN completed_on BETWEEN :start AND :cutoff THEN 1 ELSE 0 END) AS completions,
           SUM(CASE WHEN due = 1 AND has_late_shipment = 1 THEN 1 ELSE 0 END) AS late_dispatch_orders
    FROM order_facts GROUP BY product_id
),
lot_metrics AS (
    SELECT product_id, SUM(tested_units) AS tested_units, SUM(passed_units) AS passed_units,
           SUM(rejected_units) AS rejected_units
    FROM selected_lots GROUP BY product_id
),
rollup AS (
    SELECT CASE :grain
             WHEN 'product' THEN p.product_id
             WHEN 'category' THEN p.product_category
             WHEN 'family' THEN p.product_family
             ELSE 'All products'
           END AS group_name,
           COALESCE(SUM(o.due_orders), 0) AS due_orders,
           COALESCE(SUM(o.on_time_orders), 0) AS on_time_orders,
           COALESCE(SUM(o.orders_entered), 0) AS orders_entered,
           COALESCE(SUM(o.fulfilled_orders), 0) AS fulfilled_orders,
           COALESCE(SUM(o.open_orders), 0) AS open_orders,
           COALESCE(SUM(o.partial_open_orders), 0) AS partial_open_orders,
           COALESCE(SUM(o.backlog_units), 0) AS backlog_units,
           COALESCE(SUM(o.overdue_orders), 0) AS overdue_orders,
           COALESCE(SUM(o.lead_days_total), 0) AS lead_days_total,
           COALESCE(SUM(o.completions), 0) AS completions,
           COALESCE(SUM(o.late_dispatch_orders), 0) AS late_dispatch_orders,
           COALESCE(SUM(l.tested_units), 0) AS tested_units,
           COALESCE(SUM(l.passed_units), 0) AS passed_units,
           COALESCE(SUM(l.rejected_units), 0) AS rejected_units,
           SUM(i.available_stock) AS inventory_units,
           MIN(i.available_stock) AS min_inventory_units,
           COUNT(i.snapshot_id) AS inventory_skus
    FROM selected_products p
    LEFT JOIN order_metrics o USING (product_id)
    LEFT JOIN lot_metrics l USING (product_id)
    LEFT JOIN ranked_inventory i ON i.product_id = p.product_id AND i.rank = 1
    GROUP BY CASE :grain
               WHEN 'product' THEN p.product_id WHEN 'category' THEN p.product_category
               WHEN 'family' THEN p.product_family ELSE 'All products'
             END
)
SELECT *, due_orders - on_time_orders AS missed_orders,
       100.0 * on_time_orders / NULLIF(due_orders, 0) AS on_time_pct,
       100.0 * fulfilled_orders / NULLIF(orders_entered, 0) AS fulfillment_pct,
       100.0 * passed_units / NULLIF(tested_units, 0) AS yield_pct,
       100.0 * rejected_units / NULLIF(tested_units, 0) AS defect_pct,
       1.0 * lead_days_total / NULLIF(completions, 0) AS avg_lead_days
FROM rollup ORDER BY group_name
