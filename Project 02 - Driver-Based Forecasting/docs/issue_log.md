# Issue Log

## ISSUE-001 - PBIX final build completed

- Status: Closed
- Severity: Medium
- Found in: v01 build pack
- Page: File output
- Expected: `output/dashboard_final.pbix` exists and passes open/save/refresh QA.
- Actual: `output/dashboard_final.pbix` exists, was saved in Power BI Desktop, and was extract-verified after save.
- Root cause: Power BI Desktop PBIX creation is a UI save workflow, so the build required a PBIT-to-PBIX save step in Desktop.
- Fix: Generated a PbixProj/PBIT source project, opened it in Power BI Desktop, refreshed the model, saved `output/dashboard_final.pbix`, and verified the saved file.
