# Project 17 - Logistics Trade Lane Profitability

Power BI product for logistics and freight profitability by customer, trade lane, service, office, carrier, and shipment profile.

## Main Artifact

- Final PBIX: `output/dashboard_final.pbix`
- Supplemental HTML preview: `output/dashboard_final.html`
- Build route: SCRIPTED_DESKTOP_PBIX using a profitability PBIX seed as a technical container.

## Dashboard Tabs

1. Executive Overview
2. Trade Lane Margin
3. Cost Drivers & Action Queue

## Business Questions

- Which lanes, customers, and services create or destroy margin?
- How do fuel surcharge, carrier cost, demurrage, claims, and utilization affect profitability?
- Which customers should commercial teams reprice or renegotiate?

## Data And Model

- Synthetic portfolio/demo data, seed `17042`.
- Latest complete period `2026-05`.
- Star schema with Date, Customer, Trade Lane, Service, Office, Carrier, Shipment Profitability, Cost Driver Bridge, and Action Queue.
- Measures are documented in `model/MEASURES.dax` and `model/measure_catalog.json`.
