# Handoff Notes

Final product: BNPL / Digital Lending Credit Risk Dashboard.

Final PBIX: `output/dashboard_final.pbix`.

Build route: `SCRIPTED_DESKTOP_PBIX` using synthetic data generation, TOM model push into a validated seed PBIX, native report layout patch, PowerBIPackager validation, Power BI Desktop save, final extract, and export-data QA.

Dashboard pages:

1. Credit Risk Overview
2. Delinquency & Vintage Analysis
3. Collections & Provision Forecast

Model summary:

- 15 tables
- 25 relationships
- 27 KPI measures
- Synthetic data seed: 90209
- Main fact volumes: 52,000 applications, 33,051 loans, 218,547 monthly loan snapshots, 40,586 collections cases

Desktop QA summary:

- Exact file opened: yes
- Desktop save confirmed: yes
- Visual error count: 0
- Final screenshots saved under `output/screenshots`

Known issues: none for the final PBIX.

Non-blocking note: direct pbi-tools PBIT compile failed in this environment because the installed Power BI packaging API raised `Microsoft.PowerBI.Packaging.PowerBIPackager.Save` MissingMethodException. The final PBIX was built through the validated Desktop seed + TOM + native layout patch route instead.
