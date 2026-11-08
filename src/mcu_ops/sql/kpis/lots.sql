SELECT lot_id, product_id, product_name, product_category, product_family, production_date,
       tested_units, passed_units, rejected_units,
       100.0 * passed_units / NULLIF(tested_units, 0) AS yield_pct,
       100.0 * rejected_units / NULLIF(tested_units, 0) AS defect_pct
FROM selected_lots
ORDER BY production_date, lot_id
