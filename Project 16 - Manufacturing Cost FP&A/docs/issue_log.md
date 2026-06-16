# Issue Log

| Issue | Status | Notes |
|---|---|---|
| No production data supplied | Accepted | Synthetic fixed-seed portfolio data generated and documented. |
| Existing Project 13 Power BI sessions detected | Controlled | Session guard requires exact Project 16 `PbixPath` before push/save. |
| Seed PBIX contains prior PVM sample model | Controlled | Seed is technical container only; Project 16 model and layout replace current content during Desktop build. |
| Power BI Desktop did not persist live model into PBIX | Blocked | Live Project 16 model on port `56532` passes table/measure checks, but offline `output/dashboard_final.pbix` still exports seed tables (`Sales`, `Prices`, `Calendar`, `Products`, `Year`). Other open Power BI windows also expose credential/pending-query modals, making UI save/apply unsafe to automate further. |
| pbi-tools compile PBIT failed under Desktop 26.05 | Blocked | `pbi-tools compile` raised `MissingMethodException` against the installed Power BI packaging assembly. A manual schema PBIT was created and extract-validated as supplemental. |
