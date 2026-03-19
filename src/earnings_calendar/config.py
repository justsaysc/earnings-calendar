from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Company, EarningsRecord


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_watchlist(path: str) -> dict:
    raw = _load_json(path)
    companies = [Company.from_dict(item) for item in raw["companies"]]

    seen_ids: set[str] = set()
    for company in companies:
        if company.id in seen_ids:
            raise ValueError(f"Duplicate company id: {company.id}")
        seen_ids.add(company.id)

    return {
        "calendar_name": raw.get("calendar_name", "股票财报日历"),
        "timezone": raw.get("timezone", "Asia/Shanghai"),
        "companies": companies,
    }


def load_overrides(path: str, companies: list[Company], generated_at: datetime) -> dict[str, EarningsRecord]:
    raw = _load_json(path)
    raw_companies = raw.get("companies", {})
    company_map = {company.id: company for company in companies}
    overrides: dict[str, EarningsRecord] = {}

    for company_id, item in raw_companies.items():
        company = company_map.get(company_id)
        if company is None:
            continue
        overrides[company_id] = EarningsRecord(
            company_id=company.id,
            company_name=company.name,
            primary_symbol=company.primary_symbol,
            aliases=company.aliases,
            announce_date=datetime.fromisoformat(item["announce_date"]).date(),
            fiscal_period=item.get("fiscal_period"),
            source="manual_override",
            source_url=item.get("source_url", company.official_url),
            fetched_at=generated_at,
            summary=item.get("summary"),
            notes=item.get("notes"),
            cancelled=False,
            stale=False,
        )

    return overrides
