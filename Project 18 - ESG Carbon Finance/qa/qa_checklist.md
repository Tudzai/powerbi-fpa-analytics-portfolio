# QA Checklist

## Data QA

- [x] Row counts generated.
- [x] Date range validated.
- [x] Critical key nulls checked.
- [x] Duplicate keys checked.
- [x] KPI reconciliation file created.

## Metric QA

- [x] DAX measure definitions created.
- [x] Rates use DIVIDE.
- [x] Reconciliation CSV created.
- [x] Risk/action guardrails reconciled.

## Visual QA

- [x] Native report layout JSON generated.
- [x] Four report pages defined in spec/config.
- [x] v39 patched PBIX opened in Power BI Desktop.
- [x] Visual error count verified as 0 after v39 patch.
- [x] Desktop screenshots refreshed after v39 patch.
- [x] Dynamic table cards tested across default, APAC, EMEA, Scope 3, Logistics, and stress-price states.

## File QA

- [x] output/dashboard_final.pbix exists.
- [x] Exact v39 PBIX opens in Power BI Desktop.
