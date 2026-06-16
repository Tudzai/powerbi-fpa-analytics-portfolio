# PBIX Authoring Decision

Decision: SCRIPTED_DESKTOP_PBIX.

Rationale:
- Power BI Desktop EXE is available at `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe`.
- pbi-tools is available at `C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe` for session discovery and package QA.
- Use `Microsoft_Customer_Profitability.pbix` only as a valid PBIX container because it is the closest finance/profitability seed.
- Replace the model with Project 17 tables/measures through Desktop TOM/XMLA, save the exact seed, patch native layout, validate package, then open/save/reopen final.

Seed template:
`C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\04_Profitability_Margin\Microsoft_Customer_Profitability.pbix`
