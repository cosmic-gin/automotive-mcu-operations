import streamlit as st

from mcu_ops.dashboard import chart, context, format_value, table_with_download

analytics, filters, _, _ = context()
monthly = analytics.query("monthly", filters)
families = analytics.query("performance", filters, grain="family")
categories = analytics.query("performance", filters, grain="category")
orders = analytics.query("orders", filters)
metrics = analytics.headline(filters)

st.title("Orders and delivery")
st.write("Compare promise-date delivery, order-entry demand and open units at the reporting cutoff.")
for col, label, key, kind in zip(
    st.columns(4), ("Fulfilled in entry cohort", "Open at cutoff", "Partially shipped and open", "Average lead time"),
    ("fulfilled_orders", "open_orders", "partial_open_orders", "avg_lead_days"),
    ("count", "count", "count", "days"), strict=True,
):
    col.metric(label, format_value(metrics.get(key), kind), border=True)

left, right = st.columns(2)
with left:
    st.markdown("**Order volume by entry month**")
    chart(monthly, x="month", y="orders_entered", labels={"month": "Entry month", "orders_entered": "Orders"})
    st.markdown("**On-time delivery by product family**")
    chart(families, x="group_name", y="on_time_pct", kind="bar",
          labels={"group_name": "Product family", "on_time_pct": "On time (%)"})
with right:
    st.markdown("**Orders due and missed by promise month**")
    cohort = monthly.rename(columns={"on_time_orders": "On time", "missed_orders": "Missed"})
    chart(cohort, x="month", y=["On time", "Missed"], kind="bar",
          labels={"month": "Promise month", "value": "Due orders"})
    st.markdown("**Outstanding units by category**")
    chart(categories, x="group_name", y="backlog_units", kind="bar",
          labels={"group_name": "Product category", "backlog_units": "Open units"})

st.subheader("Order investigation")
view = st.radio("Order subset", ["Missed promises", "Overdue at cutoff", "Open backlog", "Partially shipped", "All in scope"],
                horizontal=True, key="order_subset")
if view == "Missed promises":
    orders = orders.loc[(orders.due == 1) & (orders.on_time == 0)]
elif view == "Overdue at cutoff":
    orders = orders.loc[orders.overdue == 1]
elif view == "Open backlog":
    orders = orders.loc[orders.remaining_units > 0].sort_values("remaining_units", ascending=False)
elif view == "Partially shipped":
    orders = orders.loc[(orders.shipped_units > 0) & (orders.remaining_units > 0)]
st.caption(f"{len(orders):,} orders · Shipment quantities reconstructed through the selected end date.")
table_with_download(orders, "order_investigation.csv")

st.subheader("Stock trend and backlog by SKU")
inventory = analytics.query("inventory", filters)
chart(inventory, x="snapshot_date", y="inventory_units",
      labels={"snapshot_date": "Snapshot date", "inventory_units": "Observed stock units"})
products = analytics.query("performance", filters, grain="product")
table_with_download(products.sort_values("backlog_units", ascending=False), "product_backlog.csv")
