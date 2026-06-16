# Data Dictionary

## DimDate

- Rows: 516
- Grain: one row per calendar day

| Column | Type |
|---|---|
| DateKey | int64 |
| Date | dateTime |
| MonthEndDate | dateTime |
| MonthKey | int64 |
| Year | int64 |
| Quarter | string |
| MonthNumber | int64 |
| MonthName | string |
| MonthYear | string |
| MonthIndex | int64 |
| IsLatestCompleteMonth | string |

## DimDataset

- Rows: 12
- Grain: one row per governed finance dataset

| Column | Type |
|---|---|
| DatasetKey | string |
| DatasetName | string |
| Domain | string |
| SourceSystem | string |
| Criticality | string |
| OwnerTeam | string |
| SLAHours | int64 |
| RefreshFrequency | string |
| RLSRequired | string |
| Certified | string |

## DimReport

- Rows: 9
- Grain: one row per finance Power BI report

| Column | Type |
|---|---|
| ReportKey | string |
| ReportName | string |
| Workspace | string |
| Audience | string |
| OwnerTeam | string |
| Certified | string |
| SensitivityLabel | string |
| ReportTier | string |

## DimDepartment

- Rows: 8
- Grain: one row per consuming department

| Column | Type |
|---|---|
| DeptKey | string |
| Department | string |
| Function | string |
| Region | string |

## FactDatasetDaily

- Rows: 6,192
- Grain: one row per dataset per day

| Column | Type |
|---|---|
| DateKey | int64 |
| DatasetKey | string |
| RowsExpected | int64 |
| RowsLoaded | int64 |
| CompletenessPct | double |
| NullCriticalCount | int64 |
| DuplicateKeyCount | int64 |
| SchemaDriftCount | int64 |
| FreshnessMinutes | int64 |
| FreshnessWithinSLAFlag | int64 |
| DataQualityScore | double |
| ReconciliationVarianceAmount | double |
| OpenIssueCount | int64 |

## FactRefreshRuns

- Rows: 6,192
- Grain: one row per dataset refresh run per day

| Column | Type |
|---|---|
| RefreshRunKey | string |
| DateKey | int64 |
| DatasetKey | string |
| Status | string |
| FailureCategory | string |
| DurationMinutes | int64 |
| SLACompliantFlag | int64 |
| RetryCount | int64 |

## FactReconciliation

- Rows: 612
- Grain: one row per dataset, department, and month-end reconciliation

| Column | Type |
|---|---|
| DateKey | int64 |
| DatasetKey | string |
| DeptKey | string |
| LedgerAmount | double |
| SubledgerAmount | double |
| VarianceAmount | double |
| VariancePct | double |
| ReconciliationStatus | string |
| AgingBucket | string |

## FactUsage

- Rows: 4,644
- Grain: one row per report per day

| Column | Type |
|---|---|
| DateKey | int64 |
| ReportKey | string |
| DeptKey | string |
| Views | int64 |
| UniqueViewers | int64 |
| ExportEvents | int64 |
| SubscriptionRuns | int64 |
| AvgLoadSeconds | double |
| FailedVisualCount | int64 |

## FactAccessReview

- Rows: 1,224
- Grain: one row per report, department, and monthly access review

| Column | Type |
|---|---|
| DateKey | int64 |
| ReportKey | string |
| DeptKey | string |
| UsersWithAccess | int64 |
| PrivilegedUsers | int64 |
| OrphanedUsers | int64 |
| RLSExceptions | int64 |
| PendingAccessReviews | int64 |
| UnauthorizedSharingEvents | int64 |
| DeploymentControlScore | double |

## FactIncidents

- Rows: 240
- Grain: one row per data quality or BI governance incident

| Column | Type |
|---|---|
| IncidentKey | string |
| DateKey | int64 |
| DatasetKey | string |
| Severity | string |
| IncidentStatus | string |
| RootCause | string |
| MTTRHours | double |
| SLAOverdueFlag | int64 |
| BusinessImpact | string |
