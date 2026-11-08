"""Dashboard connection, presentation, and isolated quality demonstration helpers."""
import json
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.engine import Engine

from mcu_ops.config import Settings
from mcu_ops.data_generation.generator import Simulation, add_duplicate, write_sources
from mcu_ops.database import make_engine, replace_snapshot
from mcu_ops.etl import extract, failed, run_etl, validate

COLORS = ["#126b80", "#df8052", "#5163a2", "#54865d"]


@dataclass
class Runtime:
    engine: Engine
    audit_root: Path
    temp: TemporaryDirectory | None = None


@st.cache_resource(show_spinner=False)
def _ephemeral_demo(config: Settings) -> Runtime:
    temp = TemporaryDirectory(prefix="mcu-demo-")
    base = Path(temp.name)
    source = base / "raw"
    write_sources(source, Simulation())
    audit = base / "etl"
    result = run_etl(source, audit)
    engine = make_engine(replace(config, data_dir=base))
    replace_snapshot(engine, result)
    return Runtime(engine, audit, temp)


@st.cache_resource(show_spinner=False)
def _local_runtime(config: Settings) -> Runtime:
    return Runtime(make_engine(config), config.data_dir / "etl")


def open_runtime(config: Settings) -> Runtime:
    if config.backend == "duckdb" and not (config.data_dir / "operations.duckdb").exists():
        return _ephemeral_demo(config)
    return _local_runtime(config)


def context():
    return st.session_state["_report_context"]


def format_value(value, kind="count") -> str:
    if value is None or pd.isna(value):
        return "Unavailable"
    if kind == "pct":
        return f"{value:.1f}%"
    if kind == "days":
        return f"{value:.1f} days"
    return f"{value:,.0f}"


def chart(frame, *, x, y, labels, kind="line", color=None):
    if frame.empty:
        st.info("No observations for the selected filters.")
        return
    if kind == "bar":
        figure = px.bar(frame, x=x, y=y, color=color, labels=labels, color_discrete_sequence=COLORS,
                        barmode="group")
    else:
        figure = px.line(frame, x=x, y=y, color=color, labels=labels, color_discrete_sequence=COLORS,
                         markers=True)
    figure.update_layout(margin=dict(l=8, r=8, t=14, b=8), height=340, legend_title_text="")
    st.plotly_chart(figure, width="stretch")


def table_with_download(frame: pd.DataFrame, filename: str):
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Download CSV", frame.to_csv(index=False), file_name=filename, mime="text/csv",
                       key=filename)


def quality_status(quality: dict) -> str:
    return "Review" if failed(quality) else "Passed"


@st.cache_data(show_spinner=False)
def duplicate_demo() -> pd.DataFrame:
    """Validate an isolated, deterministic sample without writing any canonical data."""
    with TemporaryDirectory(prefix="mcu-duplicate-") as temp:
        source = Path(temp)
        write_sources(source, Simulation(months=6, daily_orders=4))
        frames, manifest = extract(source)
        frames["customer_orders"] = add_duplicate(frames["customer_orders"])
        return validate(frames, manifest).quarantine


def history(audit: Path) -> pd.DataFrame:
    rows = []
    for path in audit.glob("quality/*/quality.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        rows.append({key: record[key] for key in ("run_id", "validated_at", "scenario", "processed",
                                                 "rejected", "rejection_pct")})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("validated_at", ascending=False)


def execution_history(audit: Path) -> pd.DataFrame:
    rows = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in audit.glob("executions/*.json")
    ]
    if not rows:
        return pd.DataFrame()
    fields = ["started_at", "finished_at", "backend", "status", "stage", "duration_seconds", "execution_id"]
    return pd.DataFrame(rows).reindex(columns=fields).sort_values("started_at", ascending=False)
