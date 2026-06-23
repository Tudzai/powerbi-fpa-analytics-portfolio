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

## Current Lens Label

```DAX
VAR MonthLens = SELECTEDVALUE ( DimDate[MonthYear], "All Months" )
VAR DomainLens = SELECTEDVALUE ( DimDataset[Domain], "All Domains" )
VAR CriticalityLens = SELECTEDVALUE ( DimDataset[Criticality], "All Tiers" )
RETURN "Lens: " & MonthLens & " | " & DomainLens & " | " & CriticalityLens
```
Format: ``

## Usage Lens Label

```DAX
VAR WorkspaceLens = SELECTEDVALUE ( DimReport[Workspace], "All Workspaces" )
VAR SensitivityLens = SELECTEDVALUE ( DimReport[SensitivityLabel], "All Sensitivity" )
RETURN "Lens: " & WorkspaceLens & " | " & SensitivityLens
```
Format: ``

## Action Lens Label

```DAX
VAR MonthLens = SELECTEDVALUE ( DimDate[MonthYear], "All Months" )
VAR DepartmentLens = SELECTEDVALUE ( DimDepartment[Department], "All Departments" )
RETURN "Lens: " & MonthLens & " | " & DepartmentLens
```
Format: ``

## Governance Decision Chip

```DAX
VAR Dq = [Data Quality Score]
VAR Fresh = [Freshness SLA %]
VAR OpenIncidents = [Open Incidents]
RETURN IF ( Dq >= 92 && Fresh >= 0.95 && OpenIncidents <= 30, "PASS: trust posture on track", IF ( OpenIncidents > 45, "ESCALATE: incident load above guardrail", "WATCH: owner review required" ) )
```
Format: ``

## Reliability Decision Chip

```DAX
VAR Failed = [Failed Refreshes]
VAR Complete = [Completeness %]
VAR RecPass = [Reconciliation Pass %]
RETURN IF ( Failed <= 25 && Complete >= 0.99 && RecPass >= 0.90, "PASS: close-ready reliability", IF ( Failed > 40 || Complete < 0.985, "ESCALATE: reliability SLA at risk", "WATCH: validate exception queue" ) )
```
Format: ``

## Adoption Decision Chip

```DAX
VAR LoadSec = [Avg Report Load Seconds]
VAR AccessRisk = [Access Risk Events]
VAR ControlScore = [Deployment Control Score]
RETURN IF ( LoadSec <= 3.0 && AccessRisk <= 800 && ControlScore >= 92, "PASS: governed adoption healthy", IF ( AccessRisk > 950, "ESCALATE: access risk concentration", "WATCH: control follow-up needed" ) )
```
Format: ``

## Risk Action Decision Chip

```DAX
VAR OpenIncidents = [Open Incidents]
VAR AccessRisk = [Access Risk Events]
VAR Pending = [Pending Access Reviews]
RETURN IF ( OpenIncidents <= 30 && AccessRisk <= 800 && Pending <= 900, "PASS: action load inside guardrail", IF ( OpenIncidents > 45 || Pending > 1100, "ESCALATE: prioritize owner actions", "WATCH: triage aging queues" ) )
```
Format: ``
