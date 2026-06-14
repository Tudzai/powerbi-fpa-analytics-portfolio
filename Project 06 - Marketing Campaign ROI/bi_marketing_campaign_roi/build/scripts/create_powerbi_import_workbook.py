from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
PREPARED = PROJECT / "data" / "prepared"
OUTPUT = PROJECT / "powerbi" / "marketing_campaign_roi_import.xlsx"

TABLES = {
    "FactCampaignDaily": "fact_campaign_daily.csv",
    "DimDate": "dim_date.csv",
    "DimMonth": "dim_month.csv",
    "DimChannel": "dim_channel.csv",
    "DimCampaign": "dim_campaign.csv",
}


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        for sheet_name, file_name in TABLES.items():
            df = pd.read_csv(PREPARED / file_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            max_row = len(df) + 1
            max_col = len(df.columns)
            if max_row > 1 and max_col > 0:
                from openpyxl.worksheet.table import Table, TableStyleInfo

                end_col = worksheet.cell(row=1, column=max_col).column_letter
                table = Table(
                    displayName=sheet_name,
                    ref=f"A1:{end_col}{max_row}",
                )
                table.tableStyleInfo = TableStyleInfo(
                    name="TableStyleMedium2",
                    showFirstColumn=False,
                    showLastColumn=False,
                    showRowStripes=True,
                    showColumnStripes=False,
                )
                worksheet.add_table(table)

            for column_cells in worksheet.columns:
                header = str(column_cells[0].value or "")
                width = min(max(len(header) + 2, 12), 28)
                worksheet.column_dimensions[column_cells[0].column_letter].width = width

    print(OUTPUT)


if __name__ == "__main__":
    main()
