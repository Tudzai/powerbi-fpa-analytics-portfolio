# Power BI Desktop Evidence

Checked on: 2026-06-11

Final PBIX:
`C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 11 - Neobank Growth Retention LTV\output\dashboard_final.pbix`

Desktop result:
- Power BI Desktop opened the final PBIX.
- Title bar showed `dashboard_final` and last saved status.
- Data pane showed the expected Neobank model tables.
- Page 1 `Growth Overview`: no visual errors detected.
- Page 2 `Funnel & Cohort Retention`: no visual errors detected.
- Page 3 `LTV, Churn & Marketing ROI`: no visual errors detected.

Screenshot evidence:
- `qa/desktop_page1_growth.jpg`
- `qa/desktop_page2_funnel_cohort.jpg`
- `qa/desktop_page3_ltv_roi.jpg`

CLI validation:
- `pbi-tools extract`: pass, output in `qa/pbix_extract_final_project11`.
- `pbi-tools export-data`: pass, output in `qa/export_data_final`.
- `build/scripts/04_validate_output.py`: pass.
