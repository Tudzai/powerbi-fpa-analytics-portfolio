# QA Checklist

| Area | Status | Evidence |
|---|---|---|
| Data QA | PASS | `data/validated/validation_summary.json` |
| Metric QA | PASS | `qa/reconciliation.json` |
| Visual QA | PASS for generated preview and native PBIX open/save | `output/screenshots/`, `qa/final_pbix_validation.json` |
| Interaction QA | PASS for native slicer/page structure; HTML checked by generated preview artifacts | `qa/interaction_qa_notes.md` |
| File QA | PASS | `output/dashboard_final.pbix`, `qa/final_pbix_validation.json` |
