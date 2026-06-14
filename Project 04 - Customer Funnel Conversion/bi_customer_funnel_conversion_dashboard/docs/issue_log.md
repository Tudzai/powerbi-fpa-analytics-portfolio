# Issue Log

## ISSUE-001 - Previous Project 04 - Customer Funnel Conversion artifacts locked during reset

- Status: Closed
- Severity: Low
- Root cause: The old Project 04 - Customer Funnel Conversion folder was held by a process while deleting the parent folder.
- Fix: Removed old contents inside Project 04 - Customer Funnel Conversion scope and rebuilt artifacts from scratch in the same project folder.
- Regression: New files are generated from seed and do not depend on previous prompt artifacts.

## ISSUE-002 - PBIX final depends on Desktop save automation

- Status: Open until PBIX File QA passes
- Severity: Medium
- Root cause: TOM/XMLA can push model to an open Desktop session but cannot save PBIX by itself.
- Fix: Generated model push script, best-effort save script, and manual-assisted runbook.
- Regression: No fake PBIX is created.

## ISSUE-003 - Text business keys inferred as numeric in TOM push

- Status: Fixed
- Severity: High
- Root cause: The PowerShell type inference treated all `_key` columns as Int64, which blanked text keys such as `device_key` and `campaign_key` on the one side of relationships.
- Fix: Patched `build/scripts/07_push_model_to_powerbi_desktop.ps1` and the generator source so only numeric keys such as `date_key`, `stage_key`, sort/order fields, and flags are typed as Int64.
- Regression: Model push reran successfully with 14 tables, 31 relationships, and 22 measures.
