# Simulated operations findings

These figures come from the 67,366-row reference replay from January through September 2025.
The rolling replay uses a different calendar window and can produce different results.

| Month | On-time delivery | Ordered units | Shipped units | Month-end backlog | Weighted yield |
| --- | ---: | ---: | ---: | ---: | ---: |
| March | 99.97% | 750,900 | 720,466 | 121,905 | 97.80% |
| April | 68.16% | 801,200 | 616,405 | 306,700 | 96.60% |
| May | 46.83% | 865,880 | 626,318 | 546,262 | 96.54% |
| June | 48.23% | 835,020 | 607,267 | 774,015 | 96.58% |
| July | 50.24% | 796,380 | 1,100,036 | 470,359 | 98.54% |
| August | 63.45% | 729,700 | 925,310 | 274,749 | 98.53% |
| September | 76.16% | 909,980 | 914,816 | 269,913 | 98.49% |

June backlog peaked after orders exceeded shipments by 227,753 units that month. July dispatches
exceeded new orders by 303,656 units. September demand jumped 24.71% from August and the backlog
reduction slowed. In the final seven days of September, on-time delivery improved from
79.46% to 80.83% while backlog rose by 52,146 units versus the prior weekly cutoff.

## Where to investigate

Safety-Control and Powertrain-Control both reached 0% on-time delivery in June while the other
two categories held at 100%. In September, Safety-Control reached 45.08% and Powertrain-Control
59.03%. They accounted for all 367 overdue orders at cutoff, with 315 in Safety-Control and
52 in Powertrain-Control.

MCU-001 had 107,169 outstanding units and MCU-007 had 45,685. Both finished September with zero
observed stock. Other SKUs in those same categories still had stock. Compare SKU-level passed
receipts, allocated dispatch capacity and overdue commitments before using category-level
inventory to judge whether a promise can be met.

## Quality and delivery

June yield was 94.30% for Safety-Control and 94.63% for Powertrain-Control. At the fictional
97% threshold, 3,651 of 6,737 due orders linked to at least one below-target lot shipped
on time (54.19%). For orders with measured links all at or above target, 15,798 of 20,967
shipped on time (75.35%). Another 392 orders had no measured lot link. Observed links include
dispatches made after the promise date. Demand, product mix, timing and capacity can all affect
the comparison.

## Reproduce the figures

```powershell
python -m mcu_ops.data_generation.generator
python -m mcu_ops.database
python -m mcu_ops.tableau
python -m streamlit run app/streamlit_app.py
```

Use the executive monthly detail for delivery, demand and yield. Set the end date to each
month-end for backlog, then open Orders and delivery for the SKU ranking. Production quality
exports the lot-linked delivery comparison.
