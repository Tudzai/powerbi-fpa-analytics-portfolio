# Agentic BI Research Notes

Checked on 2026-06-26 while enhancing Project 13 from Project 20 patterns.

## Public references used

| Source | URL | Useful pattern |
|---|---|---|
| GitHub Awesome Copilot Power BI Visualization Expert | https://github.com/github/awesome-copilot/blob/main/agents/power-bi-visualization-expert.agent.md | Visual hierarchy, chart selection, layout grouping, accessibility, and performance-oriented report design. |
| Microsoft Skills for Fabric `AGENTS.md` | https://github.com/microsoft/skills-for-fabric/blob/main/AGENTS.md | Plan/design/author/validate workflow; avoid hardcoded connection strings and validate report artifacts. |
| Microsoft Power BI Report Authoring skill | https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-authoring/SKILL.md | PBIR/PBIP edit loop: understand model, edit report files, validate, reload/screenshot review. |
| Data Goblin Power BI Agentic Development | https://github.com/data-goblin/power-bi-agentic-development | Skills/subagents/hooks pattern for agentic Power BI work; reinforces specialized review passes. |
| Data Goblins Power BI Report Checklist | https://data-goblins.com/report-checklist | 3/30/300 thinking, consistent theme, default sort, interaction testing, no unnecessary visuals. |
| pbi-tools | https://github.com/pbi-tools/pbi-tools | Source-control friendly Power BI workflow and PBIX/PBIP extract/validate mindset. |

## Applied to Project 13

- Kept Project 13 palette and top horizontal slicer layout.
- Adopted Project 20 rhythm: compact top lens, KPI strip with embedded sparkline/status, and consistent chart panel shells.
- Changed native KPI cards to SVG-backed table visuals so the value, PY comparison, status, and sparkline render together instead of relying on separate tiny combo visuals.
- Updated HTML preview cards to include mini sparklines and decision-chip style action cards.
- Added chart empty states and clearer compact bar-chart labels so filters do not leave confusing blank frames.
- Rebuilt and validated HTML with desktop and mobile Playwright checks.
- Repacked PBIX and validated `PowerBIPackager.Validate` on `output/dashboard_final.pbix`.
