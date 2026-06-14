# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Desktop QA.
Data: synthetic demo data, seed `20260611`.
Model: 12 tables, 16 relationships, native Power BI report layout with 3 pages and 48 visual containers.
QA: data QA `pass`; PBIX validation `pass`; pbi-tools extract/export-data `pass`; Power BI Desktop visual check `pass`.

Desktop QA evidence:
- `qa/desktop_page1_growth.jpg`
- `qa/desktop_page2_funnel_cohort.jpg`
- `qa/desktop_page3_ltv_roi.jpg`

Primary supporting artifacts:
- `model/MEASURES.dax`
- `model/metric_definitions.md`
- `model/relationship_map.md`
- `docs/design_research.md`
- `docs/refresh_guide.md`
- `docs/rebuild_guide.md`
- `qa/pbix_extract_final_project11`
- `qa/export_data_final`
