# Semantic Model Notes

The model is a treasury star schema optimized for a 3-tab executive report. KPI measures sit in a dedicated `KPI Measures` table. Important rates and day calculations use DAX measures rather than raw numeric fields.

Design choices:
- Monthly working-capital metrics are separated from invoice-level AR/AP detail.
- 13-week forecast uses weekly grain and scenario dimension.
- FX exposure is a point-in-time risk fact, separate from liquidity and working-capital facts.
- Synthetic data is flagged with `is_synthetic`.
