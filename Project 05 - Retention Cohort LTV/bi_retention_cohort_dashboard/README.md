# Project 05 - Retention Cohort LTV

This folder contains a complete BI build package for a portfolio Retention & Cohort Dashboard.

Final target: `output/dashboard_final.pbix`

Current status: complete. Power BI Desktop opened the PBIP, refreshed the model, and saved `output/dashboard_final.pbix`.

The project includes synthetic demo data with fixed seed `20260611`, prepared lifecycle tables, metric definitions, DAX measures, relationship map, PBIP source package, visual/page maps, screenshots, PDF/HTML preview, QA artifacts, and rebuild docs.

## Core Pages

1. Lifecycle Overview
2. Monthly Cohort Retention
3. LTV & Revenue Cohorts
4. Churn Signal & Winback

## Rebuild

Run:

```powershell
python build/scripts/01_build_project.py
powershell -ExecutionPolicy Bypass -File build/scripts/00_environment_check.ps1
python build/scripts/03_validate_prepared_data.py
python build/scripts/05_validate_output.py
```
