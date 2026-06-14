# Metric Definitions

## Funnel Grain

All funnel KPIs are session-based. A session counts once per stage when it reaches that stage. Raw event rows are not summed for funnel conversion.

| KPI | Definition | Format |
|---|---|---|
| Visits | Distinct qualified sessions entering the funnel | Whole number |
| Product View Sessions | Sessions with at least one product view | Whole number |
| Add to Cart Sessions | Sessions with at least one add-to-cart event | Whole number |
| Checkout Sessions | Sessions with checkout start | Whole number |
| Purchase Sessions | Sessions with completed purchase | Whole number |
| Overall Conversion Rate | Purchase Sessions / Visits | Percentage |
| Product View Rate | Product View Sessions / Visits | Percentage |
| Add-to-Cart Rate | Add to Cart Sessions / Product View Sessions | Percentage |
| Checkout Start Rate | Checkout Sessions / Add to Cart Sessions | Percentage |
| Purchase Completion Rate | Purchase Sessions / Checkout Sessions | Percentage |
| Drop-off Sessions | Previous stage sessions - current stage sessions | Whole number |
| Drop-off Rate | Drop-off Sessions / Previous stage sessions | Percentage |
| Revenue | Sum of order net revenue after discount/refund | Currency |
| AOV | Revenue / Orders | Currency |
| Marketing Spend | Sum of campaign spend | Currency |
| ROAS | Revenue / Marketing Spend | Decimal |
| CAC | Marketing Spend / Purchase Sessions | Currency |
