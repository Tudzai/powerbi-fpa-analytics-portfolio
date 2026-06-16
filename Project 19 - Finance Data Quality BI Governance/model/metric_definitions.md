# Metric Definitions

| Metric | Definition | Why it matters |
|---|---|---|
| Data Quality Score | Average quality score from freshness, completeness, duplicate, null, schema drift, and incident pressure signals. | Executive trust indicator for finance datasets. |
| Freshness SLA % | Dataset-days refreshed within configured SLA divided by all dataset-days. | Shows whether finance data is timely enough for close and reporting cycles. |
| Refresh Success % | Successful refresh runs divided by total refresh runs. | Measures pipeline reliability and operational readiness. |
| Completeness % | Loaded rows divided by expected rows. | Guards against partial loads and silent data loss. |
| Reconciliation Pass % | Passing reconciliation rows divided by all reconciliation rows. | Connects data quality to controllership trust. |
| Access Risk Events | RLS exceptions, orphaned users, and unauthorized sharing events. | Indicates governance and confidentiality risk. |
| Deployment Control Score | Average monthly control score from access review and deployment signals. | Tracks whether report ownership and release control are healthy. |
