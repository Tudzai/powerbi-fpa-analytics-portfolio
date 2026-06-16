# Semantic Model Design

The model uses compact synthetic CSV extracts designed for Power BI import. The main analytical grain is monthly emission activity by facility, business unit, supplier when applicable, and activity source.

## Fact Tables

- fact_emissions: primary activity/emissions/spend/revenue fact.
- fact_supplier_month: supplier rollup for intensity ranking and target-risk views.
- fact_carbon_exposure: monthly exposure under three carbon price scenarios.
- fact_abatement_initiatives: initiative-level capex, annual reduction, savings, payback, ROI, and MACC.

## Dimensions

- dim_date
- dim_business_unit
- dim_facility
- dim_activity
- dim_supplier
- dim_carbon_scenario

## Design Rules

- All primary KPIs should use DAX measures.
- Rate measures use DIVIDE.
- Percent/rate columns are not summed.
- Technical keys can be hidden after relationships are created.
