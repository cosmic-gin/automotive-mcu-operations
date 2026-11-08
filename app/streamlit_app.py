"""Streamlit entry point for the operations workspace."""
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from mcu_ops.analytics import Analytics, Filters
from mcu_ops.config import settings
from mcu_ops.dashboard import open_runtime
from mcu_ops.database import snapshot_reader

st.set_page_config(page_title="MCU Operations Intelligence", page_icon=":material/memory:", layout="wide")
page = st.navigation([
    st.Page("executive.py", title="Executive overview", icon=":material/dashboard:", default=True),
    st.Page("orders.py", title="Orders and delivery", icon=":material/local_shipping:"),
    st.Page("quality.py", title="Production quality", icon=":material/precision_manufacturing:"),
    st.Page("reliability.py", title="Data reliability", icon=":material/fact_check:"),
])

try:
    config = settings()
    with st.spinner("Opening the validated operational snapshot…"):
        runtime = open_runtime(config)
    with snapshot_reader(runtime.engine) as connection:
        analytics = Analytics(connection)
        options = analytics.products()

        with st.sidebar:
            is_reliability = page.title == "Data reliability"
            st.header("Reporting filters")
            window = st.date_input(
                "Reporting dates", (analytics.start, analytics.as_of),
                min_value=analytics.start, max_value=analytics.as_of, key="period",
                disabled=is_reliability,
            )
            category = st.selectbox("Product category", ["", *options.product_category.unique()],
                                    format_func=lambda item: item or "All categories", key="category",
                                    disabled=is_reliability)
            families = options if not category else options.loc[options.product_category == category]
            family = st.selectbox("Product family", ["", *families.product_family.unique()],
                                  format_func=lambda item: item or "All families", key="family",
                                  disabled=is_reliability)
            segment = st.selectbox("Customer segment", ["", "OEM", "Tier 1", "Distributor"],
                                   format_func=lambda item: item or "All segments", key="segment",
                                   disabled=is_reliability)
            if is_reliability:
                st.caption("Reliability covers the whole loaded snapshot.")
            else:
                st.caption("Customer segment filters orders and dispatches. Stock and yield cover all segments.")
            st.divider()
            st.caption(f"Backend · {config.backend}")
            mode = analytics.quality.get("simulation_mode", "reference")
            st.caption(f"Simulated cutoff · {analytics.as_of.isoformat()} · {mode.capitalize()} replay")
            st.caption(f"Last validated (UTC) · {analytics.quality['validated_at'][:16].replace('T', ' ')}")

        st.caption("FICTIONAL OPERATIONS DATA · AUTOMOTIVE MICROCONTROLLERS")
        if len(window) != 2 and not is_reliability:
            st.info("Choose an end date to apply the reporting period.")
            st.stop()
        filters = Filters(analytics.start, analytics.as_of) if is_reliability else Filters(
            *window, category, family, segment
        )
        st.session_state["_report_context"] = (analytics, filters, config, runtime)
        page.run()
except (OSError, ValueError, RuntimeError, SQLAlchemyError):
    st.error("The snapshot could not be opened or queried. Check the server logs and database setup.")
    import logging

    logging.getLogger(__name__).exception("Streamlit snapshot error")
