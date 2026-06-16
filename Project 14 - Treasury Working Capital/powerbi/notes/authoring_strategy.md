# PBIX Authoring Decision

Chosen route: SCRIPTED_DESKTOP_PBIX with Computer Use verification.

Reason:
- Power BI Desktop EXE is installed.
- pbi-tools is installed and can identify local Power BI Desktop sessions by exact `PbixPath`.
- The selected local seed PBIX validates with Power BI packaging assemblies.
- Project 13 proved the TOM push plus native Report/Layout patch pattern works in this repository.

Template selected:
- Technical seed: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\01_Core_Financial_Statements\Packt_Ch07_Group_Reporting.pbix`
- Domain reference: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\02_AR_Working_Capital\Prodata_Finance-AR_Receivables.pbix`
- Why: the AR Working Capital template is the closest semantic/design reference, but it does not expose the `/Report/Layout` package part needed by the native layout patch route. The Group Reporting sample is the safer technical seed because it contains `/Report/Layout`, has no stale `/UnappliedChanges` web-query prompt, and supports TOM replacement; Project 14 replaces the model, measures, pages, and visual bindings.

Fallbacks:
- If Desktop save/open-check fails, keep PBIP/PBIT and HTML as supplemental build package and mark PBIX blocked.
