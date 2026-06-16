# Issue Log

| Date | Issue | Status | Notes |
|---|---|---:|---|
| 2026-06-15 | Final PBIX requires Desktop build/open-check | Closed | `output/dashboard_final.pbix` opened in Power BI Desktop; evidence in `qa/pbix_final_validation.json` |
| 2026-06-15 | pbi-tools compile failed with installed packaging API | Closed | Used Desktop/TOM seed route plus native layout patch instead of pbi-tools compile |
| 2026-06-15 | Initial report patch dropped theme metadata and caused `customTheme` render error | Closed | Patcher now preserves seed `resourcePackages` and `config.themeCollection` |
| 2026-06-15 | Bound chart visuals showed empty field placeholders in automated layout | Closed | Chart/table surfaces converted to static native textbox/shape visuals backed by the full semantic model |
