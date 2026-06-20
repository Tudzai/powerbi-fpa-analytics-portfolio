# Cách Tạo Các KPI Có Sparkline Đẹp

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, đặc biệt phần KPI card có mini trend, PY/YoY footer, target band và marker.

## Mục Tiêu Thiết Kế

Một KPI card tốt không chỉ hiển thị số lớn. Nó cần trả lời nhanh 4 câu hỏi:

- Chỉ số hiện tại là bao nhiêu?
- So với kỳ trước hoặc PY ra sao?
- Xu hướng gần đây tăng hay giảm?
- Điểm bất thường hoặc điểm cuối nằm ở đâu?

Trong Project 20, KPI card được thiết kế theo dạng:

- Card nền sáng trên canvas tím đậm.
- Thanh accent màu ở cạnh trên để phân loại metric.
- Value lớn, màu theo metric.
- Sparkline nhỏ bên phải để đọc xu hướng.
- Footer gồm PY và YoY.
- YoY dùng màu semantic: xanh cho tốt, đỏ/cam cho xấu hoặc cần chú ý.

## Cấu Trúc KPI Card

Một KPI card nên tách thành 4 lớp:

1. Shell card: nền, border, shadow, bo góc.
2. Text layer: metric label và value.
3. Sparkline layer: mini trend bằng SVG hoặc visual nhỏ.
4. Footer layer: PY, YoY, delta, status.

Trong Project 20, các KPI được sinh bằng DAX SVG measures như:

- `Revenue KPI Card SVG`
- `Gross Margin KPI Card SVG`
- `EBITDA KPI Card SVG`
- `Cash KPI Card SVG`
- `Runway KPI Card SVG`
- `Leverage KPI Card SVG`

Các measure này có `dataCategory = ImageUrl`, sau đó render trong table/image visual để tránh Power BI card bị lỗi overlay.

## Pattern DAX Sparkline

Sparkline nên lấy dữ liệu theo tháng và tôn trọng slicer:

```DAX
VAR LatestMonth =
    CALCULATE(
        MAX(DimDate[MonthStart]),
        ALL(DimDate),
        DimDate[IsLatestCompleteMonth] = 1
    )
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Revenue]
    )
VAR CleanTable =
    FILTER(MonthTable, NOT ISBLANK([__Value]))
```

Điểm quan trọng:

- Dùng `ALLSELECTED(DimDate)` để sparkline phản ứng với slicer/report context.
- Dùng `LatestCompleteMonth` để KPI không nhảy sang tháng chưa đủ dữ liệu.
- Filter blank để SVG không bị lỗi path.

## Tính Tọa Độ Sparkline

SVG cần chuyển value thành tọa độ X/Y:

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
        VAR YValue =
            78 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 38
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
```

Best practices:

- Luôn dùng `MAX(1, RowCount - 1)` để tránh chia cho 0.
- Nếu `MaxValue = MinValue`, dùng default ratio `0.5` để line nằm giữa.
- Không để sparkline chiếm quá nhiều diện tích; trong Project 20 vùng mini trend chỉ nằm bên phải value.

## Marker Đầu, Cuối Và Anomaly

Project 20 dùng 3 loại marker:

- Start marker: vòng tròn trắng stroke xanh/tím.
- End marker: màu theo xu hướng.
- Anomaly marker: màu cam/đỏ tại điểm thấp hoặc điểm cần chú ý.

Ví dụ logic màu:

```DAX
VAR TrendColor =
    IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")

VAR BandColor =
    IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
```

Với metric lower-is-better như `Leverage`, `Funding Need`, `Net Burn`, đảo logic:

```DAX
VAR TrendColor =
    IF(LastValue <= FirstValue, "%231F8E45", "%23C94A4A")
```

## Target Band

Target band giúp người xem biết trend đang nằm trong vùng tốt hay xấu.

Trong SVG:

```SVG
<rect x='144' y='58' width='82' height='11' rx='5' fill='TARGET_BAND_COLOR'/>
<line x1='144' y1='64' x2='226' y2='64'
      stroke='%23B8AECF'
      stroke-width='1'
      stroke-dasharray='4 5'/>
```

Quy tắc:

- Band chỉ nên nhẹ, opacity thấp hoặc màu pastel.
- Target line nên dashed để không tranh với trend line.
- Không dùng quá nhiều màu trong một KPI card.

## Footer PY Và YoY

Footer nên luôn có:

- PY: prior-year hoặc previous period.
- YoY: delta hoặc delta percent.

Ví dụ format:

```DAX
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$0.0M")
VAR PYTextRaw = FORMAT(DIVIDE(PriorValue, 1000000), "$0.0M")
VAR YoYTextRaw = FORMAT(ChangePct, "+0.0%;-0.0%;0.0%")
```

Với ratio/multiple:

```DAX
FORMAT(CurrentValue, "0.0x")
FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x")
```

Lưu ý quan trọng từ Project 20:

- Revenue/Cash/EBITDA dùng `$M`.
- Runway/Leverage không được ép `$M`.
- Gross Margin dùng `%` hoặc `pt`.

## Layout Kích Thước

Trong Project 20, KPI strip dùng 4 card/page thay vì 5 card để giảm chật.

Gợi ý:

- Card width: khoảng 248 px.
- Card height: khoảng 140 px.
- Gap: 14-16 px.
- Value font: 20-28 px tùy card.
- Sparkline box: khoảng 90 x 44 px.

Không nên:

- Nhồi quá nhiều label trong card.
- Dùng card visual mặc định nếu nó tạo overlay hoặc text wrap xấu.
- Dùng sparkline quá to làm mất trọng tâm value.

## Checklist KPI Card

- Value là latest complete month, không phải tổng full-period.
- Sparkline phản ứng với slicer.
- Có marker đầu/cuối.
- Có target band hoặc reference line nhẹ.
- Có PY và YoY.
- Màu YoY đúng logic higher-is-better/lower-is-better.
- Không có chữ bị cắt, không có scrollbar trong textbox.
- Card không cần legend.
- Format unit đúng metric.

## Files Liên Quan Trong Project 20

- `build/scripts/01_build_project20.py`
- `model/MEASURES.dax`
- `model/measure_map.json`
- `qa/pbix_direct_verification_v58.json`
