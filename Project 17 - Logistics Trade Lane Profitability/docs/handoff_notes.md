# Handoff Notes

- Final PBIX path: `output/dashboard_final.pbix`.
- Build route: SCRIPTED_DESKTOP_PBIX using profitability seed, Project 17 TOM model push, native layout patch, Desktop open/save/reopen QA.
- Supplemental preview: `output/dashboard_final.html`.
- Data source: synthetic logistics profitability data, seed `17042`, latest complete period `2026-05`.
- Pages: Executive Overview; Trade Lane Margin; Cost Drivers & Action Queue.
- Key KPIs: Net Revenue, Gross Profit, GP Margin %, Shipments, Cost/Shipment, Reprice Opportunity, Margin Gap, Open Actions, Action Risk Value.
- QA status: pass. Data QA passed; TOM model push created 10 tables, 13 relationships, and 25 measures; native layout patch created 3 pages and 56 visual containers; final PBIX opened from the exact Project 17 path in Power BI Desktop and saved with visual error count 0.
- Repair note: first open-check exposed a report-render modal because layout was generated before the seed PBIX existed. Regenerating the layout from the saved seed restored the required top-level report metadata, and the final open-check passed.
