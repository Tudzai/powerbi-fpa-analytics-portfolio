# Cách tạo bảng và slicer đẹp, không bị lệch ô

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, đặc biệt các lần sửa sidebar, slicer, Current Lens, Signature, bảng chi tiết và QA đến bản v77.

Mục tiêu là tạo dashboard mà người xem không phải scroll để thấy slicer, logo, Current Lens hoặc KPI. Chart/table có thể có scroll nội bộ nếu dữ liệu dài, nhưng slicer/KPI/signature thì không.

## 1. Nguyên tắc sidebar

Sidebar trong Project 20 là vùng điều hướng + filter. Nó phải ổn định hơn các phần khác của dashboard.

Sidebar gồm:

- Signature/logo.
- Page navigation: Performance, Cash Plan, Risk Monitor.
- Global Lens: Year, Scenario.
- P&L Lens: Business Unit, Region.
- Current Lens.
- Data through.

Quy tắc:

- Các control phải cùng trục x.
- Width phải thống nhất.
- Label không bị cắt.
- Không để scrollbar trong logo, slicer, Current Lens.
- Không dùng visual header nếu nó tạo icon/filter/more menu làm lệch ô.

## 2. Signature/logo

Với logo, Project 20 đã thử nhiều cách. Bài học cuối:

- Nếu logo cần giống hệt asset, lấy `favicon.svg` làm source.
- Không tự vẽ lại nếu user muốn dùng đúng asset.
- Nếu render SVG bằng tableEx bị placeholder/scrollbar, cân nhắc native shape/text hoặc đảm bảo image visual đủ rộng/cao.
- TDAT nên là text riêng để dễ đọc, không ép chung vào logo quá nhỏ.

Checklist logo:

- Logo hiện đủ, không cần scroll ngang/dọc.
- Chữ `TDAT` đọc rõ.
- Không có hai thanh chữ nhật trắng/thừa cạnh logo.
- Không có tableEx visual header artifact.

## 3. Slicer layout không lệch ô

Slicer trong sidebar dùng dropdown, không dùng list khi sidebar hẹp.

Ví dụ pattern vị trí:

```python
slicer("DimDate", "Year", "Year", pos(30, 274, z + 52, 146, 42), mode="Dropdown")
slicer("DimScenario", "ScenarioName", "Scenario", pos(30, 368, z + 54, 146, 42), mode="Dropdown")
slicer("DimBusinessUnit", "BusinessUnit", "BU", pos(30, 460, z + 56, 146, 42), mode="Dropdown")
slicer("DimRegion", "Region", "Region", pos(30, 552, z + 58, 146, 42), mode="Dropdown")
```

Quy tắc:

- Cùng `x`.
- Cùng `width`.
- Height tối thiểu 38-44 px.
- Label phía trên dropdown, không chen trong visual.
- Tắt slicer header.
- Tắt visual header nếu không cần.
- Dùng z-index rõ để slicer không bị shape đè.

## 4. Căn giữa text trong slicer

Lỗi Project 20 từng gặp: `2026`, `Base Case`, `All` không nằm giữa khung.

Cách xử lý:

- Tăng height dropdown đủ lớn.
- Giảm font nếu text gần chạm mép.
- Dùng padding/outline ít.
- Đảm bảo shape nền không nhỏ hơn visual slicer.
- Không đặt slicer đè lên label hoặc separator.

Checklist:

- `2026` nằm giữa ô Year.
- `Base Case` nằm giữa ô Scenario.
- `All` nằm giữa Business Unit/Region.
- Dropdown arrow cùng hàng với text.
- Không có scrollbar trong slicer.

## 5. Current Lens

Current Lens trong Project 20 là SVG Image URL measure:

- Hiển thị năm + scenario.
- Hiển thị BU + region.
- Có indicator dot nhỏ.
- Fit trong ô sidebar.

Vấn đề từng gặp:

- Lens nhỏ quá, chữ bị sát mép.
- Nền ngoài shape bị tím nhạt khác sidebar.
- Có thanh/viền trắng do tableEx artifact.

Pattern cuối:

- SVG canvas khoảng `166x76`.
- tableEx image size khớp canvas.
- Visual frame đủ rộng/cao.
- Nền ngoài khớp sidebar `#250642`.
- Nếu user chỉnh layout thủ công, sync bằng tọa độ source-of-truth chứ không đoán lại.

Ví dụ nội dung:

