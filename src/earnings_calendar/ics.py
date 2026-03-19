from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .models import EarningsRecord


def build_calendar(records: list[EarningsRecord], calendar_name: str, generated_at: datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//Codex//Stock Earnings Calendar//EN",
        "METHOD:PUBLISH",
        _line("X-WR-CALNAME", calendar_name),
        "X-PUBLISHED-TTL:PT12H",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
    ]

    for record in records:
        lines.extend(_event_lines(record, generated_at))

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold_lines(lines)) + "\r\n"


def _event_lines(record: EarningsRecord, generated_at: datetime) -> list[str]:
    start = record.announce_date
    end = start + timedelta(days=1)
    description = _build_description(record)

    lines = [
        "BEGIN:VEVENT",
        _line("UID", record.uid()),
        _line("DTSTAMP", _format_dt(generated_at)),
        _line("LAST-MODIFIED", _format_dt(record.fetched_at)),
        _line("SUMMARY", f"{record.company_name} 财报日"),
        _line("DTSTART;VALUE=DATE", _format_date(start)),
        _line("DTEND;VALUE=DATE", _format_date(end)),
        _line("STATUS", "CANCELLED" if record.cancelled else "CONFIRMED"),
        _line("SEQUENCE", "1" if record.cancelled else "0"),
        "TRANSP:TRANSPARENT",
        _line("DESCRIPTION", description),
    ]

    if record.source_url:
        lines.append(_line("URL", record.source_url))

    lines.append("END:VEVENT")
    return lines


def _build_description(record: EarningsRecord) -> str:
    lines = [
        f"公司: {record.company_name}",
        f"主代码: {record.primary_symbol}",
        f"代码别名: {', '.join(record.aliases)}",
        f"日期: {record.announce_date.isoformat()}",
        f"数据来源: {record.source}",
    ]
    if record.fiscal_period:
        lines.append(f"财报周期: {record.fiscal_period}")
    if record.source_url:
        lines.append(f"参考链接: {record.source_url}")
    if record.notes:
        lines.append(f"备注: {record.notes}")
    if record.stale:
        lines.append("说明: 本次沿用了上次成功抓取结果。")
    if record.cancelled:
        lines.append("状态: 已从 watchlist 移除，当前事件已取消。")
    return "\n".join(lines)


def _line(key: str, value: str) -> str:
    return f"{key}:{_escape(value)}"


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _format_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _fold_lines(lines: list[str]) -> list[str]:
    folded: list[str] = []
    for line in lines:
        if len(line) <= 73:
            folded.append(line)
            continue
        start = 0
        first = True
        while start < len(line):
            chunk = line[start : start + 73]
            if first:
                folded.append(chunk)
                first = False
            else:
                folded.append(f" {chunk}")
            start += 73
    return folded

