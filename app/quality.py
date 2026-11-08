import streamlit as st

from mcu_ops.dashboard import chart, context, format_value, table_with_download

analytics, filters, config, _ = context()
metrics = analytics.headline(filters)
families = analytics.query("performance", filters, grain="family")
monthly = analytics.query("monthly", filters)
lots = analytics.query("lots", filters)
linked = analytics.query("lot_link", filters, yield_target=config.yield_target)

st.title("Production quality")
st.write("Yield and defect rate are weighted by units tested in the production-date cohort.")
for col, label, key, kind in zip(
    st.columns(3), ("Weighted yield", "Defect rate", "Tested units"),
    ("yield_pct", "defect_pct", "tested_units"), ("pct", "pct", "count"), strict=True,
):
    col.metric(label, format_value(metrics.get(key), kind), border=True)

left, right = st.columns(2)
with left:
    st.markdown("**Weighted yield by production month**")
    chart(monthly, x="month", y="yield_pct", labels={"month": "Production month", "yield_pct": "Yield (%)"})
with right:
    st.markdown("**Defect rate by product family**")
    chart(families, x="group_name", y="defect_pct", kind="bar",
          labels={"group_name": "Product family", "defect_pct": "Defects (%)"})

st.subheader("Delivery outcomes by linked lot quality")
st.caption(f"Each due order enters one group using dispatch links observed by cutoff. "
           f"The fictional lot target is {config.yield_target:g}%. The grouping describes an association "
           "among orders with observed links and includes dispatches after the promise date.")
chart(linked, x="trace_group", y="on_time_pct", kind="bar",
      labels={"trace_group": "Lot trace group", "on_time_pct": "On time (%)"})
table_with_download(linked, "linked_quality_delivery.csv")

st.subheader("Lot-level quality")
table_with_download(lots, "production_lots.csv")