```DAX
VAR Line1 = LEFT(YearText & " | " & ScenarioText, 25)
VAR Line2 = LEFT(BUText & " | " & RegionText, 28)
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='166' height='76' viewBox='0 0 166 76'>" &
    "<rect x='1' y='1' width='164' height='74' rx='7' fill='%233F1A63' stroke='%238E73E7'/>" &
    "<text x='10' y='18' font-family='Segoe UI' font-size='10' font-weight='700' fill='%23CFC3E6'>Current Lens</text>" &
    "<text x='10' y='40' font-family='Segoe UI' font-size='12' font-weight='700' fill='%23FFFFFF'>" & Line1 & "</text>" &
    "<text x='10' y='58' font-family='Segoe UI' font-size='9' fill='%23CFC3E6'>" & Line2 & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

## 6. Bảng/table trong dashboard

Project 20 có 3 bảng chính:

- `Board KPI Details`
- `3-Statement Summary`
- `Risk Register`

Bảng có thể scroll nếu số dòng nhiều, nhưng phải nhìn có chủ đích:

- Header rõ.
- Row banding nhẹ.
- Column width cố định.
- Numeric right aligned.
- Status/sparkline centered.
- Text left aligned.
- SVG sparkline/signal đủ width.

## 7. Table visual polish

Pattern `tableEx`:

```python
"grid": [{
    "properties": {
        "gridHorizontal": lit(True),
        "gridVertical": lit(False),
        "outlineColor": col(COLORS["table_grid"]),
        "rowPadding": lit(3),
        "imageHeight": lit(24 if has_image else 0),
        "imageWidth": lit(66 if has_image else 0)
    }
}]
```

Header:

```python
"columnHeaders": [{
    "properties": {
        "fontFamily": txt("Segoe UI Semibold"),
        "fontSize": lit(7.2),
        "fontColor": col(COLORS["ink"]),
        "backColor": col(COLORS["table_header"])
    }
}]
```

Rows:

```python
"values": [{
    "properties": {
        "fontFamily": txt("Segoe UI"),
        "fontSize": lit(7.05),
        "fontColor": col(COLORS["ink"]),
        "backColorPrimary": col(COLORS["table_row"]),
        "backColorSecondary": col(COLORS["table_alt"]),
        "urlIcon": lit(False)
    }
}]
```

## 8. Column width rules

Không để Power BI auto-size khi bảng có nhiều loại dữ liệu.

```python
def table_column_width(display: str, qref: str) -> float:
    label = display.lower()
    if "trend" in label or "signal" in label:
        return 64.0
    if "board ask" in label:
        return 94.0
    if label in {"risk"}:
        return 124.0
    if "line item" in label:
        return 104.0
    if "variance" in label:
        return 72.0
    if "actual" in label or "plan" in label or "exposure" in label:
        return 74.0
    return 84.0
```

Quy tắc:

- Text dài: 100-130 px.
- Số tiền/percent: 70-80 px.
- SVG sparkline/signal: 60-70 px.
- Status ngắn: 60-70 px.

## 9. Alignment rules

```python
def table_cell_alignment(display: str, qref: str) -> str:
    label = display.lower()
    if any(token in label for token in ["actual", "plan", "variance", "exposure"]):
        return "Right"
    if any(token in label for token in ["trend", "signal", "status", "severity"]):
        return "Center"
    return "Left"
```

Lý do:

- Số canh phải để so sánh nhanh.
- Icon/status/sparkline canh giữa.
- Text mô tả canh trái.

## 10. SVG trong table

Project 20 dùng SVG columns:

- `Board KPI Trend SVG`
- `Statement Trend SVG`
- `Risk Signal SVG`

Yêu cầu:

- Measure trả `data:image/svg+xml;utf8,...`.
- Measure có `dataCategory = ImageUrl`.
- `urlIcon = false`.
- `imageHeight` và `imageWidth` phải set.
- Column width đủ rộng.

Không vẽ sparkline table quá chi tiết, vì row thấp.

## 11. Sync layout giữa các tab

Project 20 v77 có bài học lớn: khi user đã chỉnh tab `Performance` bằng tay, tab đó là chuẩn.

Để sync sang `Cash Plan` và `Risk & Valuation`:

- Đọc `Report/Layout` trong PBIX.
- Tìm section theo `displayName`.
- Patch visual trong đúng section.
- Dùng query token như `Lens Summary SVG`, `Cash KPI Card SVG`, `Risk KPI Card SVG`.
- Không search global theo internal name vì internal name có thể trùng giữa các tab.
- Sau khi patch zip PBIX, xoá `SecurityBindings`.
- Mở lại Power BI Desktop để chắc file không corrupt.

Direct verification v77 pass:

- `lens_pass = true`
- `kpi_slots_pass = true`
- `top_chart_slots_pass = true`

## 12. QA chống lỗi scroll/lệch

Các lỗi user ghét nhất trong Project 20:

- Logo phải scroll mới thấy đủ.
- Slicer text không nằm giữa.
- Current Lens không fit.
- KPI card có scrollbar.
- KPI card có nền rectangle xấu sau value.
- Chart/table không fit shape.

Checklist QA:

- Logo TDAT hiện đủ, không scroll.
- Slicer Year/Scenario/BU/Region cùng trục và text nằm giữa.
- Current Lens fit trong ô.
- KPI card không có scrollbar.
- Table có thể scroll nếu dữ liệu dài, nhưng không được lệch column.
- Direct PBIX verification pass.
- Capture Power BI Desktop bằng Playwright/desktop screenshot.

Evidence v77:

- `qa/pbix_direct_verification_v77_tabs_synced.json`
- `output/playwright/project20_v77_tabs_synced_qa.png`
