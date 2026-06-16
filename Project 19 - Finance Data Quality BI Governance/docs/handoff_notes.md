# Handoff Notes

- Final PBIX target: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 19 - Finance Data Quality BI Governance\output\dashboard_final.pbix`
- Current PBIX status: pending Desktop build/open-check.
- Build package: `output/powerbi_project/Finance_Data_Quality_BI_Governance.pbip`
- Supplemental preview: `output/dashboard_final.html`
- Build route: PBIP_PBIT seed generated, Desktop save to PBIX pending exact-session validation.
- Pages: Governance Overview; Reliability & Quality; Adoption & Controls.
- Visual count: 37 native visual definitions.
- Data source: synthetic portfolio data, seed `20260615`, generated from `build/scripts/build_project19.py`.
- Known issue: Several unrelated Power BI Desktop windows are open and `pbi-tools info` times out. A Project 19 PBIP process was launched and detected by command line, but a credential prompt/topmost window from another Power BI session prevented a clean Project 19 visual open-check. No save or overwrite action was performed.

## PBIX Status

Final output: blocked for PBIX build.

Reason: Power BI Desktop session isolation is not safe right now. The generated PBIP seed exists and is ready, but final PBIX cannot be called complete until Desktop opens Project 19 cleanly, refreshes the CSV-backed model, saves `output/dashboard_final.pbix`, and reopens that exact file with visual error count 0.
