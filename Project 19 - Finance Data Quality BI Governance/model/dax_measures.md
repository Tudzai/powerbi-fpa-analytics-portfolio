# DAX Measures

## Dataset Count

```DAX
DISTINCTCOUNT ( DimDataset[DatasetKey] )
```
Format: `#,0`

## Critical Dataset Count

```DAX
CALCULATE ( [Dataset Count], DimDataset[Criticality] = "Tier 1" )
```
Format: `#,0`

## Certified Dataset Count

```DAX
CALCULATE ( [Dataset Count], DimDataset[Certified] = "Y" )
```
Format: `#,0`

## Data Quality Score

```DAX
AVERAGE ( FactDatasetDaily[DataQualityScore] )
```
Format: `0.0`

## Completeness %

```DAX
DIVIDE ( SUM ( FactDatasetDaily[RowsLoaded] ), SUM ( FactDatasetDaily[RowsExpected] ) )
```
Format: `0.0%`

## Freshness SLA %

```DAX
DIVIDE ( SUM ( FactDatasetDaily[FreshnessWithinSLAFlag] ), COUNTROWS ( FactDatasetDaily ) )
```
Format: `0.0%`

## Refresh Runs

```DAX
COUNTROWS ( FactRefreshRuns )
```
Format: `#,0`

## Refresh Success %

```DAX
DIVIDE ( CALCULATE ( [Refresh Runs], FactRefreshRuns[Status] = "Success" ), [Refresh Runs] )
```
Format: `0.0%`

## Failed Refreshes

```DAX
CALCULATE ( [Refresh Runs], FactRefreshRuns[Status] = "Failed" )
```
Format: `#,0`

## Avg Refresh Duration Min

```DAX
AVERAGE ( FactRefreshRuns[DurationMinutes] )
```
Format: `0.0`

## DQ Issue Count

```DAX
SUM ( FactDatasetDaily[NullCriticalCount] ) + SUM ( FactDatasetDaily[DuplicateKeyCount] ) + SUM ( FactDatasetDaily[SchemaDriftCount] )
```
Format: `#,0`

## Open Incidents

```DAX
CALCULATE ( COUNTROWS ( FactIncidents ), FactIncidents[IncidentStatus] <> "Closed" )
```
Format: `#,0`

## Avg MTTR Hours

```DAX
AVERAGE ( FactIncidents[MTTRHours] )
```
Format: `0.0`

## Reconciliation Variance

```DAX
SUM ( FactReconciliation[VarianceAmount] )
```
Format: `$#,0`

## Abs Reconciliation Variance

```DAX
SUMX ( FactReconciliation, ABS ( FactReconciliation[VarianceAmount] ) )
```
Format: `$#,0`

## Reconciliation Pass %

```DAX
DIVIDE ( CALCULATE ( COUNTROWS ( FactReconciliation ), FactReconciliation[ReconciliationStatus] = "Pass" ), COUNTROWS ( FactReconciliation ) )
```
Format: `0.0%`

## Report Views

```DAX
SUM ( FactUsage[Views] )
```
Format: `#,0`

## Active Viewer Days

```DAX
SUM ( FactUsage[UniqueViewers] )
```
Format: `#,0`

## Export Events

```DAX
SUM ( FactUsage[ExportEvents] )
```
Format: `#,0`

## Avg Report Load Seconds

```DAX
AVERAGE ( FactUsage[AvgLoadSeconds] )
```
Format: `0.0`

## Failed Visual Count

```DAX
SUM ( FactUsage[FailedVisualCount] )
```
Format: `#,0`

## Access Risk Events

```DAX
SUM ( FactAccessReview[RLSExceptions] ) + SUM ( FactAccessReview[OrphanedUsers] ) + SUM ( FactAccessReview[UnauthorizedSharingEvents] )
```
Format: `#,0`

## RLS Exceptions

```DAX
SUM ( FactAccessReview[RLSExceptions] )
```
Format: `#,0`

## Pending Access Reviews

```DAX
SUM ( FactAccessReview[PendingAccessReviews] )
```
Format: `#,0`

## Deployment Control Score

```DAX
AVERAGE ( FactAccessReview[DeploymentControlScore] )
```
Format: `0.0`
