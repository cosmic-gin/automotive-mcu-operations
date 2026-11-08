SELECT snapshot_date, SUM(available_stock) AS inventory_units, COUNT(*) AS observed_skus
FROM ranked_inventory WHERE snapshot_date >= :start
GROUP BY snapshot_date ORDER BY snapshot_date
