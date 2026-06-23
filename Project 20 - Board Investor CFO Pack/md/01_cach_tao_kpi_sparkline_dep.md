# Cách tạo KPI card có sparkline đẹp

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, bản cuối `dashboard_final.pbix` và snapshot `dashboard_final_v77_tabs_synced.pbix`.

Mục tiêu là tạo KPI card nhìn giống một component dashboard thật, không phải một card Power BI mặc định: có số chính rõ, mini trend dễ đọc, marker đầu/cuối, band target, PY/YoY, và quan trọng nhất là không có scrollbar hoặc mảng chữ nhật thừa trong KPI card.

## 1. Nguyên tắc thiết kế KPI

Một KPI card tốt phải trả lời được 4 câu trong vài giây:

- Hiện tại chỉ số là bao nhiêu?
- So với PY hoặc kỳ trước thì tốt hơn hay xấu hơn?
- Xu hướng gần đây đi lên, đi ngang hay đi xuống?
- Chỉ số này đang thuộc trạng thái tốt, cảnh báo hay rủi ro?

Trong Project 20, KPI card không dùng Power BI card visual mặc định. Mỗi KPI là một DAX SVG measure, render bằng `tableEx` dưới dạng Image URL.

Các measure chính:

- `Revenue KPI Card SVG`
- `Margin KPI Card SVG`
- `EBITDA KPI Card SVG`
- `Cash KPI Card SVG`
- `Runway KPI Card SVG`
- `FCF KPI Card SVG`
- `Burn KPI Card SVG`
- `EV KPI Card SVG`
- `Equity KPI Card SVG`
- `Leverage KPI Card SVG`
- `Risk KPI Card SVG`

## 2. Cấu trúc card

Card trong Project 20 có 5 lớp:

- Shell: nền sáng, border tím nhạt, radius vừa phải.
- Accent line: thanh màu phía trên cho biết loại metric.
- Value block: label + số chính, font lớn nhất card.
- Sparkline block: mini trend bên phải, có band, marker đầu/cuối.
- Footer: PY và YoY ở dưới, dùng màu semantic.

Layout nội bộ nên đi theo tỷ lệ này:

- 55-60% bên trái cho label, value, PY/YoY.
- 35-40% bên phải cho sparkline.
- Top accent line chỉ cao 3-5 px.
- Footer không cao quá 30% card.

## 3. Vì sao dùng DAX SVG thay vì card mặc định

Power BI card visual dễ bị các lỗi sau:

- Text wrap xấu khi số dài.
- Không kiểm soát được sparkline nhỏ trong card.
- Visual header hoặc padding tạo khoảng trắng khó kiểm soát.
- Khi resize dễ xuất hiện scrollbar hoặc vùng nền lạ.

Với DAX SVG:

- Toàn bộ card là một ảnh vector nên layout ổn định.
- Có thể tự vẽ marker, target band, background bar, anomaly.
- Dễ copy pattern sang nhiều KPI khác.
- Dễ render đồng nhất ở nhiều tab.

Measure phải trả về:

```DAX
RETURN "data:image/svg+xml;utf8," & SVG
```

Và measure cần đặt `dataCategory = ImageUrl`.

## 4. Pattern DAX sparkline

Sparkline nên tôn trọng slicer, nhưng vẫn khóa vào latest complete month để số chính không nhảy sang tháng chưa đủ dữ liệu.

```DAX
VAR LatestMonth =
    CALCULATE(
        MAX(DimDate[MonthStart]),
        ALL(DimDate),
        DimDate[IsLatestCompleteMonth] = 1
    )

VAR MonthTable =
    ADDCOLUMNS(
        FILTER(
            ALLSELECTED(DimDate),
            DimDate[MonthStart] <= LatestMonth
        ),
        "__Value", [Revenue]
    )

VAR CleanTable =
    FILTER(MonthTable, NOT ISBLANK([__Value]))
```

Quy tắc:

- Dùng `ALLSELECTED(DimDate)` để sparkline phản ứng với slicer.
- Dùng `LatestMonth` để tránh tháng chưa hoàn chỉnh.
- Luôn filter blank để SVG không tạo path lỗi.

## 5. Tính tọa độ X/Y

SVG cần convert từng điểm dữ liệu thành tọa độ trong sparkline box.

```DAX
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])

VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue =
            RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue =
            142 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 86
        VAR YRatio =
            DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5)
        VAR YValue =
            78 - YRatio * 38
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
```

Quy tắc an toàn:

- `MAX(1, RowCount - 1)` để tránh chia cho 0.
- Nếu `MaxValue = MinValue`, dùng ratio `0.5` để line nằm giữa.
- Không cho sparkline quá cao; nó hỗ trợ value, không thay thế value.

## 6. Marker, target band và anomaly

Project 20 dùng 3 marker:

- Start marker: chấm nhỏ có stroke sáng.
- End marker: màu theo metric hoặc theo trend.
- Anomaly marker: đỏ/cam nếu điểm gần nhất hoặc điểm thấp nhất cần chú ý.

Ví dụ màu trend:

```DAX
VAR TrendColor =
    IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")

VAR BandColor =
    IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
```

Với metric lower-is-better như `Burn`, `Funding Need`, `Leverage`, đảo logic:

