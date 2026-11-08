,
months(month) AS (
    SELECT CAST(DATE_TRUNC('month', CAST(:start AS DATE)) AS DATE)
    WHERE :start <= :cutoff
    UNION ALL
    SELECT CAST(month + INTERVAL '1 month' AS DATE)
    FROM months
    WHERE month + INTERVAL '1 month' <= :cutoff
),
delivery AS (
    SELECT CAST(DATE_TRUNC('month', promised_date) AS DATE) AS month,
           SUM(due) AS due_orders, SUM(on_time) AS on_time_orders
    FROM order_facts WHERE due = 1 GROUP BY 1
),
demand AS (
    SELECT CAST(DATE_TRUNC('month', order_date) AS DATE) AS month,
           COUNT(*) AS orders_entered, SUM(ordered_quantity) AS ordered_units
    FROM selected_orders WHERE order_date >= :start GROUP BY 1
),
throughput AS (
    SELECT CAST(DATE_TRUNC('month', s.shipment_date) AS DATE) AS month,
           SUM(s.shipped_quantity) AS shipped_units
    FROM shipments s JOIN selected_orders o USING (order_id)
    WHERE s.shipment_date BETWEEN :start AND :cutoff GROUP BY 1
),
quality AS (
    SELECT CAST(DATE_TRUNC('month', production_date) AS DATE) AS month,
           SUM(tested_units) AS tested_units, SUM(passed_units) AS passed_units
    FROM selected_lots GROUP BY 1
),
series AS (
    SELECT m.month, COALESCE(d.due_orders, 0) AS due_orders,
           COALESCE(d.on_time_orders, 0) AS on_time_orders,
           COALESCE(a.orders_entered, 0) AS orders_entered,
           COALESCE(a.ordered_units, 0) AS ordered_units,
           COALESCE(t.shipped_units, 0) AS shipped_units,
           COALESCE(q.tested_units, 0) AS tested_units,
           COALESCE(q.passed_units, 0) AS passed_units,
           CASE WHEN m.month >= :start AND m.month + INTERVAL '1 month' - INTERVAL '1 day' <= :cutoff
                THEN 1 ELSE 0 END AS full_month
    FROM months m LEFT JOIN delivery d USING (month) LEFT JOIN demand a USING (month)
    LEFT JOIN throughput t USING (month) LEFT JOIN quality q USING (month)
),
comparison AS (
    SELECT *, LAG(ordered_units) OVER (ORDER BY month) AS prior_ordered_units,
           LAG(full_month) OVER (ORDER BY month) AS prior_full_month
    FROM series
)
SELECT *, due_orders - on_time_orders AS missed_orders,
       100.0 * on_time_orders / NULLIF(due_orders, 0) AS on_time_pct,
       100.0 * passed_units / NULLIF(tested_units, 0) AS yield_pct,
       CASE WHEN full_month = 1 AND prior_full_month = 1 THEN
           100.0 * (ordered_units - prior_ordered_units) / NULLIF(prior_ordered_units, 0)
       END AS demand_growth_pct
FROM comparison ORDER BY month
