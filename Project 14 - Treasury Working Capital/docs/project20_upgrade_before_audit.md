# Project 20 Upgrade Before Audit

Audit date: 2026-06-23
Target project: Project 14 - Treasury Working Capital
Project 20 benchmark: Project 20 - Board Investor CFO Pack, v77-style quality standard

## Baseline Read

The upgrade started from a treasury working-capital portfolio project with synthetic demo data, a finance/treasury semantic model, and a Power BI final-output requirement. The Project 20 prompt required preserving the target project identity while raising the craft level: left rail, compact slicers, four KPI cards per page, Current Lens, decision chips, polished chart/table panels, clean z-order, and evidence-backed QA.

## Target Style To Preserve

- Domain story: liquidity, cash forecast, working capital, FX exposure, and treasury risk actioning.
- Visual mood: muted finance palette with teal, blue, green, gold, and rose accents rather than copying Project 20 purple.
- Audience: CFO, Treasurer, and working-capital operators.
- Decision flow: command-center status, AR/AP execution, and forecast/risk monitoring.

## Upgrade Risks Identified

- KPI SVG/image visuals can show placeholders in Power BI Desktop if the image-fit table configuration is wrong.
- Narrow left-rail slicers can clip labels unless kept as compact dropdown controls with external title/header styling.
- Table visuals can look unfinished unless row banding, small typography, header fill, and detail-panel sizing are applied.
- Chart grids can become cluttered if titles/subtitles, units, and z-order are not standardized.

## Final Upgrade Direction

Use Project 20 as a pattern library, not a skin clone. The final Project 14 implementation keeps a treasury cockpit palette and uses dynamic model-bound `tableEx` ImageUrl SVG KPI cards with sparkline bands, markers, PY/delta footer logic, and compact image-fit settings. Lens/chip SVG measures, charts, slicers, and tables remain model-bound in the PBIX.
