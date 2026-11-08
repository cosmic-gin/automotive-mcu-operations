import pandas as pd
import streamlit as st

from mcu_ops.dashboard import (
    chart,
    context,
    duplicate_demo,
    execution_history,
    history,
    quality_status,
    table_with_download,
)

analytics, _, _, runtime = context()
quality = analytics.quality
st.title("Data reliability")
st.write("Validation, quarantine and freshness refer to the loaded snapshot across all business filters.")
st.caption(f"Loaded run · {quality['run_id']} · {quality['scenario']} · {quality_status(quality)}")
for col, label, key in zip(st.columns(3), ("Processed", "Accepted", "Rejected"),
                           ("processed", "accepted", "rejected"), strict=True):
    col.metric(label, f"{quality[key]:,}", border=True)
if quality["rejection_pct"] is not None:
    st.caption(f"Snapshot rejection rate · {quality['rejection_pct']:.3f}%")

st.subheader("Source checks")
st.dataframe(pd.DataFrame(quality["tables"]), hide_index=True, width="stretch")
st.dataframe(pd.DataFrame(quality["freshness"]), hide_index=True, width="stretch")
if quality["schema_failures"]:
    st.error("Source schema failures were recorded.")
    st.json(quality["schema_failures"])
if quality["rules"]:
    rules = pd.DataFrame(list(quality["rules"].items()), columns=["rule", "rejected"])
    chart(rules, x="rule", y="rejected", kind="bar", labels={"rule": "Primary rule", "rejected": "Rows"})
    path = runtime.audit_root / "quality" / quality["run_id"] / "quarantine.csv"
    if path.is_file():
        table_with_download(pd.read_csv(path), "quarantine.csv")
else:
    st.success("The loaded run has no row-level rejections.")

st.subheader("Controlled duplicate demonstration")
st.write("Add one duplicate to an isolated fictional sample and inspect the quarantine result.")
if st.button("Detect a duplicate order", key="duplicate_demo"):
    with st.spinner("Validating the isolated sample…"):
        result = duplicate_demo()
    st.warning(f"{len(result)} record quarantined with rule {result.iloc[0].failed_rule}.")
    table_with_download(result, "duplicate_demo.csv")

st.subheader("Pipeline history")
runs = history(runtime.audit_root)
if runs.empty:
    st.info("Local validation audit files are unavailable for this database connection.")
else:
    table_with_download(runs, "validation_history.csv")


executions = execution_history(runtime.audit_root)
if not executions.empty:
    st.subheader("Scheduled and on-demand report runs")
    table_with_download(executions, "execution_history.csv")
