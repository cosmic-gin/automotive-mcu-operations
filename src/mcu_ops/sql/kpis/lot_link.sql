,
trace AS (
    SELECT o.order_id,
           MAX(CASE WHEN l.tested_units > 0 THEN 1 ELSE 0 END) AS measured,
           MAX(CASE WHEN 100.0 * l.passed_units / NULLIF(l.tested_units, 0) < :yield_target
                    THEN 1 ELSE 0 END) AS linked_below_target
    FROM order_facts o JOIN shipments s USING (order_id)
    JOIN production_lots l USING (lot_id)
    WHERE o.due = 1 AND s.shipment_date <= :cutoff
    GROUP BY o.order_id
),
comparison_group AS (
    SELECT o.on_time,
           CASE WHEN t.linked_below_target = 1 THEN 'At least one below-target lot'
                WHEN t.measured = 1 THEN 'Measured lots at or above target'
                ELSE 'No measured lot link' END AS trace_group
    FROM order_facts o LEFT JOIN trace t USING (order_id) WHERE o.due = 1
)
SELECT trace_group, COUNT(*) AS due_orders, SUM(on_time) AS on_time_orders,
       100.0 * SUM(on_time) / COUNT(*) AS on_time_pct
FROM comparison_group GROUP BY trace_group ORDER BY trace_group
