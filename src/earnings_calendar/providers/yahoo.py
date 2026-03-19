from __future__ import annotations

from datetime import date, datetime

from ..models import Company, EarningsRecord


class YahooQuoteSummaryProvider:
    def fetch(self, company: Company, generated_at: datetime) -> EarningsRecord | None:
        import yfinance as yf

        ticker = yf.Ticker(company.primary_symbol)

        announce_date = self._extract_announce_date_from_calendar(ticker.calendar)
        notes = "Auto-fetched from yfinance calendar."
        if announce_date is None:
            announce_date = self._extract_announce_date_from_earnings_dates(ticker)
            notes = "Auto-fetched from yfinance earnings dates."

        if announce_date is None:
            return None

        return EarningsRecord(
            company_id=company.id,
            company_name=company.name,
            primary_symbol=company.primary_symbol,
            aliases=company.aliases,
            announce_date=announce_date,
            fiscal_period=None,
            source="yfinance",
            source_url=company.official_url,
            fetched_at=generated_at,
            notes=notes,
            cancelled=False,
            stale=False,
        )

    def _extract_announce_date_from_calendar(self, calendar) -> date | None:
        if not isinstance(calendar, dict):
            return None
        raw_dates = calendar.get("Earnings Date")
        return self._normalize_dates(raw_dates)

    def _extract_announce_date_from_earnings_dates(self, ticker) -> date | None:
        try:
            earnings_dates = ticker.get_earnings_dates(limit=1)
        except Exception:  # noqa: BLE001
            return None

        if earnings_dates is None or getattr(earnings_dates, "empty", True):
            return None

        try:
            first_index = earnings_dates.index[0]
        except Exception:  # noqa: BLE001
            return None

        return self._to_date(first_index)

    def _normalize_dates(self, raw_dates) -> date | None:
        if raw_dates is None:
            return None
        if not isinstance(raw_dates, (list, tuple)):
            raw_dates = [raw_dates]

        candidates = []
        for item in raw_dates:
            normalized = self._to_date(item)
            if normalized is not None:
                candidates.append(normalized)
        if not candidates:
            return None
        return min(candidates)

    def _to_date(self, value) -> date | None:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime().date()
        if hasattr(value, "date"):
            try:
                return value.date()
            except TypeError:
                return None
        return None
