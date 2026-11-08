import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from mcu_ops.analytics import Analytics, Filters
from mcu_ops.config import settings
from mcu_ops.data_generation.generator import Simulation, write_sources
from mcu_ops.database import make_engine, replace_snapshot
from mcu_ops.etl import run_etl


def test_four_pages_filter_metrics_and_detect_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("MCU_BACKEND", "duckdb")
    monkeypatch.setenv("MCU_DATA_DIR", str(tmp_path))
    source = tmp_path / "raw"
    write_sources(source, Simulation(months=6, daily_orders=6))
    engine = make_engine(settings())
    replace_snapshot(engine, run_etl(source, tmp_path / "etl"))
    analytics = Analytics(engine)
    first = analytics.start.replace(month=3)
    last = analytics.as_of
    category = "Safety-Control MCUs"
    expected = analytics.headline(Filters(first, last, category))
    engine.dispose()

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py", default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value == "Executive overview"
    app.date_input(key="period").set_value((first, last)).run()
    app.selectbox(key="category").set_value(category)
    app.run()
    assert not app.exception
    assert app.session_state["_report_context"][1] == Filters(first, last, category)
    assert app.metric[0].value == f"{expected['on_time_pct']:.1f}%"
    assert app.get("plotly_chart")

    for filename, title in (
        ("orders", "Orders and delivery"), ("quality", "Production quality"),
        ("reliability", "Data reliability"),
    ):
        app.switch_page(f"{filename}.py").run()
        assert not app.exception
        assert app.title[0].value == title
    app.button(key="duplicate_demo").click().run()
    assert not app.exception
    assert "duplicate_key" in app.warning[0].value
    assert app.date_input(key="period").proto.disabled
    for table in app.dataframe:
        columns = json.loads(table.proto.columns)
        assert columns
        visible = [config for config in columns.values() if not config.get("hidden")]
        assert visible and all(config.get("alignment") == "center" for config in visible), columns
