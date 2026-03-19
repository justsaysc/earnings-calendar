#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from earnings_calendar.config import load_overrides, load_watchlist
from earnings_calendar.engine import (
    build_published_records,
    load_state,
    resolve_current_records,
    save_state,
)
from earnings_calendar.ics import build_calendar
from earnings_calendar.providers.yahoo import YahooQuoteSummaryProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a stock earnings ICS calendar.")
    parser.add_argument(
        "--watchlist",
        default=str(ROOT / "config" / "watchlist.json"),
        help="Path to watchlist JSON.",
    )
    parser.add_argument(
        "--overrides",
        default=str(ROOT / "config" / "manual_overrides.json"),
        help="Path to manual overrides JSON.",
    )
    parser.add_argument(
        "--state",
        default=str(ROOT / "data" / "state.json"),
        help="Path to persisted state JSON.",
    )
    parser.add_argument(
        "--snapshot",
        default=str(ROOT / "data" / "resolved_events.json"),
        help="Path to resolved events snapshot JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "earnings.ics"),
        help="Path to generated ICS file.",
    )
    return parser.parse_args()


def ensure_parent(path_str: str) -> Path:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_snapshot(path: Path, generated_at: datetime, current_records, published_records, errors) -> None:
    payload = {
        "generated_at": generated_at.isoformat(),
        "current_records": [record.to_dict() for record in current_records],
        "published_records": [record.to_dict() for record in published_records],
        "errors": errors,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    generated_at = datetime.now(timezone.utc)
    today = date.today()

    watchlist_config = load_watchlist(args.watchlist)
    companies = watchlist_config["companies"]
    calendar_name = watchlist_config["calendar_name"]

    overrides = load_overrides(args.overrides, companies, generated_at)
    previous_records = load_state(args.state)

    providers = {
        "yahoo": YahooQuoteSummaryProvider(),
    }

    current_records, errors = resolve_current_records(
        companies=companies,
        overrides=overrides,
        previous_records=previous_records,
        providers=providers,
        generated_at=generated_at,
        today=today,
    )

    published_records = build_published_records(
        companies=companies,
        current_records=current_records,
        previous_records=previous_records,
        generated_at=generated_at,
        today=today,
    )

    output_path = ensure_parent(args.output)
    snapshot_path = ensure_parent(args.snapshot)
    state_path = ensure_parent(args.state)

    ics_text = build_calendar(
        records=published_records,
        calendar_name=calendar_name,
        generated_at=generated_at,
    )
    output_path.write_text(ics_text, encoding="utf-8")

    write_snapshot(snapshot_path, generated_at, current_records, published_records, errors)
    save_state(state_path, generated_at, published_records, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

    print(f"Generated {len(published_records)} calendar events -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

