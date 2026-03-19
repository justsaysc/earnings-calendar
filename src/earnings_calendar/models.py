from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Company:
    id: str
    name: str
    primary_symbol: str
    aliases: tuple[str, ...]
    market: str
    provider: str
    official_url: str
    enabled: bool = True

    @classmethod
    def from_dict(cls, raw: dict) -> "Company":
        return cls(
            id=raw["id"],
            name=raw["name"],
            primary_symbol=raw["primary_symbol"],
            aliases=tuple(raw.get("aliases", [raw["primary_symbol"]])),
            market=raw["market"],
            provider=raw["provider"],
            official_url=raw["official_url"],
            enabled=bool(raw.get("enabled", True)),
        )


@dataclass(frozen=True)
class EarningsRecord:
    company_id: str
    company_name: str
    primary_symbol: str
    aliases: tuple[str, ...]
    announce_date: date
    fiscal_period: str | None
    source: str
    source_url: str | None
    fetched_at: datetime
    notes: str | None = None
    cancelled: bool = False
    stale: bool = False

    def uid(self) -> str:
        return f"earnings:{self.company_id}"

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "primary_symbol": self.primary_symbol,
            "aliases": list(self.aliases),
            "announce_date": self.announce_date.isoformat(),
            "fiscal_period": self.fiscal_period,
            "source": self.source,
            "source_url": self.source_url,
            "fetched_at": self.fetched_at.isoformat(),
            "notes": self.notes,
            "cancelled": self.cancelled,
            "stale": self.stale,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "EarningsRecord":
        return cls(
            company_id=raw["company_id"],
            company_name=raw["company_name"],
            primary_symbol=raw["primary_symbol"],
            aliases=tuple(raw.get("aliases", [raw["primary_symbol"]])),
            announce_date=date.fromisoformat(raw["announce_date"]),
            fiscal_period=raw.get("fiscal_period"),
            source=raw["source"],
            source_url=raw.get("source_url"),
            fetched_at=datetime.fromisoformat(raw["fetched_at"]),
            notes=raw.get("notes"),
            cancelled=bool(raw.get("cancelled", False)),
            stale=bool(raw.get("stale", False)),
        )

