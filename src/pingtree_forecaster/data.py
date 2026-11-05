"""Loaders for the anonymized partner-month dataset and the parameter file."""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def load_params(path: Path | str = DATA / "params.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_partners(path: Path | str = DATA / "partner_monthly.csv", names: dict | None = None) -> dict:
    """Return {"months": [...], "partners": [{"name", "m": {month: [requests, accepted, sales, revenue]}}]}.

    `names` optionally maps partner_id -> commercial name (private file, never committed).
    """
    by: dict[str, dict] = {}
    months = set()
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = r["partner_id"]
            by.setdefault(pid, {})[r["month"]] = [int(r["requests"]), int(r["accepted"]), int(r["sales"]), float(r["revenue_eur"])]
            months.add(r["month"])
    partners = [{"id": pid, "name": (names or {}).get(pid, pid), "m": m} for pid, m in sorted(by.items())]
    return {"months": sorted(months), "partners": partners}


def load_private_names(path: Path | str = DATA / "private" / "partner_names.csv") -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as f:
        return {r["partner_id"]: r["commercial_name"] for r in csv.DictReader(f)}
