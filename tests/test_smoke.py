from mcu_ops.config import settings


def test_settings_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MCU_BACKEND", "duckdb")
    monkeypatch.setenv("MCU_DATA_DIR", str(tmp_path))
    assert settings().backend == "duckdb"
    assert settings().data_dir == tmp_path
