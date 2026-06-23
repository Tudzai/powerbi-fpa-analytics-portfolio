# Cách vẽ chart đẹp

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, gồm cách chọn chart, format panel, xử lý units, sort, layout giữa các tab và QA bằng PBIX thật.

Mục tiêu là chart giúp người xem ra quyết định, không chỉ trang trí.

## 1. Vai trò chart trong dashboard

Project 20 dùng dashboard theo 3 tầng:

- KPI row: đọc nhanh trong 3-10 giây.
- Chart panels: phân tích driver, trend, mix, variance.
- Tables: audit chi tiết và drill sâu.

Chart nên trả lời nhanh:

- Metric đang đi lên hay đi xuống?
- Nhóm nào đóng góp nhiều nhất?
- Chênh lệch so với plan nằm ở đâu?
- Có rủi ro/outlier nào cần chú ý?

## 2. Page structure trong Project 20

Project 20 có 3 tab:

- `Performance`
- `Cash Plan`
- `Risk & Valuation`

Mỗi tab có cùng logic bố cục:

- Sidebar bên trái.
- Header/title.
- KPI card row phía trên.
- 3 chart panels hàng trên.
- 3 panels hàng dưới, gồm chart/table tùy page.

Ở v77, layout tab `Performance` user chỉnh tay được dùng làm source-of-truth để sync `Cash Plan` và `Risk & Valuation`.

Top chart slots chuẩn v77:

| Slot | x | y | width | height |
|---|---:|---:|---:|---:|
| 1 | 205.6 | 215.2 | 425.6 | 210.4 |
| 2 | 640.8 | 216.8 | 304.5 | 210.4 |
| 3 | 966.0 | 218.4 | 293.3 | 210.4 |

## 3. Chart panel style

Chart panel dùng nền sáng trên canvas tím đậm.

```python
def frame(fill=None):
    fill = fill or COLORS["panel"]
    return {
        "background": [{
            "properties": {
                "show": lit(True),
                "color": col(fill),
                "transparency": lit(0.0)
            }
        }],
        "border": [{
            "properties": {
                "show": lit(True),
                "color": col(COLORS["border"]),
                "radius": lit(6.0),
                "width": lit(0.75)
            }
        }],
        "dropShadow": [{
            "properties": {
                "show": lit(True),
                "position": txt("Outer"),
                "color": col("#180827"),
                "transparency": lit(82.0),
                "angle": lit(45.0),
                "distance": lit(2.0)
            }
        }]
    }
```

Quy tắc:

- Border mảnh.
- Radius vừa phải.
- Shadow nhẹ.
- Không dùng panel trắng quá gắt trên nền tím.
- Không nhồi quá nhiều chart trong một panel.

## 4. Title và subtitle

Project 20 dùng subtitle ngắn kiểu:

- `Drilldown: Month > KPI`
- `Drilldown: Region`
- `Drilldown: Business Unit`
- `Drilldown: BU > Variance`

Quy tắc:

- Title nói metric/chủ đề.
- Subtitle nói grain/drill path.
- Không viết hướng dẫn dài trong dashboard.
- Không dùng title chung chung như `Chart 1`.

## 5. Chart objects pattern

```python
def chart_objects(fill, labels=True, display_units=1000000.0):
    return {
        "valueAxis": [{
            "properties": {
                "showAxisTitle": lit(False),
                "gridlineShow": lit(False),
                "labelDisplayUnits": lit(display_units),
                "fontSize": lit(7.0),
                "color": col(COLORS["muted"])
            }
        }],
        "categoryAxis": [{
            "properties": {
                "showAxisTitle": lit(False),
                "gridlineShow": lit(False),
                "concatenateLabels": lit(False),
                "fontSize": lit(7.0),
                "color": col(COLORS["ink"])
            }
        }],
        "labels": [{
            "properties": {
                "show": lit(labels),
                "fontSize": lit(7.0),
                "labelDisplayUnits": lit(display_units),
                "color": col(COLORS["ink"])
            }
        }],
        "legend": [{
            "properties": {
                "showTitle": lit(False),
                "position": txt("Top"),
                "fontSize": lit(7.0),
                "labelColor": col(COLORS["muted"])
            }
        }],
        "dataPoint": [{
            "properties": {
                "fill": col(fill)
            }
        }]
    }
```

Chart nhỏ nên ít noise:

- Tắt axis title nếu title/subtitle đã đủ.
- Tắt gridline nếu chart không cần đọc chính xác từng mức.
- Legend top, font nhỏ.
- Data labels chỉ bật khi ít category.

## 6. Units đúng theo metric

Một lỗi xấu là ép mọi chart về `$M`.

Project 20 dùng logic:

```python
def chart_display_units(measures: list[str]) -> float:
    formats = [mfmt(measure) or "" for measure in measures]
    return 1000000.0 if formats and all("$" in fmt for fmt in formats) else 0.0
```

Kết quả:

- Revenue/Cash/EBITDA/Funding Need: compact `$M`.
- Runway: giữ `x` hoặc month logic, không `$M`.
- Leverage: giữ `x`.
- Gross Margin: giữ `%` hoặc `pt`.

Checklist:

- Money chart dùng `$M`.
- Ratio/multiple không dùng display unit money.
- Multi-measure chart chỉ dùng `$M` nếu tất cả measures là money.

