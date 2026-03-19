from __future__ import annotations

import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from earnings_calendar.engine import build_published_records, resolve_current_records
from earnings_calendar.models import Company, EarningsRecord
from earnings_calendar.providers.yahoo import YahooQuoteSummaryProvider


class DummyProvider:
    def __init__(self, record=None):
        self.record = record

    def fetch(self, company, generated_at):
        return self.record


class EngineTests(unittest.TestCase):
    def test_yahoo_payload_parser_extracts_announce_date(self):
        fixture_path = ROOT / "tests" / "fixtures" / "yahoo_tencent.json"
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        company = Company(
            id="tencent",
            name="腾讯",
            primary_symbol="0700.HK",
            aliases=("0700.HK",),
            market="HK",
            provider="yahoo",
            official_url="https://www.tencent.com/en-us/investors.html",
            enabled=True,
        )
        provider = YahooQuoteSummaryProvider()
        record = provider.parse_payload(company, payload, datetime(2026, 3, 19, tzinfo=timezone.utc))
        self.assertIsNotNone(record)
        self.assertEqual(record.announce_date.isoformat(), "2026-05-13")
        self.assertEqual(record.uid(), "earnings:tencent")

    def test_fallback_and_cancellation_flow(self):
        generated_at = datetime(2026, 3, 19, tzinfo=timezone.utc)
        today = date(2026, 3, 19)

        current_company = Company(
            id="tencent",
            name="腾讯",
            primary_symbol="0700.HK",
            aliases=("0700.HK",),
            market="HK",
            provider="dummy",
            official_url="https://example.com/tencent",
            enabled=True,
        )
        previous_current = EarningsRecord(
            company_id="tencent",
            company_name="腾讯",
            primary_symbol="0700.HK",
            aliases=("0700.HK",),
            announce_date=date(2026, 5, 13),
            fiscal_period=None,
            source="manual_override",
            source_url="https://example.com/tencent",
            fetched_at=generated_at,
            notes=None,
            cancelled=False,
            stale=False,
        )
        removed_previous = EarningsRecord(
            company_id="tesla",
            company_name="Tesla",
            primary_symbol="TSLA",
            aliases=("TSLA",),
            announce_date=date(2026, 4, 20),
            fiscal_period=None,
            source="manual_override",
            source_url="https://example.com/tesla",
            fetched_at=generated_at,
            notes=None,
            cancelled=False,
            stale=False,
        )

        current_records, errors = resolve_current_records(
            companies=[current_company],
            overrides={},
            previous_records={
                "tencent": previous_current,
                "tesla": removed_previous,
            },
            providers={"dummy": DummyProvider(record=None)},
            generated_at=generated_at,
            today=today,
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(current_records), 1)
        self.assertTrue(current_records[0].stale)

        published = build_published_records(
            companies=[current_company],
            current_records=current_records,
            previous_records={
                "tencent": previous_current,
                "tesla": removed_previous,
            },
            generated_at=generated_at,
            today=today,
        )

        by_id = {record.company_id: record for record in published}
        self.assertFalse(by_id["tencent"].cancelled)
        self.assertTrue(by_id["tesla"].cancelled)


if __name__ == "__main__":
    unittest.main()

