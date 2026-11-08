# Tableau Public workbook guide

The CSVs contain fictional, publicly shareable data. Tableau Public is a public publishing
service. Use these synthetic exports for this workbook. Published workbooks use extracts,
and CSV sources must be republished to refresh their data. [Tableau Public FAQ](https://help.tableau.com/current/pro/desktop/en-us/public_faq.htm)

## Export one analytical snapshot

Load a validated database first, then run the export from the repository.

```powershell
python -m mcu_ops.tableau --output data/exports/tableau
```

Use `--start YYYY-MM-DD --end YYYY-MM-DD` for a different window. Each CSV includes
`period_start` and `period_end`. The export manifest supplies the validation run and row counts.

| File | Grain | Key fields and use |
| --- | --- | --- |
| executive_kpis.csv | One reporting window | Due and on-time orders, fulfillment numerator and denominator, tested and passed units, backlog and overdue orders. Snapshot-wide headline. |
| monthly_delivery_performance.csv | Promise or event month × category × family | `month`, `due_orders`, `on_time_orders`, `orders_entered`, `ordered_units`, `shipped_units`, `tested_units`, `passed_units`. Additive components for delivery, demand and quality charts. |
| product_performance.csv | One SKU | `product_id`, name, category, family, cohort counts, `backlog_units`, `overdue_orders`, `inventory_units`. SKU ranking. |
| production_quality.csv | One tested lot | `lot_id`, `production_date`, SKU labels, `tested_units`, `passed_units`, `rejected_units`, lot percentages. |
| order_backlog.csv | One open order at cutoff | `order_id`, product and customer labels, `order_date`, `promised_date`, `ordered_quantity`, `shipped_units`, `remaining_units`, `overdue`. |

Set identifiers and dimensions to String. Set ISO date fields to Date and quantities and
counts to Number (whole). Existing `*_pct` fields use a 0–100 scale. Format them as numbers
with a percent suffix for row-level display. Use ratios on a 0–1 scale for Tableau's built-in
Percentage format. Blank fields represent unavailable values.

## Build the workbook

1. Install or open Tableau Public Desktop Edition and start a workbook.
2. Choose **Connect → Text File** and open each CSV as a separate data source. Rename the
   sources Executive, Monthly, Products, Lots and Backlog.
   [Tableau text file connector](https://help.tableau.com/current/pro/desktop/en-gb/examples_text.htm)
3. In each data source set types using the table above. Keep the five sources separate. Their
   different grains make a physical join unsafe. If extending this design with a SKU dimension,
   relate facts to a unique SKU table on `product_id` at the logical layer.
4. On Monthly, define **On-time delivery** as
   `IF SUM([due_orders]) > 0 THEN SUM([on_time_orders]) / SUM([due_orders]) END`.
   Put `month` on Columns as a continuous month and the ratio on Rows. Format it as a percentage.
   Add `SUM([due_orders])` to Tooltip. Create a second sheet for ordered and shipped units using
   Measure Names and Measure Values. Demand growth already exported per family is a nonadditive
   rate. Recompute growth after grouping demand across families.
5. On Lots, calculate weighted yield as
   `IF SUM([tested_units]) > 0 THEN SUM([passed_units]) / SUM([tested_units]) END`.
   Build a family bar chart. Use the same approach with `rejected_units` for defect rate.
6. On Products, sort `SUM([backlog_units])` descending by SKU. On Backlog, create an order
   table with promised date, remaining units and overdue flag. On Executive, create text
   tiles from the single row and label them as full-window snapshot values.
7. Assemble a dashboard with a title and fictional-data subtitle at the top, executive
   tiles below, monthly delivery and flows side by side, then family yield and SKU backlog.
   Use teal for delivery and orange for missed commitments. Use integer labels for quantities,
   one decimal for rates, and grain-specific titles.
8. Add category and family filters on the Monthly sheets and choose **Apply to Worksheets →
   All Using This Data Source**. Apply filters independently to Products or Lots, or use
   explicit dashboard filter actions mapping the category field across sources. Keep the
   Executive tiles visibly labeled as full-window values. Spot-check the tooltip denominator
   before and after filtering. The export period is fixed for the snapshot.
9. When ready to share the fictional workbook, choose **Server → Tableau Public → Save to
   Tableau Public**, sign in, and verify the public page and its filters.
   [Tableau publication instructions](https://help.tableau.com/current/pro/desktop/en-us/publish_workbooks_tableaupublic.htm)

Streamlit runs application code against the analytical database and can trigger the validation
demo. Tableau is a visual workbook over prepared extracts. It demonstrates chart authoring,
calculated fields and public BI presentation. The generated extracts and workbook instructions
are the local deliverables.
