# Power Query Notes

Import prepared CSV files from `data/prepared/`.

Recommended steps:

1. Use Get Data > Text/CSV for each prepared table.
2. Set data types:
   - Date fields as Date.
   - Numeric fields as Decimal Number or Whole Number.
   - IDs, status, category, channel, device as Text.
3. Disable load for raw files if imported for audit only.
4. Load prepared tables only for the report model.
5. Mark `dim_date` as the date table using `dim_date[date]`.
