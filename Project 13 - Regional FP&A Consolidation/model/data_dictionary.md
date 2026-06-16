## DimDate

One row per month. Key: `date_id`. Fields: calendar date, year, quarter, month label, latest-complete flag, and month index.

## DimEntity

One row per legal entity / country. Key: `entity_id`. Fields: entity name, country, region, functional currency, ownership percentage.

## DimBusinessUnit

One row per business unit. Key: `business_unit_id`. Used to slice financials and variance drivers.

## DimAccount

P&L account hierarchy. Key: `account_id`. Fields: account, group, sort order, and statement classification.

## DimScenario

Planning scenario dimension. Key: `scenario_id`. Values: Actual, Budget, Forecast, and Prior Year.

## FactFinancials

Monthly entity-BU-scenario-account grain. Amounts are stored in local currency and USD; account sign convention is normalized for reporting.

## FactFinancialSummary

Monthly entity-BU-scenario KPI-ready grain. Stores revenue, intercompany, gross profit, OPEX, EBITDA, income, cash, operating cash flow, and working capital in USD.

## FactVarianceDriverBridge

Monthly entity-BU variance-driver grain. `amount_usd` ties to Actual EBITDA minus Budget EBITDA by month/entity/BU within $1 tolerance.

## FactCloseExceptions

Close exception register by issue. Tracks owner team, severity, status, amount at risk, due date, and management commentary.

## FactFXRate

Monthly currency-to-USD rates by rate type. Join to `DimDate`; use currency as a lookup attribute when extending the model.
