SELECT order_id, product_id, product_name, product_category, product_family, customer_segment,
       order_date, promised_date, ordered_quantity, shipment_count, shipped_units, remaining_units,
       completed_on, due, on_time, overdue, has_late_shipment,
       CASE WHEN due = 1 AND on_time = 1 THEN 'On time'
            WHEN due = 1 AND completed_on IS NOT NULL THEN 'Completed late'
            WHEN due = 1 AND shipped_units > 0 THEN 'Incomplete, partially shipped'
            WHEN due = 1 THEN 'Incomplete, unshipped'
            WHEN completed_on IS NOT NULL THEN 'Completed outside due cohort'
            WHEN shipped_units > 0 THEN 'Open, partially shipped'
            ELSE 'Open, unshipped' END AS delivery_status
FROM order_facts
WHERE due = 1 OR order_date >= :start OR completed_on >= :start OR remaining_units > 0
ORDER BY promised_date, order_id