```DAX
VAR TrendColor =
    IF(LastValue <= FirstValue, "%231F8E45", "%23C94A4A")
```

Target band SVG:

```svg
<rect x='144' y='58' width='82' height='11' rx='5' fill='TARGET_BAND_COLOR'/>
<line x1='144' y1='64' x2='226' y2='64'
      stroke='%23B8AECF'
      stroke-width='1'
      stroke-dasharray='4 5'/>
```

Band nên rất nhẹ. Nếu band đậm hơn line chính, card sẽ rối.

## 7. Format số đúng theo metric

Project 20 từng bị lỗi ép nhầm unit. Quy tắc cuối:

- Money: `$36.7M`, `$376.7M`, `$14.3M`.
- Margin: `77.8%`, YoY dạng `+0.8pt`.
- Runway: `99.0x` hoặc `>99 mo`, không dùng `$M`.
- Leverage: `0.2x`, không dùng `$M`.
- Risk/Funding/Burn: dùng `$M` nếu là amount.

Ví dụ:

```DAX
VAR ValueText = FORMAT(DIVIDE(CurrentValue, 1000000), "$0.0M")
VAR PYText = FORMAT(DIVIDE(PriorValue, 1000000), "$0.0M")
VAR YoYText = FORMAT(ChangePct, "+0.0%;-0.0%;0.0%")
```

Với ratio:

```DAX
FORMAT(CurrentValue, "0.0x")
FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x")
```

## 8. Render bằng tableEx Image URL

KPI SVG render trong `tableEx` cần format như sau:

```json
{
  "grid": [{
    "properties": {
      "gridHorizontal": false,
      "gridVertical": false,
      "rowPadding": 0,
      "imageHeight": 158,
      "imageWidth": 249
    }
  }],
  "columnHeaders": [{
    "properties": { "show": false }
  }],
  "values": [{
    "properties": {
      "urlIcon": false,
      "imageHeight": 158,
      "imageWidth": 249
    }
  }]
}
```

Checklist chống scrollbar:

- SVG canvas phải nhỏ hơn hoặc bằng visual frame.
- `imageHeight` và `imageWidth` phải khớp kích thước card.
- `rowPadding = 0`.
- Tắt column header.
- Tắt visual header.
- Nếu thấy mảng chữ nhật nền sau value, kiểm tra fill/backColor của `values` và background SVG.

## 9. Kích thước thực tế ở Project 20 v77

Ở v77, user chỉnh tab `Performance` trước. Sau đó layout này được sync sang 2 tab sau.

KPI slots chuẩn:

| Slot | x | y | width | height |
|---|---:|---:|---:|---:|
| 1 | 204.0 | 49.4 | 266.2 | 172.2 |
| 2 | 471.3 | 49.4 | 300.5 | 177.0 |
| 3 | 738.0 | 49.4 | 266.2 | 172.2 |
| 4 | 1004.2 | 49.4 | 271.0 | 188.1 |

Mapping:

- Performance: Revenue, Margin, EBITDA, Cash.
- Cash Plan: Cash, Runway, FCF, Burn.
- Risk & Valuation: EV, Equity, Leverage, Risk.

Bài học quan trọng: nếu đã chỉnh layout thủ công trong Power BI Desktop, hãy dùng tab đó làm source-of-truth. Đừng rebuild lại toàn bộ model/layout nếu không cần.

## 10. Sync KPI row sang các tab khác

Khi copy layout trong PBIX:

- Đọc `Report/Layout`.
- Tìm đúng section theo `displayName`.
- Patch đúng visual theo query token như `Cash KPI Card SVG`, không chỉ theo internal name.
- Internal visual name có thể trùng giữa các tab, nên phải patch trong phạm vi section.
- Sau khi sửa zip PBIX, xoá `SecurityBindings` để Power BI Desktop mở file bình thường.

Không nên reserialize toàn bộ `Report/Layout` nếu không cần, vì Power BI có thể reject file.

## 11. QA bắt buộc

Project 20 không chấp nhận chỉ xem HTML preview. Quy trình QA:

- Direct read `Report/Layout` trong PBIX.
- Verify Lens/KPI slots pass bằng JSON.
- Mở `dashboard_final.pbix` trong Power BI Desktop.
- Capture từng tab bằng Power BI Desktop render.
- Tạo QA page và chụp bằng Playwright.

Evidence v77:

- `qa/pbix_direct_verification_v77_tabs_synced.json`
- `output/playwright/project20_v77_performance_full.jpg`
- `output/playwright/project20_v77_cash_plan_full.jpg`
- `output/playwright/project20_v77_risk_valuation_full.jpg`
- `output/playwright/project20_v77_tabs_synced_qa.png`

## 12. Checklist cuối cho KPI card

- Value là latest complete month.
- Số chính không bị nền rectangle xấu phía sau.
- Sparkline có start/end marker.
- Có target band/reference line nhẹ.
- PY và YoY đọc rõ.
- Màu YoY đúng higher-is-better hoặc lower-is-better.
- Card không có scrollbar ngang/dọc.
- Card không cần legend.
- Unit đúng từng metric.
- Kiểm tra trên PBIX thật bằng Power BI Desktop.
