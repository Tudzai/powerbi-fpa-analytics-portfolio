# Changelog

## v01 - 2026-06-20

- Built Project 20 board/investor CFO synthetic data, semantic model, native layout JSON, preview screenshots, docs and QA scaffolding.

## v06 - 2026-06-20

- Reworked the report closer to the provided ZoomCharts inventory screenshot.
- Added a dark purple left sidebar with visible Year, Scenario, Business Unit, and Region slicers.
- Changed each page to five KPI cards and six rounded chart/table panels.
- Added mini sparklines to Performance and Cash Plan KPI cards.
- Removed memo note boxes, reset placeholder text, KPI chip bars, and header helper text.

## v07 - 2026-06-20

- Brightened the report shell to better match the actual ZoomCharts reference image.
- Changed Year and Scenario to visible sidebar slicers; later tightened all sidebar slicers into compact dropdown controls to reduce clutter.
- Added PY and YoY footer rows to KPI cards for board-style context.
- Preserved native Power BI visuals for portability instead of requiring ZoomCharts PRO custom visuals.

## v08 - 2026-06-20

- Reworked the report with closer detail alignment to the ZoomCharts reference.
- Darkened the purple canvas and changed Power BI outspace to a light neutral.
- Widened the sidebar and rebuilt navigation text to avoid clipping.
- Increased Year and Scenario slicer height and removed the visible Select all row from those list controls.
- Rebuilt KPI cards as layered shell/text/sparkline/footer visuals so metric labels and values no longer wrap or split.

## v09 - 2026-06-20

- Enlarged KPI cards from 112px to 124px and moved chart panels down to keep the grid balanced.
- Rebuilt the KPI mini trend area as a drawn panel with background fill, area columns, stepped trend line, and red/green/current markers to better match the ZoomCharts KPI cards.
- Increased KPI value, PY, and YoY typography and spacing so the cards read like mini KPI dashboards.
- Rechecked Performance, Cash Plan, and Risk & Valuation in Power BI Desktop with screenshots after the final PBIX apply.

## v10 - 2026-06-20

- Tried the official ZoomCharts PBIX download endpoint; it returned account-gated HTML instead of a downloadable PBIX.
- Downloaded the public official preview asset and used it as the template reference.
- Shifted the main content grid from x=200 to x=184 to better match the sample proportions on a 1280x720 canvas.
- Narrowed and shifted KPI mini trend panels right so KPI values remain readable while preserving the sample card structure.

## v20 - 2026-06-20

- Added DAX SVG sparkline measures and status icon/color measures for model-level dashboard decoration.
- Replaced KPI `cardVisual` and mini native `lineChart` objects with stable layered text/shape KPI cards to remove Power BI Desktop authoring overlays.
- Converted the three main trend visuals from line charts to bar/column trend panels to match the ZoomCharts sample more closely and avoid native line chart render errors.
- Added interaction polish: ordered sidebar navigation labels, Board Lens slicer grouping, compact lens subtitles on panels, clearer slicer typography, and semantic YoY coloring for lower-is-better metrics.

## v21 - 2026-06-20

- Added page-level decision chips beside each page title so CFO/board users see the current status before drilling.
- Changed the large hero KPI values from static text into measure-bound card layers so they respond to Year, Scenario, Business Unit, and Region slicers.
- Increased slicer, chart, and table typography for readability while preserving the dense finance-control layout.
- Changed KPI footer wording from `YoY %` to `YoY` because some deltas are points or multiples, not percentages.

## v23 - 2026-06-20

- Rebound all 15 native hero cardVisual layers from string Display measures to numeric compact KPI measures to remove Power BI Desktop render overlays.
- Tightened KPI cards by reducing the mini sparkline footprint, lowering visual noise, and thinning progress bars.
- Added Playwright preview QA for Performance, Cash Plan, and Risk & Valuation; all 15 KPI cards pass value/footer/vertical overflow checks.

## v24 - 2026-06-20

- Reduced each top KPI strip from five cards to four focused cards so the board page reads faster and the right edge no longer feels cramped.
- Changed hero KPI measures to latest-complete-month numeric values, fixing totals like Revenue showing full-period values instead of the current board month.
- Reworked the KPI micro-trend area into a compact canvas sparkline with target band, target line, start marker, anomaly marker, and end marker.
- Ran Playwright overview and individual KPI-card crop QA across all 3 pages / 12 cards, then rechecked the final PBIX in Power BI Desktop.
