from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..models import Company, EarningsRecord


class YahooQuoteSummaryProvider:
    base_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"

    def fetch(self, company: Company, generated_at: datetime) -> EarningsRecord | None:
        payload = self._request(company.primary_symbol)
        return self.parse_payload(company, payload, generated_at)

    def _request(self, symbol: str) -> dict[str, Any]:
        url = f"{self.base_url}/{quote(symbol)}?modules=calendarEvents"
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def parse_payload(
        self,
        company: Company,
        payload: dict[str, Any],
        generated_at: datetime,
    ) -> EarningsRecord | None:
        result = ((payload.get("quoteSummary") or {}).get("result") or [])
        if not result:
            return None

        calendar_events = (result[0].get("calendarEvents") or {}).get("earnings") or {}
        earnings_dates = calendar_events.get("earningsDate") or []
        announce_date = self._extract_announce_date(earnings_dates)
        if announce_date is None:
            return None

        return EarningsRecord(
            company_id=company.id,
            company_name=company.name,
            primary_symbol=company.primary_symbol,
            aliases=company.aliases,
            announce_date=announce_date,
            fiscal_period=None,
            source="yahoo_quote_summary",
            source_url=company.official_url,
            fetched_at=generated_at,
            notes="Auto-fetched from Yahoo Finance quoteSummary calendarEvents.",
            cancelled=False,
            stale=False,
        )

    def _extract_announce_date(self, raw_dates: Any):
        if isinstance(raw_dates, dict):
            raw_dates = [raw_dates]

        candidates = []
        for item in raw_dates:
            if not isinstance(item, dict):
                continue
            raw_value = item.get("raw")
            fmt_value = item.get("fmt")
            if raw_value is not None:
                try:
                    candidates.append(datetime.fromtimestamp(int(raw_value), tz=timezone.utc).date())
                    continue
                except (TypeError, ValueError, OSError):
                    pass
            if fmt_value:
                try:
                    candidates.append(datetime.fromisoformat(fmt_value).date())
                except ValueError:
                    continue

        if not candidates:
            return None
        return min(candidates)
