import json
from pathlib import Path

import pytest

from mcu_ops.config import settings
from mcu_ops.data_generation.generator import Simulation, write_sources
from mcu_ops.reporting import run_cycle


def test_report_and_failed_execution_are_auditable(tmp_path, monkeypatch):
    monkeypatch.setenv("MCU_BACKEND", "duckdb")
    monkeypatch.setenv("MCU_DATA_DIR", str(tmp_path))
    config = settings()
    reports = tmp_path / "reports"
    simulation = Simulation(months=6, daily_orders=4)
    source = tmp_path / "raw"
    write_sources(source, simulation)
    output = run_cycle(config, source, reports)
    report = output.read_text(encoding="utf-8")
    assert "2025-06-24 through 2025-06-30" in report
    assert "2025-06-17 through 2025-06-23" in report
    assert "| Production test yield |" in report
    assert "## Investigations" in report
    assert "**Passed**" in report
    with pytest.raises(FileNotFoundError):
        run_cycle(config, tmp_path / "missing", reports)
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in Path(tmp_path / "etl" / "executions").glob("*.json")
    ]
    assert {record["status"] for record in records} == {"succeeded", "failed"}
    rejected = next(record for record in records if record["status"] == "failed")
    assert rejected["stage"] == "validate"
    assert rejected["error_type"] == "FileNotFoundError"
    assert list(reports.glob("*/*.md")) == [output]
