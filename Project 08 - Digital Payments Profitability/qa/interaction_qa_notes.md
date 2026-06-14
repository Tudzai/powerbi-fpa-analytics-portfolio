# Interaction QA Notes

HTML preview filters update KPI cards, charts, and tables for Month, Segment, Method, Channel, Search, and Scenario in the generated artifact logic.

PBIX validated interactions:
- Month, Segment, Method, and Channel slicers appear on each page.
- Scenario slicer appears on Margin & Scenario Planning.
- Native charts and tables use report-level cross filtering.
- Final PBIX was opened and saved in Power BI Desktop after native layout patching.
- `pbi-tools extract` and `pbi-tools export-data` passed after the final Desktop save.

Browser note: the in-app Browser blocked direct `file://` navigation by policy, so HTML preview QA relies on generated screenshots and local artifact inspection rather than browser automation.
