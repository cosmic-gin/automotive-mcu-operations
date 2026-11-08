"""Extract CSV snapshots, validate records, and write clean and quarantine artifacts."""
import argparse
import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from mcu_ops.data_generation.generator import COLUMNS
from mcu_ops.validation import KEYS, RuleViolation, Validator, parse_record

LOG = logging.getLogger(__name__)
QUARANTINE_FIELDS = (
    "source_table", "record_id", "failed_rule", "error_description", "validated_at", "original_record"
)


@dataclass
class ValidatedSnapshot:
    tables: dict[str, pd.DataFrame]
    quarantine: pd.DataFrame
    quality: dict


class ValidationFailed(RuntimeError):
    """Strict processing rejected the snapshot."""


def extract(root: Path) -> tuple[dict[str, pd.DataFrame], dict]:
    """Preserve raw CSV field strings so quarantine can show the original values."""
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("fictional") is not True:
        raise ValueError("This project accepts only fictional simulation manifests")
    frames = {
        name: pd.read_csv(root / f"{name}.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
        for name in KEYS
    }
    return frames, manifest


def _freshness(manifest: dict, as_of: date, max_age_days: int) -> list[dict]:
    results = []
    dates = manifest.get("source_dates")
    if not isinstance(dates, dict):
        dates = {}
    for table in KEYS:
        raw = dates.get(table)
        try:
            age = (as_of - date.fromisoformat(raw)).days
        except (ValueError, TypeError):
            age = None
        results.append({
            "table": table, "source_date": raw, "age_days": age,
            "status": "fresh" if age is not None and 0 <= age <= max_age_days else "failed",
        })
    return results


def validate(frames: dict[str, pd.DataFrame], manifest: dict, max_age_days: int = 7) -> ValidatedSnapshot:
    """Validate in dependency order. Shipments consume balances in date and ID order."""
    as_of = date.fromisoformat(manifest["as_of"])
    start = date.fromisoformat(manifest["start"])
    if as_of < start or max_age_days < 0:
        raise ValueError("Invalid reporting window or freshness threshold")
    validator = Validator(as_of)
    timestamp = datetime.now(UTC).isoformat()
    rejects = []
    counts = []
    schemas = []
    for table, key in KEYS.items():
        frame = frames[table]
        expected = COLUMNS[table].split()
        missing = sorted(set(expected) - set(frame.columns))
        if missing:
            schemas.append({"table": table, "missing_columns": missing})
        if table == "shipments" and not missing:
            frame = frame.sort_values(["shipment_date", key], kind="stable")
        for original in frame.to_dict("records"):
            try:
                if missing:
                    raise RuleViolation("schema_columns", f"Missing columns: {', '.join(missing)}")
                row = parse_record(
                    {column: original[column] for column in expected}, nullable_lot=table == "shipments"
                )
                validator.accept(table, row)
            except RuleViolation as exc:
                rejects.append({
                    "source_table": table, "record_id": original.get(key, ""),
                    "failed_rule": exc.rule, "error_description": str(exc),
                    "validated_at": timestamp, "original_record": json.dumps(original, default=str),
                })
        accepted = len(validator.rows[table])
        counts.append({"table": table, "processed": len(frame), "accepted": accepted,
                       "rejected": len(frame) - accepted})
        LOG.info("%s processed=%d accepted=%d rejected=%d", table, len(frame), accepted, len(frame) - accepted)

    # Keep source status for audit. All analytics derive fulfillment from accepted shipment rows.
    tables = {
        name: pd.DataFrame(list(rows.values()), columns=COLUMNS[name].split())
        for name, rows in validator.rows.items()
    }
    processed = sum(item["processed"] for item in counts)
    quality = {
        "run_id": uuid4().hex, "validated_at": timestamp, "start": start.isoformat(),
        "as_of": as_of.isoformat(), "scenario": manifest.get("scenario", "unknown"),
        "simulation_mode": manifest.get("simulation_mode", "reference"),
        "processed": processed, "accepted": processed - len(rejects), "rejected": len(rejects),
        "rejection_pct": 100 * len(rejects) / processed if processed else None,
        "tables": counts, "rules": dict(Counter(row["failed_rule"] for row in rejects)),
        "freshness": _freshness(manifest, as_of, max_age_days), "schema_failures": schemas,
    }
    return ValidatedSnapshot(tables, pd.DataFrame(rejects, columns=QUARANTINE_FIELDS), quality)


def failed(quality: dict) -> bool:
    return bool(quality["rejected"] or quality["schema_failures"] or any(
        source["status"] == "failed" for source in quality["freshness"]
    ))


def run_etl(source: Path, output: Path, *, strict: bool = True) -> ValidatedSnapshot:
    """Always preserve validation evidence. Publish clean CSVs only after mode checks."""
    frames, manifest = extract(source)
    result = validate(frames, manifest)
    run_dir = output / "quality" / result.quality["run_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    result.quarantine.to_csv(run_dir / "quarantine.csv", index=False)
    (run_dir / "quality.json").write_text(json.dumps(result.quality, indent=2) + "\n", encoding="utf-8")
    if failed(result.quality):
        LOG.warning("Validation flagged source problems. Evidence: %s", run_dir)
        if strict:
            raise ValidationFailed(f"Strict validation failed. Review {run_dir}")
    processed_dir = output / "processed" / result.quality["run_id"]
    processed_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in result.tables.items():
        frame.to_csv(processed_dir / f"{name}.csv", index=False)
    LOG.info("Validation evidence and processed datasets written under %s", output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/raw/clean"))
    parser.add_argument("--output", type=Path, default=Path("data/etl"))
    parser.add_argument("--mode", choices=("strict", "quarantine"), default="strict")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        run_etl(args.source, args.output, strict=args.mode == "strict")
    except (OSError, ValueError, ValidationFailed) as exc:
        LOG.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
