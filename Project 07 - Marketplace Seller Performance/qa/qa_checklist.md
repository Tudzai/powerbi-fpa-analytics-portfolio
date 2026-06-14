# QA Checklist

| Area | Status | Notes |
| --- | --- | --- |
| Data QA | PASS | Raw/prepared reconciliation passed. |
| Metric QA | PASS | Definitions, DAX, denominator rules documented. |
| Visual QA | PASS | Native PBIX contains a card visual for core KPIs and a seller table visual with GMV, fulfillment, cancellation, rating, and stock availability. Static HTML/PNG preview remains supplemental. |
| Interaction QA | PASS | PBIX opens in edit mode with filter pane and fields bound to the native visuals. No slicer page was added in this final cut. |
| File QA | PASS | `output/dashboard_final.pbix` exists, was saved by Power BI Desktop, and passed `pbi-tools extract` plus `pbi-tools export-data`. |
| Performance QA | PASS | Extract/export completed successfully against the compact monthly seller model. |
