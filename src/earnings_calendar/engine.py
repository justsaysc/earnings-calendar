from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

from .models import Company, EarningsRecord

STALE_FALLBACK_DAYS = 45
CANCELLATION_RETENTION_DAYS = 45


def load_state(path: str) -> dict[str, EarningsRecord]:
    state_path = Path(path)
    if not state_path.exists():
        return {}

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    records = raw.get("records", [])
    return {
        record["company_id"]: EarningsRecord.from_dict(record)
        for record in records
    }


def save_state(path: Path, generated_at: datetime, records: list[EarningsRecord], errors: list[str]) -> None:
    payload = {
        "generated_at": generated_at.isoformat(),
        "records": [record.to_dict() for record in records],
        "errors": errors,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_current_records(
    companies: list[Company],
    overrides: dict[str, EarningsRecord],
    previous_records: dict[str, EarningsRecord],
    providers: dict[str, object],
    generated_at: datetime,
    today: date,
) -> tuple[list[EarningsRecord], list[str]]:
    resolved: list[EarningsRecord] = []
    errors: list[str] = []

    for company in companies:
        if not company.enabled:
            continue

        override = overrides.get(company.id)
        if override is not None:
            resolved.append(override)
            continue

        provider = providers.get(company.provider)
        record = None
        if provider is None:
            errors.append(f"[{company.id}] Unknown provider: {company.provider}")
        else:
            try:
                record = provider.fetch(company, generated_at)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"[{company.id}] Provider fetch failed: {exc}")

        if record is None:
            previous = previous_records.get(company.id)
            if previous and not previous.cancelled:
                cutoff = today - timedelta(days=STALE_FALLBACK_DAYS)
                if previous.announce_date >= cutoff:
                    resolved.append(
                        replace(
                            previous,
                            fetched_at=generated_at,
                            stale=True,
                        )
                    )
            continue

        resolved.append(record)

    resolved.sort(key=lambda item: (item.announce_date, item.company_name))
    return resolved, errors


def build_published_records(
    companies: list[Company],
    current_records: list[EarningsRecord],
    previous_records: dict[str, EarningsRecord],
    generated_at: datetime,
    today: date,
) -> list[EarningsRecord]:
    published = {record.company_id: record for record in current_records}
    current_ids = {company.id for company in companies if company.enabled}
    cutoff = today - timedelta(days=CANCELLATION_RETENTION_DAYS)

    for company_id, previous in previous_records.items():
        if company_id in current_ids:
            continue
        if previous.announce_date < cutoff:
            continue
        published[company_id] = replace(
            previous,
            fetched_at=generated_at,
            cancelled=True,
            stale=False,
        )

    return sorted(published.values(), key=lambda item: (item.announce_date, item.company_name))

