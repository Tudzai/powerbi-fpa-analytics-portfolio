# Source Inventory

## Source Name

Synthetic ESG Carbon Finance portfolio dataset.

## Location

- Raw synthetic inputs: `data/raw/`
- Prepared Power BI tables: `data/prepared/`
- Validation output: `data/validated/validation_summary.json`

## Owner

Portfolio/demo build owner.

## Refresh Frequency

On demand. Rebuild by running:

```powershell
python build/scripts/build_project18_assets.py
```

## Data Range

January 2024 through May 2026.

## Data Grain

Monthly emission activity record by facility, business unit, supplier where applicable, and activity source.

## Known Limitations

- Synthetic demo data, not production GHG inventory data.
- Emission factors are realistic placeholders, not regulatory-grade factors.
- Supplier target and data-quality statuses are synthetic.
- Carbon price scenarios are illustrative internal planning scenarios.
