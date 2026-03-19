# Earnings Calendar

一个面向个人 watchlist 的财报订阅项目。

目标：
- 只生成财报日历，不混入价格提醒或新闻
- 按公司建模，避免 `BABA` / `9988.HK` 这类重复事件
- 支持手工覆盖，避免被单一数据源卡死
- 生成稳定 `UID` 的 `ics` 文件，便于长期订阅
- 支持移除股票后发布取消事件，减少客户端残留

## 目录

```text
.
├── .github/workflows/update.yml
├── config/watchlist.json
├── config/manual_overrides.json
├── data/state.json
├── data/resolved_events.json
├── docs/earnings.ics
├── docs/index.html
├── generate_calendar.py
├── src/earnings_calendar/
└── tests/
```

## 配置

### `config/watchlist.json`

按公司维护，不按 ticker 堆列表。

字段：
- `id`: 稳定公司 ID，用于生成 `UID`
- `name`: 日历里展示的公司名
- `primary_symbol`: 默认抓取用代码
- `aliases`: 同一家公司对应的其他代码
- `provider`: 当前默认是 `yahoo`
- `official_url`: 公司 IR 或结果公告主页
- `enabled`: 关闭后会进入取消流程

### `config/manual_overrides.json`

当自动数据缺失或不准时，手工写这里，优先级高于自动抓取。

示例：

```json
{
  "companies": {
    "tencent": {
      "announce_date": "2026-05-13",
      "fiscal_period": "FY2026 Q1",
      "source_url": "https://www.tencent.com/en-us/investors.html",
      "notes": "Official filing"
    }
  }
}
```

## 运行

本地生成：

```bash
python3 generate_calendar.py
```

输出：
- `docs/earnings.ics`
- `data/resolved_events.json`
- `data/state.json`

## 数据优先级

1. `manual_overrides.json`
2. 自动抓取提供方
3. 上一次成功结果回填

这意味着：
- 某家公司短时抓取失败，不会立刻从日历里消失
- 从 watchlist 移除后，会继续发布一段时间 `STATUS:CANCELLED` 事件

## GitHub Actions / Pages

这个仓库设计为直接配合 GitHub Actions 和 GitHub Pages 使用。

工作流会：
- 每天两次生成 `docs/earnings.ics`
- 提交更新后的 `ics` 和状态文件

`docs/index.html` 会提供一个可点击的订阅入口。
