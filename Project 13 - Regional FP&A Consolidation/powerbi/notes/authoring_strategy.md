# PBIX Authoring Decision

Decision: BLOCKED for native PBIX final.

Reason: The environment has Power BI Desktop, pbi-tools, and Computer Use. However, the reliable scripted authoring path for a full native PBIX is not available in this run: no Tabular Editor or dotnet CLI route is available, pbi-tools compile supports PBIX only for thin reports and PBIT for data-model projects, and UI-only native authoring through Computer Use is not deterministic enough to create, save, reopen, and visually QA a multi-page FP&A report without risking a false final.

Chosen deliverable: portable HTML dashboard plus Power BI-ready data/model/DAX/runbook package. No fake PBIX is created.
