# Visual QA Notes

Status: pending PBIX build. Static HTML preview was generated but not browser-verified because the in-app browser blocks direct `file://` navigation.

## Design Rules

- Use orange as the primary accent, not as every chart color.
- Use teal for favorable variance and red for unfavorable variance.
- Keep KPI cards on the same baseline and height.
- Use horizontal bars for rankings with long names.
- Keep matrix detail lower on each page so the first 30 seconds stay summary-led.
- Do not use 3D charts.
- Avoid pie/donut charts unless category count is four or fewer.

## Page-Level Risks To Check In Power BI

- Commentary text may need card height adjustment.
- Customer scatter can become crowded if all customers and all products are selected.
- Waterfall total/subtotal formatting must be checked after building.
- Slicer labels should not duplicate field names.
