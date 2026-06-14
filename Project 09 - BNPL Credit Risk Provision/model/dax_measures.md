# DAX Measures

| Measure | Format | Definition |
|---|---|---|
| Applications | `#,0` | Total submitted credit applications. |
| Approved Applications | `#,0` | Approved application count. |
| Approval Rate | `0.0%` | Approved applications divided by total applications. |
| Disbursed Loans | `#,0` | Funded loan count. |
| Disbursement Amount | `$#,0,,.0M` | Total funded amount. |
| Loan Book Balance | `$#,0,,.0M` | Outstanding principal balance in selected snapshot context. |
| DPD 30+ Balance | `$#,0,,.0M` | Outstanding balance with 30 or more days past due. |
| DPD 60+ Balance | `$#,0,,.0M` | Outstanding balance with 60 or more days past due. |
| NPL Balance | `$#,0,,.0M` | Outstanding 90+ DPD or non-performing balance. |
| Delinquency Rate | `0.0%` | DPD 30+ balance divided by loan book balance. |
| NPL Rate | `0.0%` | NPL balance divided by loan book balance. |
| Expected Loss | `$#,0,,.0M` | Expected credit loss amount. |
| Expected Loss Rate | `0.0%` | Expected loss divided by loan book balance. |
| Provision Amount | `$#,0,,.0M` | Provision amount calculated from expected loss policy. |
| Provision Coverage | `0.0x` | Provision amount divided by expected loss. |
| Autopay Failure Loans | `#,0` | Loans with autopay failure flag. |
| Recovery Amount | `$#,0,,.0M` | Total recovery amount from collection cases. |
| Case Balance | `$#,0,,.0M` | Total balance assigned to collection cases. |
| Recovery Rate | `0.0%` | Recovered amount divided by collection case balance. |
| Collections SLA % | `0.0%` | Share of collection cases handled within SLA. |
| Promise To Pay % | `0.0%` | Share of cases with promise to pay. |
| Vintage 30+ Rate | `0.0%` | Vintage cohort DPD 30+ balance share. |
| Vintage Loss Rate | `0.0%` | Average cumulative loss rate across visible vintage cells. |
| Roll Rate | `0.0%` | Average roll rate across selected transition cells. |
| Forecast Provision | `$#,0,,.0M` | Forecast provision amount. |
| Forecast Expected Loss | `$#,0,,.0M` | Forecast expected loss. |
| Incremental Provision | `$#,0,,.0M` | Incremental provision bridge amount. |
