# Project 06 - Marketing Campaign ROI

Prompt version: BI A-Z Master Prompt v2.

## Status

- Complete dashboard: `output/dashboard_final.html`
- Final Power BI-style artifact: `output/dashboard_final.html`
- Current status: complete interactive HTML dashboard delivered; native PBIX is not published in the GitHub portfolio until it passes a clean rebuild and QA cycle
- Authoring mode: `COMPUTER_USE_ATTEMPTED`
- Computer Use requested: `True`
- Computer Use callable UI tool exposed: `True`
- SCRIPTED_DESKTOP_PBIX feasible: `False`
- Native PBIX note: the GitHub portfolio publishes the accepted HTML dashboard for this project; a native PBIX should be rebuilt from a clean Power BI Desktop session before being promoted.
- Synthetic data seed: `6262026`
- Visual template applied: `Executive ROI Command Center`
- Preview: `output/dashboard_preview.html`
- Final dashboard QA screenshot: `qa/html_dashboard_screenshot.png`
- Template research notes: `docs/template_research_notes.md`

## Final Dashboard

- Open `output/dashboard_final.html` for the finished BI dashboard.
- The dashboard is self-contained and works offline with no external CDN dependency.
- Included controls: date range, channel, paid vs organic, and recommended action.
- Included views: Overview, Channel ROI, Campaign Ranking, and Actions.
- Main business question: which channels are burning spend and which channels can scale.

## Power BI Status

- Power BI Desktop window verified with Computer Use.
- Project import workbook created at `powerbi/marketing_campaign_roi_import.xlsx`.
- `output/dashboard_final.pbix` is intentionally not published in the GitHub portfolio.
- A valid final PBIX should be rebuilt from a clean Power BI process and pass extract/open/save/refresh QA before promotion.

## Business Story

The dashboard shows which channels are burning spend and which channels can scale.

- Review/cut: Google Search, Meta, TikTok, LinkedIn, Programmatic Display, Affiliates
- Scale: Direct, Email, Referral Partners, Organic Search
- Total spend: $4.0M
- Total revenue: $18.1M
- Portfolio ROAS: 4.49

## Pages

1. Executive Overview
2. Channel ROI
3. Campaign Ranking
4. Exceptions and Actions

## Visual Design

- Left navigation rail, executive KPI strip, white chart panels, and action-state colors.
- Action palette: Scale = green, Optimize = amber, Review/Cut = coral.
- Power BI theme file: `build/config/theme.json`
- Visual layout spec: `build/config/page_map.json` and `build/config/visual_map.json`
