# PBIX Authoring Decision

Decision status: `scripted_desktop_attempt_ready`.

Preferred route:

1. Open Power BI Desktop.
2. Push the prepared semantic model through local Desktop XMLA/TOM using `build/scripts/07_push_model_to_powerbi_desktop.ps1`.
3. Save the active report as `output/dashboard_model.pbix`.
4. Generate native report layout JSON using `build/scripts/10_build_native_pbix_report.py`.
5. Patch `/Report/Layout` into the model PBIX using `build/scripts/10_apply_native_pbix_report.ps1`.
6. Open/save/refresh the final PBIX for File QA.

Tool evidence:

- Power BI Desktop EXE is available.
- pbi-tools is available and detects local Desktop sessions.
- `Microsoft.PowerBI.Packaging.dll` exists in the Power BI Desktop install.
- Current thread does not expose callable Computer Use desktop controls, so automated save/open screenshot QA may need manual-assisted UI unless keyboard automation succeeds.

Important limitation:

- pbi-tools alone will not author a full PBIX with imported data model from scratch. It can compile PBIX only for thin report projects and PBIT for model projects.
