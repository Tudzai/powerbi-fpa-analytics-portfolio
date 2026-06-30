# Design Research

Chosen seed: `Template/04_Profitability_Margin/Microsoft_Customer_Profitability.pbix`.

Why:
- Microsoft's Customer Profitability sample is CFO-oriented and focuses on customers, products, gross margin, and the factors affecting profitability: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability
- Microsoft's sample catalog lists Customer Profitability as a `.pbix`/`.xlsx` sample for revenue, costs, customer segments, high/low-profit customers, and lifetime value: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets
- Local template catalog rates `Microsoft_Customer_Profitability.pbix` as a strong profitability/margin starting point and `Packt_Ch10_PVM.pbix` as a strong bridge-analysis reference.

Layout selected for Project 17:
- Tab 1: Executive Trade Lane Cockpit.
- Tab 2: Trade Lane Margin diagnostics.
- Tab 3: Cost Drivers and Action Queue.
- Slicers sit in a top filter row above the KPI strip on every page so filters are visible before the reader scans KPIs.
- Current Lens and Decision panels use native card/text layers, so they respond to slicer context without raw SVG tooltip leakage.
- KPI cards use intentional TableEx + SVG Image URL visuals layered over chart-style wrapper panels, so the visible border/shadow matches chart cards while the TableEx container remains chrome-free.

Design system:
- Off-white canvas, white panels, compact KPI strip, blue/teal/green for revenue and profit, amber/red for warnings and margin leakage.
- Dense but readable FP&A control-tower layout; no marketing hero or decorative cards.
