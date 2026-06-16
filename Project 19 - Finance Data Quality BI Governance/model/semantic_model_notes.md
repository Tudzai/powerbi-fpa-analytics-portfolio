# Semantic Model Notes

The model uses a star schema with shared DimDate, DimDataset, DimReport, and DimDepartment dimensions. Key rates are DAX measures rather than raw numeric fields. Percentage measures use `DIVIDE` to avoid summing rates. Date and numeric columns are explicitly typed in the model.bim M expressions.
