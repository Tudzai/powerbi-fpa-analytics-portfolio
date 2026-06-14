# PBIX Authoring Decision

Selected route: SCRIPTED_DESKTOP_PBIX with Computer Use-assisted Desktop save/check.

Reason:
- Power BI Desktop and pbi-tools are installed.
- pbi-tools compile cannot create a full data-model PBIX directly; it can help inspect/extract/validate.
- The deterministic route is to push the semantic model into Power BI Desktop, save a model PBIX, patch a native report layout, validate with PowerBIPackager, then reopen the exact final file.

Fallback:
- If Desktop save/open-check cannot complete, final output must be marked blocked for PBIX build, with HTML/PBIP retained as supplemental build package.
