# Business requirements

All records, operating targets, and scenarios are fictional. The audience is an operations
manager reviewing customer delivery, production test quality, stock, and pipeline reliability.

| Decision | Evidence | Follow-up |
| --- | --- | --- |
| Are we meeting customer commitments? | Due-cohort on-time rate and affected orders | Inspect split and late shipments |
| Where is demand outpacing shipments? | Order-entry units, shipment-event units and remaining units | Rank products by backlog |
| Is deterioration concentrated? | Product category and family trends | Examine inventory and lot quality |
| Is quality associated with delivery? | Product trends and lot-linked delivery outcomes | Investigate shipment allocation and other explanations |
| Can the team trust the numbers? | Validation rejects and source freshness | Review quarantine and execution history |
| Can the weekly review run consistently? | Scheduled, versioned report logic | Inspect CI status and report artifacts |

An order represents one product line. Orders can ship in several installments. A lot is optional
on a shipment, and a linked lot must match the product on the order. This model supports
order-level fulfillment without splitting a customer's purchase order into a separate header.
There are no cancellations, returns or timestamp-level delivery promises in the simulation.
Shipped units are a proxy for delivery and a measure of realized throughput.
