# Issue Log

No open data QA issues.

Power BI Desktop had multiple unrelated PBIX windows open during QA. The Project 15 final file was identified by `pbi-tools info` and Windows process metadata before saving:
- PID 41448
- Window handle 1051452
- `PbixPath`: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 15 - SaaS CFO Metrics\output\dashboard_final.pbix`

Power BI canvas accessibility text was not reliable for visual labels, so final evidence combines native layout extraction, static previews, pbi-tools extract/export, and exact Desktop session metadata.
