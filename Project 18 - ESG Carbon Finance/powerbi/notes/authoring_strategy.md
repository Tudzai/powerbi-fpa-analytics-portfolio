# PBIX Authoring Decision

Preferred route: COMPUTER_USE / Desktop-assisted PBIX build.

Evidence:
- Power BI Desktop EXE is installed.
- Microsoft Store Power BI Desktop is also installed.
- pbi-tools is installed and can extract PBIX files.
- pbi-tools compile failed in this environment because the installed Desktop packaging API does not match the pbi-tools Desktop compile call.

Fallback routes:
- PBIP/PBIT build package: prepared as supplemental source package.
- Manual-assisted Desktop build: documented if automated Save As cannot complete.

Final status is not complete until `output/dashboard_final.pbix` exists and opens in Power BI Desktop with visual error count 0.
