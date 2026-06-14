# Semantic Model Notes

- Main fact grain: `fact_payment_month` is monthly merchant x payment method x channel.
- `fact_fee_bridge` supports the fee revenue bridge for the latest month.
- `dim_scenario` is disconnected and drives scenario measures.
- Rates are calculated as DAX measures with `DIVIDE`; no raw rate column should be summed.
- Currency fields are USD for portfolio comparability.
