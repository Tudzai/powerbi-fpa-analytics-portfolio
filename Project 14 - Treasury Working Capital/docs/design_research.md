# Design Research

Research sources used:
- Microsoft Power BI design guidance: keep the most important information prominent, clean, uncluttered, and ordered top-left to lower-detail flow. Source: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Atlar 13-week cash flow guidance: 13-week forecasts are short-term, weekly, direct-method views of cash receipts and payments for liquidity management. Source: https://www.atlar.com/learn/what-is-the-13-week-cash-flow-forecast
- Embat treasury dashboard metrics: CFO treasury dashboard should include consolidated cash, 13-week forecast, liquidity headroom, DSO, DPO, overdue AR, payment status, FX exposure, unhedged FX, and debt maturity. Source: https://www.embat.io/blog/treasury-dashboard-metrics-cfo
- Qlik finance dashboard examples: financial dashboards should combine high-level KPIs with drillable breakdowns and action-oriented detail. Source: https://www.qlik.com/us/dashboard-examples/financial-dashboards

Template choice:
- Technical seed: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\01_Core_Financial_Statements\Packt_Ch07_Group_Reporting.pbix`
- Domain reference: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\02_AR_Working_Capital\Prodata_Finance-AR_Receivables.pbix`
- Rationale: the AR Working Capital template is the best semantic inspiration, while the Group Reporting PBIX is the safer technical seed because it contains the native `/Report/Layout` part required by the report patch route, avoids stale web-query credential prompts, and supports TOM model replacement. The semantic model, measures, 3 report tabs, visual field bindings, theme, and screenshots are created for treasury working capital.

Layout decision:
1. Treasury Command Center: status-first liquidity cockpit for CFO/Treasurer.
2. Working Capital Control: diagnostic AR/AP and DSO/DPO execution view.
3. Forecast, FX & Risk: near-term forecast plus treasury risk queue.

Palette:
- Neutral finance base with teal, blue, green, gold, and rose accents. The palette avoids a one-note blue/purple dashboard while keeping treasury risk states readable.
