# Metric Definitions

Latest complete month: `2026-05`.

| Metric | Definition |
|---|---|
| GMV | Sum of authorized payment volume before refund and chargeback deductions. |
| Transaction Volume | Count of attempted transactions at monthly merchant-method-channel grain. |
| Revenue | Variable fee revenue plus fixed transaction fees minus modeled refund fee reversals. |
| Take Rate | `Revenue / GMV`. Uses `DIVIDE` in DAX. |
| Variable Cost | Interchange, network, processor, fraud, incentive, and chargeback-related costs. |
| Cost per Transaction | `Variable Cost / Transactions`. |
| Contribution Margin | `Revenue - Variable Cost`. |
| Contribution Margin % | `Contribution Margin / Revenue`. |
| Refund Rate | `Refund Amount / GMV`. |
| Chargeback Bps | `Chargeback Amount / GMV * 10,000`. |
| Auth Success Rate | `Successful Transactions / (Successful + Failed Transactions)`. |
| Scenario Contribution Margin | Scenario revenue less scenario cost using selected take-rate, cost, and volume assumptions. |

Current-month reconciliation: GMV $41.4M, revenue $540.3K, contribution margin $201.9K.
