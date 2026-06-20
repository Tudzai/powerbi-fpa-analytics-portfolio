# Cách Vẽ Chart Đẹp

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, tập trung vào chart panel, chart units, sort, màu sắc và khả năng scan trong dashboard Power BI.

## Mục Tiêu Chart Trong Dashboard

Chart trong dashboard không phải để trang trí. Chart cần trả lời nhanh:

- Metric đang tăng/giảm?
- Nhóm nào đóng góp nhiều nhất?
- Chênh lệch so với plan nằm ở đâu?
- Có rủi ro hay outlier nào cần chú ý?

Project 20 dùng chart theo 3 tầng:

- KPI strip trên cùng: 3-30 second scan.
- Chart panels ở giữa: phân tích trend/mix/driver.
- Tables ở dưới: chi tiết và audit.

## Chart Panel Layout

Trong Project 20, chart panel dùng card/panel sáng trên nền tím đậm:

```python
def frame(title=None, sub=None, fill=None):
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

Best practices:

- Border mảnh, radius vừa phải.
- Shadow nhẹ để tách panel khỏi nền.
- Không để chart panel quá trắng nếu canvas quá đậm; dùng pale lavender như `#F0EAF7`.
- Title ngắn, subtitle nói drill grain.

## Subtitle Cho Chart

Project 20 dùng subtitle kiểu:

- `Drilldown: Month > KPI`
- `Drilldown: Region`
- `Drilldown: Business Unit`
- `Drilldown: BU > Variance`

Quy tắc:

- Subtitle không phải mô tả dài.
- Subtitle cho biết người dùng có thể drill theo gì.
- Tránh câu hướng dẫn dài trong dashboard.

## Chart Units Đúng Theo Metric

Một lỗi rất xấu là ép mọi chart về `$M`. Project 20 đã sửa logic chart units:

```python
def chart_display_units(measures: list[str]) -> float:
    formats = [mfmt(measure) or "" for measure in measures]
    return 1000000.0 if formats and all("$" in fmt for fmt in formats) else 0.0
```

Kết quả:

- Revenue, Cash, EBITDA, Funding Need: compact theo `$M`.
- Runway Months: không bị ép millions.
- Leverage Ratio: không bị ép millions.
- Gross Margin/Covenant ratios: giữ unit tự nhiên.

Checklist:

- Nếu format measure có `$`, dùng display unit 1,000,000.
- Nếu format là `0.0x`, `%`, `pt`, count, không dùng display unit `$M`.
- Multi-measure chart chỉ dùng `$M` nếu tất cả measures là money.

## Chart Objects Pattern

Project 20 tạo object chart bằng function:

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
        }],
    }
```

Best practices:

- Tắt axis title nếu title/subtitle đã đủ rõ.
- Tắt gridline với chart nhỏ để giảm noise.
- Data labels chỉ bật khi ít categories và label không đè nhau.
- Legend đặt top, font nhỏ.
- `concatenateLabels = false` để label category dễ đọc hơn.

## Sort Chart

Chart ranking nên sort theo measure descending:

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

Chart trend nên sort theo month index ascending:

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

Quy tắc:

- Trend chart: sort theo thời gian tăng dần.
- Bar chart ranking: sort theo metric giảm dần.
- Scenario chart: dùng sort order nếu scenario có thứ tự business.
- Không để Power BI sort alphabetic nếu chart thể hiện performance.

## Chart Type Trong Project 20

Performance page:

- Revenue vs Plan + EBITDA Trend: multi-series bar chart theo month.
- Revenue Mix by Region: donut chart.
- Revenue by Business Unit: horizontal bar chart.
- Revenue vs Plan by BU: variance bar chart.
- EBITDA by BU: bar chart.

Cash Plan page:

- Cash Balance + Funding Need Trend.
- Funding Need by Scenario.
- Runway by Scenario.
- Opex by Cost Category.
- Free Cash Flow by Scenario.

Risk & Valuation page:

- Valuation Range by Method.
- Risk Exposure by Severity.
- Covenant Headroom Trend.
- Sensitivity Impact.
- Risk Exposure by Owner.

## Màu Sắc

Project 20 dùng semantic colors:

```python
"blue": "#4F87F5"
"teal": "#0F9F95"
"green": "#1F8E45"
"amber": "#BE7C10"
"red": "#B73535"
"violet": "#6C2DBE"
```

Quy tắc:

- Blue: revenue/primary metric.
- Teal: margin/cash-flow/efficiency.
- Green: favorable/profit/headroom.
- Amber: watch/cash/leverage.
- Red: burn/funding/risk.
- Violet: portfolio/business-unit accent.

Không nên:

- Mỗi chart một màu ngẫu nhiên.
- Dùng quá nhiều màu trong bar chart ranking.
- Dùng đỏ cho mọi variance âm nếu metric lower-is-better.

## Khi Nào Dùng Donut

Donut chỉ nên dùng khi:

- Category ít, khoảng 3-5 nhóm.
- Muốn đọc mix/share.
- Không cần so sánh ranking quá chính xác.

Trong Project 20, `Revenue Mix by Region` hợp với donut vì chỉ có 4 region.

Nếu có nhiều hơn 5 categories, dùng bar chart.

## Khi Nào Dùng Bar Chart

Dùng bar chart cho:

- Ranking business unit.
- Variance by BU.
- Risk exposure by owner/severity.
- Scenario comparison.

Gợi ý:

- Horizontal bar cho category label dài.
- Data label bật nếu số category ít.
- Axis title tắt nếu title đã rõ.
- Sort descending theo measure.

## Khi Nào Dùng Multi-Series Trend

Dùng multi-series trend khi cần so sánh:

- Actual vs Plan vs Forecast.
- Cash vs Funding Need.
- Leverage vs Limit.
- Low/Base/High valuation range.

Lưu ý:

- Multi-series chart dễ rối; giới hạn 2-4 series.
- Nếu series khác unit, tách chart hoặc dùng combo cẩn thận.
- Legend phải rõ nhưng nhỏ.

## QA Chart Trong PBIX Thật

Project 20 không chỉ nhìn HTML preview. Verification đọc trực tiếp `Report/Layout` trong PBIX:

- Chart title/subtitle tồn tại.
- Chart units đúng theo measure format.
- Chart/table visual count đúng.
- Target tables có SVG columns.
- Power BI Desktop render được và Playwright crop từ Desktop screenshot.

Checklist chart:

- Chart đúng loại dữ liệu.
- Sort đúng business logic.
- Unit không sai.
- Title ngắn.
- Subtitle cho drill grain.
- Axis không thừa.
- Label không đè.
- Màu nhất quán.
- Cross-filter enabled nếu cần interactive.
- Verify trong PBIX thật, không chỉ preview.

## Files Liên Quan Trong Project 20

- `build/scripts/01_build_project20.py`
- `build/native_report_layout_project20.json`
- `qa/pbix_direct_verification_v58.json`
- `output/playwright/project20_v58_desktop_crops.png`
