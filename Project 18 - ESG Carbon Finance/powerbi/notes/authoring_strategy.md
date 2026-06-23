# PBIX Authoring Decision

Preferred route: SCRIPTED_DESKTOP_PBIX with Desktop open-check.

Evidence:
- Power BI Desktop EXE is installed.
- Microsoft Store Power BI Desktop is also installed.
- pbi-tools is installed and can extract PBIX files.
- pbi-tools compile failed in this environment because the installed Desktop packaging API does not match the pbi-tools Desktop compile call.

Fallback routes:
- PBIP/PBIT build package: prepared as supplemental source package.
- Manual-assisted Desktop build: documented if automated Save As cannot complete.

Final status:
- Original 2026-06-15 PBIX opened in Power BI Desktop with visual error count 0.
- 2026-06-23 v3 upgrade regenerates source/model/layout package and requires a fresh Desktop open-check after PBIX patching.
