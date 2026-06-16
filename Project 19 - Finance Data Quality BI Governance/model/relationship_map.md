# Relationship Map

| From | To | Direction |
|---|---|---|
| FactDatasetDaily[DateKey] | DimDate[DateKey] | oneDirection |
| FactDatasetDaily[DatasetKey] | DimDataset[DatasetKey] | oneDirection |
| FactRefreshRuns[DateKey] | DimDate[DateKey] | oneDirection |
| FactRefreshRuns[DatasetKey] | DimDataset[DatasetKey] | oneDirection |
| FactReconciliation[DateKey] | DimDate[DateKey] | oneDirection |
| FactReconciliation[DatasetKey] | DimDataset[DatasetKey] | oneDirection |
| FactIncidents[DateKey] | DimDate[DateKey] | oneDirection |
| FactIncidents[DatasetKey] | DimDataset[DatasetKey] | oneDirection |
| FactReconciliation[DeptKey] | DimDepartment[DeptKey] | oneDirection |
| FactUsage[DateKey] | DimDate[DateKey] | oneDirection |
| FactUsage[ReportKey] | DimReport[ReportKey] | oneDirection |
| FactUsage[DeptKey] | DimDepartment[DeptKey] | oneDirection |
| FactAccessReview[DateKey] | DimDate[DateKey] | oneDirection |
| FactAccessReview[ReportKey] | DimReport[ReportKey] | oneDirection |
| FactAccessReview[DeptKey] | DimDepartment[DeptKey] | oneDirection |
