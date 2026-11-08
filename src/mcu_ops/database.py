"""Store one validated snapshot with shared SQLAlchemy access for both backends."""
import argparse
import json
import logging
import os
from datetime import date
from importlib.resources import files
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError

from mcu_ops.config import Settings, settings
from mcu_ops.etl import ValidatedSnapshot, ValidationFailed, run_etl
from mcu_ops.validation import KEYS

LOG = logging.getLogger(__name__)


def make_engine(config: Settings, *, memory: bool = False) -> Engine:
    """Build an engine without interpolating credentials into a string URL."""
    if config.backend == "duckdb":
        if memory:
            return create_engine("duckdb:///:memory:")
        config.data_dir.mkdir(parents=True, exist_ok=True)
        database = str((config.data_dir / "operations.duckdb").resolve())
        return create_engine(URL.create("duckdb", database=database))

    override = os.getenv("MCU_POSTGRES_URL")
    if override:
        return create_engine(override, pool_pre_ping=True, hide_parameters=True)
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise ValueError("Set POSTGRES_PASSWORD in .env for PostgreSQL")
    return create_engine(
        URL.create(
            "postgresql+psycopg", username=os.getenv("POSTGRES_USER", "mcu"),
            password=password, host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5432")), database=os.getenv("POSTGRES_DB", "mcu"),
        ),
        pool_pre_ping=True,
        hide_parameters=True,
    )


def sql_source(folder: str, filename: str) -> str:
    return files("mcu_ops").joinpath("sql", folder, filename).read_text(encoding="utf-8")


def replace_snapshot(engine: Engine, snapshot: ValidatedSnapshot) -> dict[str, int]:
    """Atomically replace project-owned tables in a dedicated analytics database."""
    schema = sql_source("schema", "snapshot.sql")
    row_counts = {}
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("SELECT pg_advisory_xact_lock(51803429)"))
        for table in ("snapshot_metadata", *reversed(KEYS)):
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(text(statement))
        for name in KEYS:
            frame = snapshot.tables[name]
            columns = list(frame.columns)
            placeholders = ", ".join(f":{column}" for column in columns)
            # Identifiers are defined by the checked-in schema, values are bound.
            statement = text(f"INSERT INTO {name} ({', '.join(columns)}) VALUES ({placeholders})")
            for offset in range(0, len(frame), 2_000):
                conn.execute(statement, frame.iloc[offset:offset + 2_000].to_dict("records"))
            row_counts[name] = conn.scalar(text(f"SELECT COUNT(*) FROM {name}"))
        quality = snapshot.quality
        conn.execute(
            text("""INSERT INTO snapshot_metadata VALUES (1, :run, :start, :as_of, :quality)"""),
            {
                "run": quality["run_id"], "start": date.fromisoformat(quality["start"]),
                "as_of": date.fromisoformat(quality["as_of"]), "quality": json.dumps(quality),
            },
        )
    LOG.info("Committed %s snapshot %s: %s", engine.dialect.name, quality["run_id"], row_counts)
    return row_counts


def metadata(engine: Engine) -> dict:
    """Return the quality record committed with the currently queryable tables."""
    with engine.connect() as conn:
        encoded = conn.scalar(text("SELECT quality_json FROM snapshot_metadata WHERE singleton = 1"))
    if encoded is None:
        raise RuntimeError("Database contains no loaded snapshot")
    return json.loads(encoded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--mode", choices=("strict", "quarantine"), default="strict")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = settings()
        source = args.source or config.data_dir / "raw" / "clean"
        snapshot = run_etl(source, config.data_dir / "etl", strict=args.mode == "strict")
        engine = make_engine(config)
        try:
            replace_snapshot(engine, snapshot)
        finally:
            engine.dispose()
    except (OSError, ValueError, ValidationFailed, SQLAlchemyError) as exc:
        LOG.error("Load failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
