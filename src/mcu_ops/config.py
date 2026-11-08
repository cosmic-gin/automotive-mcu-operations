"""Read runtime configuration from the environment and optional .env file."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    backend: str
    data_dir: Path
    otd_target: float
    yield_target: float
    backlog_growth_target: float
    inventory_floor: float
    dq_max: float


def settings() -> Settings:
    """Load settings at the entry point so tests can override the environment."""
    load_dotenv(dotenv_path=Path.cwd() / ".env", encoding="utf-8-sig")
    backend = os.getenv("MCU_BACKEND", "duckdb")
    if backend not in {"duckdb", "postgresql"}:
        raise ValueError("MCU_BACKEND must be duckdb or postgresql")
    return Settings(
        backend,
        Path(os.getenv("MCU_DATA_DIR", "data")),
        float(os.getenv("MCU_OTD_TARGET", "95")),
        float(os.getenv("MCU_YIELD_TARGET", "97")),
        float(os.getenv("MCU_BACKLOG_GROWTH_TARGET", "20")),
        float(os.getenv("MCU_INVENTORY_FLOOR", "1000")),
        float(os.getenv("MCU_DQ_MAX", "0.5")),
    )
