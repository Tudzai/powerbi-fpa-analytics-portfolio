# Metric Definitions

| KPI | Business Definition | DAX Measure |
|---|---|---|
| Total transactions | Count of all monitored financial transactions in the selected period. | [Total Transactions] |
| Flagged amount | Sum of transaction value where monitoring logic generated a flag. | [Flagged Amount] |
| Alerts | Count of generated monitoring alerts. | [Alert Count] |
| Suspicious cases | Cases confirmed suspicious or filed as SAR. | [Suspicious Cases] |
| False positive rate | False-positive alerts divided by closed alerts. Uses DIVIDE. | [False Positive Rate] |
| Rule precision | True-positive alerts divided by closed alerts. Uses DIVIDE. | [Rule Precision] |
| SLA compliance | Cases not overdue divided by all cases. Uses DIVIDE. | [SLA Compliance Rate] |
| Alert to case conversion | Cases opened divided by alert count. Uses DIVIDE. | [Alert to Case Conversion] |
