import streamlit as st

from mcu_ops.analytics import alerts, executive_summary
from mcu_ops.dashboard import chart, context, format_value, quality_status, table_with_download

analytics, filters, config, _ = context()
metrics = analytics.headline(filters)
previous = analytics.headline(filters.previous())
categories = analytics.query("performance", filters, grain="category")
monthly = analytics.query("monthly", filters)
st.title("Executive overview")
st.write(executive_summary(metrics, categories))

for row in (
    [("On-time delivery", "on_time_pct", "pct", "Due orders shipped in full by the promise date."),
     ("Production test yield", "yield_pct", "pct", "Passed units divided by tested units."),
     ("Open backlog", "backlog_units", "count", "Units outstanding across all orders at cutoff.")],
    [("Order fulfillment", "fulfillment_pct", "pct", "Share of orders entered in the period and fully shipped by cutoff."),
     ("Overdue orders", "overdue_orders", "count", "Incomplete orders with a promise date before cutoff."),
     ("Data quality", None, None, "Snapshot-wide row, schema and freshness checks.")],
):
    for col, (label, key, kind, help_text) in zip(st.columns(3), row, strict=True):
        col.metric(label, format_value(metrics.get(key), kind) if key else quality_status(analytics.quality),
                   help=help_text, border=True)

st.subheader("Delivery and demand")
left, right = st.columns(2)
with left:
    st.markdown("**On-time delivery by promise month**")
    chart(monthly, x="month", y="on_time_pct", labels={"month": "Promise month", "on_time_pct": "On time (%)"})
    observed = monthly.dropna(subset=["on_time_pct"])
    if len(observed) > 1:
        low = observed.loc[observed.on_time_pct.idxmin()]
        latest = observed.iloc[-1]
        st.caption(f"Lowest selected month · {low.month:%b %Y} ({low.on_time_pct:.1f}%). "
                   f"Latest selected month · {latest.month:%b %Y} ({latest.on_time_pct:.1f}%).")
with right:
    st.markdown("**Ordered units and actual dispatches**")
    flows = monthly.rename(columns={"ordered_units": "Ordered units", "shipped_units": "Shipped units"})
    chart(flows, x="month", y=["Ordered units", "Shipped units"],
          labels={"month": "Event month", "value": "Units"})

with st.expander("Monthly metrics and demand growth"):
    table_with_download(monthly, "monthly_kpis.csv")

st.subheader("Product category performance")
chart(categories, x="group_name", y="on_time_pct", kind="bar",
      labels={"group_name": "Product category", "on_time_pct": "On time (%)"})
with st.expander("Category metrics and definitions"):
    st.write("Backlog uses the end-date balance. Fulfillment uses order entry dates. "
             "Delivery uses promise dates. Production yield uses production dates.")
    table_with_download(categories, "category_performance.csv")

st.subheader("Operations alerts")
triggered = alerts(metrics, previous, analytics.quality, config)
for alert in triggered:
    st.warning(f"**{alert.metric}** · {alert.message} {alert.investigation}")
if not triggered:
    st.info("The selected observations did not trigger a fictional target.")
st.page_link("orders.py", label="Investigate due orders and backlog")
