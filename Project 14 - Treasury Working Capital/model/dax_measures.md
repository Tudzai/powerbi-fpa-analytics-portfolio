# DAX Measures

| Measure | Definition | Format |
|---|---|---|
| Cash Balance | Total book cash balance across bank accounts. | `$#,0` |
| Available Cash | Cash balance net of restricted cash. | `$#,0` |
| Restricted Cash | Restricted bank cash not available for operating liquidity. | `$#,0` |
| Credit Available | Undrawn committed liquidity facilities. | `$#,0` |
| Available Liquidity | Available cash plus undrawn credit facilities. | `$#,0` |
| Minimum Cash Buffer | Entity minimum cash covenant or operating buffer. | `$#,0` |
| Liquidity Headroom | Available liquidity above minimum cash buffer. | `$#,0` |
| AR Outstanding | Open customer receivable balance. | `$#,0` |
| Overdue AR | Open AR balance past due date. | `$#,0` |
| Overdue AR % | Overdue AR as a percentage of total AR outstanding. | `0.0%` |
| AP Outstanding | Open vendor payable balance. | `$#,0` |
| AP Due 14 Days | AP outstanding due in the next 14 days. | `$#,0` |
| Revenue | Monthly revenue used for DSO denominator. | `$#,0` |
| COGS | Monthly cost of goods sold used for DPO and DIO denominators. | `$#,0` |
| Working Capital | AR plus inventory less AP. | `$#,0` |
| DSO | Days sales outstanding, based on AR balance over revenue. | `0.0` |
| DPO | Days payable outstanding, based on AP balance over COGS. | `0.0` |
| DIO | Days inventory outstanding, based on inventory balance over COGS. | `0.0` |
| Cash Conversion Cycle | DSO plus DIO minus DPO. | `0.0` |
| Forecast Closing Cash | Projected closing cash over the selected 13-week forecast scenario. | `$#,0` |
| Forecast Net Cash Flow | Projected cash inflows less outflows. | `$#,0` |
| Forecast Receipts | Forecast customer and other receipts. | `$#,0` |
| Forecast Payments | Forecast supplier, payroll, capex, and debt payments. | `$#,0` |
| Cash Runway Weeks | Available liquidity divided by average weekly cash burn when net flow is negative. | `0.0` |
| Forecast Error % | Absolute forecast error divided by absolute actual net cash flow. | `0.0%` |
| FX Net Exposure | Gross net FX exposure in USD equivalent. | `$#,0` |
| Unhedged FX Exposure | FX exposure remaining after hedge coverage. | `$#,0` |
| Unhedged FX % | Unhedged exposure divided by total net FX exposure. | `0.0%` |
| Open Risk Value | Value attached to non-closed treasury action items. | `$#,0` |
| Open Risk Count | Count of non-closed treasury risk action items. | `#,0` |