## 7. Sort chart

Trend chart sort theo thời gian:

```python
order = {
    "Direction": 1,
    "Expression": {
        "Column": {
            "Expression": src("c"),
            "Property": "MonthIndex"
        }
    }
}
```

Ranking chart sort theo measure descending:

```python
order = {
    "Direction": 2,
    "Expression": {
        "Measure": {
            "Expression": src("m"),
            "Property": measure
        }
    }
}
```

Quy tắc:

- Trend: thời gian tăng dần.
- Ranking: metric giảm dần.
- Scenario: nếu có business order thì dùng thứ tự business, không alphabetic.
- Variance: có thể sort theo absolute impact nếu muốn làm rõ driver.

## 8. Khi dùng donut

Donut chỉ dùng khi:

- 3-5 nhóm.
- Mục tiêu là đọc mix/share.
- Không cần so sánh ranking quá chính xác.

Trong Project 20:

- `Revenue Mix by Region` dùng donut vì có 4 region.

Nếu category nhiều hơn 5, dùng bar chart.

## 9. Khi dùng bar chart

Bar chart dùng cho:

- Revenue by Business Unit.
- Funding Need by Scenario.
- Runway by Scenario.
- Risk Exposure by Severity.
- Risk Exposure by Owner.
- Sensitivity Impact.

Quy tắc:

- Horizontal bar cho label dài.
- Data label bật khi số category ít.
- Sort theo metric.
- Một chart ranking thường chỉ cần một màu chính, không cần quá nhiều màu.

## 10. Khi dùng multi-series trend

Dùng multi-series khi cần so sánh:

- Actual vs Plan vs Forecast.
- Cash Balance vs Funding Need.
- Covenant/headroom trend.
- Valuation range.

Lưu ý:

- 2-4 series là vừa.
- Nếu khác unit, tách chart hoặc dùng combo cẩn thận.
- Legend nhỏ nhưng rõ.
- Không dùng quá nhiều màu bão hòa.

## 11. Màu semantic

Project 20 dùng màu có ý nghĩa:

```python
blue   = "#4F87F5"  # revenue/primary
teal   = "#0F9F95"  # margin/cash-flow/efficiency
green  = "#1F8E45"  # favorable/headroom/profit
amber  = "#BE7C10"  # watch/cash/leverage
red    = "#B73535"  # burn/funding/risk
violet = "#6C2DBE"  # portfolio/business unit
```

Quy tắc:

- Cùng metric dùng cùng màu qua nhiều tab.
- Không random màu theo chart.
- Đỏ chỉ dùng cho rủi ro/cảnh báo hoặc metric xấu.
- Lower-is-better phải đảo logic màu.

## 12. Chart list trong Project 20

Performance:

- Revenue vs Plan + EBITDA Trend.
- Revenue Mix by Region.
- Revenue by Business Unit.
- Revenue vs Plan by BU.
- EBITDA by BU.
- Board KPI Details.

Cash Plan:

- Cash Balance + Funding Need Trend.
- Funding Need by Scenario.
- Runway by Scenario.
- 3-Statement Summary.
- Opex by Cost Category.
- Free Cash Flow by Scenario.

Risk & Valuation:

- Valuation Range by Method.
- Risk Exposure by Severity.
- Covenant Headroom Trend.
- Risk Register.
- Sensitivity Impact.
- Risk Exposure by Owner.

## 13. Sync chart layout giữa tab

Ở v77, `Performance` là layout chuẩn. `Cash Plan` và `Risk & Valuation` được sync top chart row theo slot của `Performance`.

Bài học kỹ thuật:

- Patch đúng section theo `displayName`.
- Patch chart visual trong đúng page.
- Không search internal visual name global.
- Sau khi edit PBIX zip, xoá `SecurityBindings`.
- Mở PBIX trong Power BI Desktop để xác nhận file không corrupt.

Direct verification v77:

- `top_chart_slots_pass = true` cho `Cash Plan`.
- `top_chart_slots_pass = true` cho `Risk & Valuation`.

## 14. QA chart trong PBIX thật

Project 20 dùng 2 lớp QA:

1. Direct PBIX verification:
   - đọc `Report/Layout`.
   - verify Lens/KPI/chart slots.
   - verify title, units, visual types.

2. Visual QA:
   - mở `dashboard_final.pbix` bằng Power BI Desktop.
   - capture `Performance`, `Cash Plan`, `Risk & Valuation`.
   - tạo QA HTML.
   - dùng Playwright screenshot full page.

Evidence:

- `qa/pbix_direct_verification_v77_tabs_synced.json`
- `output/playwright/project20_v77_performance_full.jpg`
- `output/playwright/project20_v77_cash_plan_full.jpg`
- `output/playwright/project20_v77_risk_valuation_full.jpg`
- `output/playwright/project20_v77_tabs_synced_qa.png`

## 15. Checklist cuối cho chart

- Chart đúng loại dữ liệu.
- Title rõ, subtitle nói drill grain.
- Sort đúng business logic.
- Unit đúng từng metric.
- Axis không thừa.
- Gridline không gây noise.
- Label không đè.
- Màu nhất quán qua các tab.
- Chart panel không lệch shape.
- Top chart row được sync giữa các tab.
- QA bằng PBIX thật, không chỉ HTML preview.
