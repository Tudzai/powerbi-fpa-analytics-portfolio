# DAX Measures

## Total Transactions

```DAX
Total Transactions = COUNTROWS ( FactTransactions )
```

## Transaction Amount

```DAX
Transaction Amount = SUM ( FactTransactions[AmountUSD] )
```

## Flagged Transactions

```DAX
Flagged Transactions = CALCULATE ( [Total Transactions], FactTransactions[IsFlagged] = "Y" )
```

## Flagged Amount

```DAX
Flagged Amount = CALCULATE ( [Transaction Amount], FactTransactions[IsFlagged] = "Y" )
```

## Alert Count

```DAX
Alert Count = COUNTROWS ( FactAlerts )
```

## Case Count

```DAX
Case Count = COUNTROWS ( FactCases )
```

## Suspicious Cases

```DAX
Suspicious Cases = CALCULATE ( [Case Count], FactCases[Outcome] IN { "Confirmed Suspicious", "SAR Filed" } )
```

## SAR Filed Cases

```DAX
SAR Filed Cases = CALCULATE ( [Case Count], FactCases[SARFiled] = "Y" )
```

## Closed Alerts

```DAX
Closed Alerts = CALCULATE ( [Alert Count], FactAlerts[AlertStatus] IN { "Closed False Positive", "Closed True Positive", "SAR Filed" } )
```

## False Positive Alerts

```DAX
False Positive Alerts = CALCULATE ( [Closed Alerts], FactAlerts[IsFalsePositive] = "Y" )
```

## False Positive Rate

```DAX
False Positive Rate = DIVIDE ( [False Positive Alerts], [Closed Alerts] )
```

## True Positive Alerts

```DAX
True Positive Alerts = CALCULATE ( [Alert Count], FactAlerts[IsTruePositive] = "Y" )
```

## Rule Precision

```DAX
Rule Precision = DIVIDE ( [True Positive Alerts], [Closed Alerts] )
```

## Alert Rate

```DAX
Alert Rate = DIVIDE ( [Alert Count], [Total Transactions] )
```

## Alert to Case Conversion

```DAX
Alert to Case Conversion = DIVIDE ( [Case Count], [Alert Count] )
```

## SAR Conversion Rate

```DAX
SAR Conversion Rate = DIVIDE ( [SAR Filed Cases], [Case Count] )
```

## Open Cases

```DAX
Open Cases = CALCULATE ( [Case Count], NOT ( FactCases[CaseStatus] IN { "Closed", "SAR Filed" } ) )
```

## Overdue Cases

```DAX
Overdue Cases = CALCULATE ( [Case Count], FactCases[IsOverdue] = "Y" )
```

## SLA Compliance Rate

```DAX
SLA Compliance Rate = DIVIDE ( [Case Count] - [Overdue Cases], [Case Count] )
```

## Average Case Age Days

```DAX
Average Case Age Days = AVERAGE ( FactCases[AgeDays] )
```

## Average Alert Risk Score

```DAX
Average Alert Risk Score = AVERAGE ( FactAlerts[RiskScore] )
```

## High Risk Customers

```DAX
High Risk Customers = CALCULATE ( DISTINCTCOUNT ( DimCustomer[CustomerKey] ), DimCustomer[CustomerRiskTier] = "High" )
```

## Governance Changes

```DAX
Governance Changes = COUNTROWS ( FactRuleGovernance )
```

## Avg Precision After Tuning

```DAX
Avg Precision After Tuning = AVERAGE ( FactRuleGovernance[PrecisionAfter] )
```

## Alert Amount

```DAX
Alert Amount = SUM ( FactAlerts[AlertAmountUSD] )
```

## Case Amount

```DAX
Case Amount = SUM ( FactCases[CaseAmountUSD] )
```
