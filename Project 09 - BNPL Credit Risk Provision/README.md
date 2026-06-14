# BNPL / Digital Lending Credit Risk Dashboard

This Project 09 - BNPL Credit Risk Provision BI package contains a complete synthetic BNPL credit risk dashboard build.

Key paths:

- `data/raw/`: synthetic source extract.
- `data/prepared/`: prepared star-schema CSV tables.
- `model/`: semantic model, DAX measures, relationship map.
- `build/config/`: dashboard page, visual, slicer, and theme config.
- `build/native_report_layout_project9.json`: native Power BI report layout.
- `powerbi/pbip/Project9_BNPL_Risk/`: Power BI project source package.
- `output/dashboard_preview.html`: supplemental browser preview.
- `output/dashboard_final.pbix`: final target after Power BI Desktop save and package QA.

Rebuild:

```powershell
python .\build\scripts\build_project9.py
```
