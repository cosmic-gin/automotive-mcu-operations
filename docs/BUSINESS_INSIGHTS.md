# Simulated operations findings

Scope is the seed-42 snapshot from 2025-01-01 through 2025-09-30. All values below come
from the fictional transactions and the project's SQL engine. The simulation has no real
manufacturer data.

## Delivery, demand and backlog

| Promise or event month | On-time delivery | Ordered units | Shipped units | End-of-month open units | Weighted yield |
| --- | ---: | ---: | ---: | ---: | ---: |
| March | 100.00% | 357,957 | 370,190 | 46,887 | 97.69% |
| April | 71.96% | 353,079 | 278,843 | 121,123 | 96.04% |
| May | 46.55% | 352,340 | 270,595 | 202,868 | 96.00% |
| June | 45.99% | 353,539 | 249,013 | 307,394 | 96.08% |
| July | 52.28% | 415,984 | 517,518 | 205,860 | 98.49% |
| August | 67.62% | 480,528 | 540,811 | 145,577 | 98.47% |
| September | 78.04% | 482,584 | 526,162 | 101,999 | 98.50% |

June demand exceeded actual dispatches by 104,526 units. Compared with March, June demand
was slightly lower while dispatches fell by 121,177 units. Ordered units then rose 17.66%
in July and 15.52% in August. Actual dispatches exceeded ordered units in each of the last
three months, reducing backlog by 205,395 units from the June cutoff. September's on-time
rate remained below the fictional 95% target. The final weekly report also shows why the
monthly view matters. Overdue orders declined from 67 to 45 versus the previous weekly
cutoff while total backlog rose from 94,134 to 101,999 units.

## Category and SKU investigation

Safety-Control and Powertrain-Control both reached 0% OTD in June, while Body-Electronics
and Connectivity held at 100%. By September, Powertrain-Control was at 99.83% and
Safety-Control at 6.18%. Safety-Control accounted for all 45 overdue orders at the final
cutoff. Its three SKUs had zero stock at their latest observations and were the top three
open balances.

| SKU | Outstanding units at 2025-09-30 |
| --- | ---: |
| MCU-002 | 17,548 |
| MCU-003 | 15,927 |
| MCU-001 | 14,457 |

In the simulated operating review, investigate Safety-Control promises and open quantities by
SKU first. Compare expected lot starts, passed units and actual dispatches against incoming
orders before changing schedules. Separate already overdue commitments from recently placed
orders awaiting normal dispatch. Body-Electronics and Connectivity still had open units at
cutoff, illustrating that an open order can be within its promised lead time.

## Quality and delivery association

June's Safety-Control and Powertrain-Control yield was about 93.3%. Their latest June
stock observations were zero. The simulation also imposed capacity and dispatch limits on
both categories during the same interval.

At the fictional 97% lot threshold, 593 of 1,761 due orders linked to at least one below-target
lot shipped on time (33.67%). Among 13,451 due orders with measured links all at or above
target, 10,310 shipped on time (76.65%). Another 55 due orders had no measured link.
Traceability connects dispatches to lots. The comparison uses links observed through cutoff,
including links made after a missed promise. Timing, product mix, demand, capacity and
unshipped orders all affect this descriptive association. Investigate lot and release dates
within a single SKU and period before attributing delays to quality.

## Reproduce the evidence

Load the default clean snapshot and open Streamlit. Executive monthly detail provides
delivery, demand and yield. Set the end date to each month-end for backlog and use the
Orders page to export the SKU ranking. The Production quality page exports the lot link
comparison. The Tableau exporter writes the additive counts for independent reconciliation.

```powershell
python -m mcu_ops.data_generation.generator
python -m mcu_ops.database
python -m mcu_ops.tableau
python -m streamlit run app/streamlit_app.py
```
