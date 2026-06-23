# Handoff Notes

Final PBIX: `output/dashboard_final.pbix` rebuilt and checked in Power BI Desktop on 2026-06-23.
Build route: source upgrade complete; seed PBIX opened in Power BI Store App, model replaced via TOM direct-port binding, seed saved, native layout patched into final PBIX.
Data: synthetic SaaS CFO demo data, seed `20260615`.
Model: 13 data tables plus KPI Measures, 17 relationships, 75 DAX measures.
Pages: Executive Overview; Revenue & Retention; Efficiency & Forecast.
Upgrade: Project 20 quality patterns applied without copying Project 20's purple investor-pack skin.
Layout: dark navy left sidebar, compact dropdown lens controls, Current Lens SVG, decision chips, four SVG KPI cards per page, synced chart slots, polished tables.
QA: data QA `pass`; source layout verification is `qa/project20_upgrade_verification.json`; native PBIX patch validation is `qa/pbix_native_report_validation.json`; final Desktop evidence is `qa/powerbi_desktop_evidence.json`; final PBIX validation is `qa/pbix_final_validation.json`.
