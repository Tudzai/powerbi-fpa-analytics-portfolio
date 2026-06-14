# Design Research

Sources used:

- [Tableau: Loan Risk Analysis Dashboard](https://www.tableau.com/solutions/gallery/banking-analytics): loan default risk, credit score distribution, risk trends, write-off risk over a 24-month view.
- [Microsoft Learn: Credit and collections management Power BI content](https://learn.microsoft.com/en-us/dynamics365/finance/accounts-receivable/credit-collections-power-bi): collections overview, aged balances, expected payments, write-offs, past-due customers.
- [Microsoft Fabric Community: Credit Risk Analytics Dashboard](https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Credit-Risk-Analytics-Dashboard/m-p/4833815): executive overview, risk matrix, borrower detail, neutral palette with risk colors.
- [ZoomCharts: Credit Risk Analysis Dashboard](https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/credit-risk-analysis-dashboard): Power BI borrower risk overview and portfolio risk exposure patterns.
- [SAS: Credit Risk Dashboard](https://communities.sas.com/t5/SAS-Communities-Library/Credit-Risk-Dashboard-Visualize-loan-performance-delinquency/ta-p/968182): KPI cards, delinquency trends, credit score distribution, filters by loan type and delinquency.
- [ListenData: Credit Risk Vintage Analysis](https://www.listendata.com/2019/09/credit-risk-vintage-analysis.html): origination cohort and MOB vintage analysis.
- [OCC BNPL risk management guidance](https://www.occ.gov/news-issuances/bulletins/2023/bulletin-2023-37.html): BNPL needs early delinquency indicators and low-and-grow exposure monitoring.
- [CFPB BNPL Report 2025](https://files.consumerfinance.gov/f/documents/cfpb_BNPL_Report_2025_01.pdf): borrower segmentation and default context for BNPL users.

Applied design patterns:

- Three-tab workflow: monitor, diagnose, act.
- KPI strip on each tab, with dense finance-style charts below.
- Neutral blue/gray base, with amber/red reserved for risk and green/teal for recovery.
- Early BNPL DPD buckets: 1-7, 8-14, 15-29, 30-59, 60-89, 90+, charge-off.
- Vintage heatmap and roll-rate matrix as the main diagnostic patterns.
- Provision forecast scenario view with base, upside, downside cases.
