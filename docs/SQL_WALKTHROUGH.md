# SQL walkthrough

Operations needs one count per customer promise even when there are several dispatches.
Run the hand-calculated example with `python -m pytest -q tests/test_analytics.py`.

| Example metric | Expected and observed in DuckDB |
| --- | --- |
| On-time delivery | 1 of 4 due orders, 25% |
| Order fulfillment | 2 of 5 entered orders, 40% |
| Backlog and overdue | 195 units, 2 overdue orders |
| Production yield | 982 / 1010, 97.23% |
| Average fulfillment lead time | (4 + 7) / 2, 5.5 days |
| Latest observed stock | 50 + 20, 70 units |

## Order facts in context.sql

1. `selected_products` binds category and family. `selected_orders` joins those products to the
   order table and keeps orders entered by the cutoff.
2. `dispatch` joins shipments to that order set and removes dispatches after cutoff.
3. `GROUP BY s.order_id` produces at most one shipment summary per order.
4. `SUM(CASE WHEN ...)` counts units dispatched on or before the promise date.
5. `order_facts` uses a left join so an order without shipments remains in the denominator.
   `COALESCE` treats missing dispatch totals as zero. `CASE` derives completion, overdue and
   on-time flags at the requested cutoff.

## Product rollup in performance.sql

1. `order_metrics` counts flags and sums remaining units by SKU.
2. `lot_metrics` independently sums tested, passed and rejected units by SKU.
3. `ROW_NUMBER` in the shared context ranks each SKU's stock snapshots newest first.
4. `rollup` joins one row per SKU from each source and groups by the chosen business grain.
5. The final `SELECT` divides total numerators by total denominators. `NULLIF` returns unavailable
   for empty denominators. Averaging the 98% and 20% fixture lot rates would yield 59%, while
   the weighted result is 97.23% because the larger lot contains 1,000 of 1,010 tested units.

## Monthly trend in monthly.sql

1. The recursive `months` CTE creates one row per selected calendar month.
2. Separate CTEs aggregate orders by promise or entry date, dispatches by shipment date, and
   lots by production date. Each returns one row per month before joining.
3. Left joins preserve months with no events. Rates are unavailable when their denominator is zero.
4. `LAG` retrieves the preceding month's demand. Growth is calculated only when both adjacent
   months are complete and prior demand is positive.

A CTE is a named intermediate result scoped to one statement. These names expose the grain and
filter boundaries for review. The Python service binds date and dimension values separately
from SQL text, so user-entered filter values cannot alter the statement.
