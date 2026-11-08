# KPI definitions

Dates are inclusive. For period metrics, start and end select the business events described
below. The reporting cutoff is the earlier of the selected end and the snapshot date.
Product filters apply throughout. Customer segment applies only to order-derived metrics.
Percentages use zero to 100. An undefined denominator produces a null, displayed as unavailable.

| KPI | Cohort and calculation |
| --- | --- |
| On-time delivery rate | Promised date within period and on or before cutoff. Orders with cumulative quantity by the promise date at least equal to ordered quantity divided by all due orders. An incomplete due order is missed. Date-only shipments on the promised date are on time. |
| Order fulfillment rate | Order date within period. Fully shipped orders by cutoff divided by orders entered in period. |
| Open order backlog | All orders entered by cutoff regardless of start date. Sum of ordered units minus dispatched units through cutoff for incomplete orders. Empty cohort yields zero units. |
| Overdue order count | Open at cutoff and promised date strictly earlier than cutoff. A promise due on the cutoff date can miss the end-of-day OTD measure while overdue age is zero days. |
| Production test yield | Lots produced in period. 100 times total passed units divided by total tested units. Zero-tested lots contribute zero to both. |
| Defect rate | Lots produced in period. 100 times total rejected units divided by total tested units. Passed plus rejected equals tested. |
| Average fulfillment lead time | Orders completed in period. Average elapsed calendar days from order date to final quantity completing shipment. |
| Inventory availability | On-hand units from each SKU's latest observation as of cutoff, summed over observed SKUs. Trend points sum available units for snapshots on the same date. Missing observations are unavailable. |
| Monthly demand growth | Percentage change in ordered units from the preceding calendar month using order dates. First observed month, empty prior month and incomplete comparison months yield null. |
| Data quality failure rate | Rejected source rows divided by all rows processed in the selected pipeline run, times 100. Freshness and schema failures also have separate flags. |

Demand and realized throughput use their respective event dates. Their difference during a
month describes flow, while backlog measures the outstanding balance across all prior orders.
Category or lot quality comparisons are descriptive associations. Shipment lot links establish
traceability to the tested lot, with no experimental evidence of causality.
