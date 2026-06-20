# Interaction QA Notes

v24 interaction polish:

- Global slicers are positioned in the left sidebar under the Board Lens group.
- Year, Scenario, Business Unit, and Region use compact dropdown controls to reduce scan noise.
- Page-level decision chips summarize the current board focus before users drill into charts.
- Hero KPI values are measure-bound native card layers with latest-complete-month numeric KPI measures, so they respond to slicers without showing full-period totals by default.
- KPI micro-trends show a compact target band, target line, start marker, anomaly marker, and end marker without crowding the value.
- Chart subtitles use compact Lens labels so users can scan the diagnostic grain without reading long instructions.
- Native visuals use Power BI cross-filter behavior within each page.
- Lower-is-better KPI deltas use green when they improve, including Net Burn, Funding Need, Leverage, and Risk Exposure.
- Playwright preview QA checks Performance, Cash Plan, and Risk & Valuation KPI overflow and individual card crops before handoff; Desktop capture validates the final PBIX visual layer renders.
