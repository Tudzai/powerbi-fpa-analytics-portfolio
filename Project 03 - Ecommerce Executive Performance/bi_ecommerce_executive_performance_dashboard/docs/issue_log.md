# Issue Log

| ID | Severity | Issue | Status | Resolution |
|---|---|---|---|---|
| ISS-001 | Medium | No production source data supplied | Closed | Generated synthetic portfolio demo data and documented it |
| ISS-002 | High | PBIX cannot be truthfully marked final until built and refresh-tested | Closed | Built `output/dashboard_final.pbix`, validated package, reopened it in Power BI Desktop, and captured screenshot evidence |
| ISS-003 | Low | Real subagents not spawned | Closed | Tool policy requires explicit subagent request; simulated 4-role workflow and logged fallback |
| ISS-004 | High | SCRIPTED_DESKTOP_PBIX route must be attempted before manual fallback | Closed | Used Computer Use to save the model PBIX, then applied and validated the scripted native report layout |
| ISS-005 | High | Initial native final PBIX opened with a Power BI theme `customTheme` render error | Closed | Patched the layout generator to place `themeCollection` inside the top-level Layout `config` JSON, repackaged the PBIX, and verified clean render |
| ISS-006 | Medium | First visual pass looked too plain for a portfolio-facing executive dashboard | Closed | Researched modern Power BI/ecommerce templates and applied a polished header, KPI, card, canvas, and palette refresh |
| ISS-007 | Medium | Executive overview needed a clearer complete business readout | Closed | Added Top Category, Top Channel, ROAS, and Quality Watch insight cards from validated KPI data |
