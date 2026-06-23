# Issue Log

No open data QA issues.

## PBIX Rebuild Resolved - 2026-06-23

The Project 20-style source upgrade and upgraded final PBIX rebuild completed.

Resolution: The exact Project 15 seed PBIX was opened through File Explorer using its full path. Because `pbi-tools info` timed out with several unrelated Power BI sessions open, the TOM model push used the seed process workspace port directly (`58188`) after confirming the process command line matched `output/dashboard_model_seed.pbix`.

Evidence: `qa/pbix_rebuild_attempt_20260623.json`, `qa/seed_model_push_via_tom.json`, `qa/pbix_native_report_validation.json`, and `qa/powerbi_desktop_evidence.json`.

Final result: `output/dashboard_final.pbix` is the upgraded final PBIX, size 4,391,319 bytes after Desktop save, SHA256 `B93D9FB627EF5164F43B0B1DAD796ED1FEFC8E39BEBB65771D32235FFD93021C`.

Note: A transient Microsoft .NET Framework `Error creating window handle` dialog appeared on first final open while multiple unrelated Power BI instances were running. It was dismissed once; the model then reloaded and all three pages rendered.
