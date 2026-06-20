# Cách Tạo Các Bảng Và Slicer Đẹp, Không Bị Lệch Ô

Tài liệu này rút từ Project 20 - Board Investor CFO Pack, nhất là giai đoạn v58 đã pass table/slicer verification trong PBIX thật.

## Nguyên Tắc Chung

Bảng và slicer trong dashboard tài chính phải ưu tiên scan nhanh:

- Cột quan trọng đọc rõ.
- Cột số canh phải.
- Cột text canh trái.
- Header nổi nhẹ nhưng không quá nặng.
- Row banding giúp mắt đi theo hàng.
- Slicer nằm đúng khung, không lệch, không tràn chữ.

Trong Project 20, các bảng chính được polish:

- `Board KPI Details`
- `3-Statement Summary`
- `Risk Register`

Các slicer chính nằm trong left rail:

- Year
- Scenario
- BU
- Region

## Bố Cục Slicer Không Bị Lệch

Trong Project 20, slicer được đặt trong sidebar có tọa độ cố định:

```python
slicer("DimDate", "Year", "Year", pos(30, 274, z + 52, 146, 42), mode="Dropdown")
slicer("DimScenario", "ScenarioName", "Scenario", pos(30, 368, z + 54, 146, 42), mode="Dropdown")
slicer("DimBusinessUnit", "BusinessUnit", "BU", pos(30, 460, z + 56, 146, 42), mode="Dropdown")
slicer("DimRegion", "Region", "Region", pos(30, 552, z + 58, 146, 42), mode="Dropdown")
```

Quy tắc:

- Slicer width cố định, cùng x position.
- Label nằm phía trên slicer, không nằm trong cùng visual nếu dễ cắt chữ.
- Height dropdown nên đủ cao: khoảng 38-44 px.
- Không dùng Basic list khi sidebar quá hẹp, vì list dễ lệch ô và tạo visual header/scrollbar rối.
- Dùng cùng `z` pattern để tránh slicer bị che bởi shape/sidebar.

## Slicer Formatting

Pattern trong script:

```python
objects = {
    "data": [{"properties": {"mode": txt(mode)}}],
    "selection": [{
        "properties": {
            "selectAllCheckboxEnabled": lit(show_select_all),
            "singleSelect": lit(False)
        }
    }],
    "header": [{"properties": {"show": lit(False)}}],
    "items": [{
        "properties": {
            "fontFamily": txt("Segoe UI"),
            "fontSize": lit(item_size),
            "fontColor": col(COLORS["ink"])
        }
    }],
}
```

Best practices:

- Hide slicer header để tránh icon/filter/more menu làm rối.
- Dùng font size 7.4-8.3 tùy sidebar.
- Dùng `selectAllCheckboxEnabled` cho dropdown, tắt cho Basic list nếu cần.
- Dùng fill nhất quán (`COLORS["pale"]`) để slicer giống một control có chủ đích.

## Table Visual Polish

Project 20 dùng `tableEx` với format rõ:

```python
"grid": [{
    "properties": {
        "gridHorizontal": lit(True),
        "gridVertical": lit(False),
        "outlineColor": col(COLORS["table_grid"]),
        "rowPadding": lit(3),
        "imageHeight": lit(24 if has_image else 0),
        "imageWidth": lit(66 if has_image else 0),
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
        "backColor": col(COLORS["table_header"]),
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
        "urlIcon": lit(False),
        "imageHeight": lit(24 if has_image else 0),
        "imageWidth": lit(66 if has_image else 0),
    }
}]
```

## Column Width Rules

Không để Power BI tự đo cột nếu bảng có nhiều loại dữ liệu. Project 20 dùng function riêng:

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

## Alignment Rules

Project 20 dùng alignment theo loại cột:

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

- Số phải canh phải để so sánh nhanh.
- Icon/status/sparkline canh giữa.
- Text mô tả canh trái.

## SVG Column Trong Table

Project 20 thêm các cột SVG:

- `Board KPI Trend SVG`
- `Statement Trend SVG`
- `Risk Signal SVG`

Pattern:

```python
measures=[
    ("Board KPI Trend SVG", "Trend")
]
```

Trong model, measure phải có:

```python
{"dataType": "string", "dataCategory": "ImageUrl"}
```

Checklist cho SVG table:

- Measure trả về `data:image/svg+xml;utf8,...`
- Column width đủ rộng.
- `imageHeight` và `imageWidth` được set.
- `urlIcon` = false để render image thay vì icon link.
- SVG không quá nhiều chi tiết vì table row thấp.

## Tránh Lệch Ô Trong Table

Các lỗi thường gặp:

- Không set width cho toàn bộ cột.
- Text cột quá dài làm auto-resize.
- Image column không set `imageHeight/imageWidth`.
- Header font lớn hơn row quá nhiều.
- Row padding quá cao làm table bị cắt dưới panel.

Trong Project 20, direct verification kiểm:

- 3 bảng mục tiêu đều có SVG column.
- `columnWidth` count bằng số column.
- `columnFormatting` count bằng số column.
- Header fill được set.
- Banded rows được set.

## Checklist Table/Slicer

- Slicer cùng x, cùng width, cùng mode.
- Slicer header hidden.
- Slicer label không bị cắt.
- Table có column width cho mọi cột.
- Numeric columns canh phải.
- SVG/status columns canh giữa.
- Header fill nhẹ.
- Row banding nhẹ.
- Row padding đủ nhưng không làm table tràn.
- Direct verification trong PBIX pass, không chỉ nhìn HTML preview.

## Files Liên Quan Trong Project 20

- `build/scripts/01_build_project20.py`
- `build/native_report_layout_project20.json`
- `qa/pbix_direct_verification_v58.json`
- `output/playwright/project20_v58_desktop_crops.png`
