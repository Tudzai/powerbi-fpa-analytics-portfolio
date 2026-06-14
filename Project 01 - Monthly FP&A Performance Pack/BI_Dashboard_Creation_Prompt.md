# BI Dashboard Creation Prompt

## Objective

Create a complete Power BI product named **Monthly FP&A Performance Pack** for portfolio demonstration.

The dashboard must look like a polished FP&A management reporting pack, not a generic demo dashboard. It should prioritize important financial indicators, variance analysis, and drill-down views that support monthly business review.

## Required Theme

- Primary theme color: orange.
- Use a clean executive dashboard style.
- Avoid excessive text blocks.
- Avoid commentary paragraphs on the report canvas unless explicitly requested.
- Use white cards, subtle orange borders, light shadows, and dark readable text.
- The dashboard must use space well and should not leave large empty areas on the right side.
- No visual should hide, overlap, or crop data.

## Agent Roles

Use the following agent roles when building the dashboard:

1. **Manager Agent**
   - Define business scope and acceptance criteria.
   - Check if the final dashboard is portfolio-ready.

2. **Data Analyst Agent**
   - Validate data model, KPIs, calculations, and variance logic.
   - Confirm actual vs budget vs forecast comparisons are meaningful.

3. **Power BI Specialist Agent**
   - Build semantic model, relationships, DAX measures, and native Power BI visuals.
   - Ensure PBIX opens correctly and visuals are not static textbox/shape layers.

4. **UI/UX Agent**
   - Improve layout, spacing, visual hierarchy, slicers, and readability.
   - Ensure dashboard looks clean, balanced, and professional.

## Dashboard Pages

### Page 1: Executive KPI

Purpose: give CFO/FP&A leaders a fast view of current performance.

Required visuals:

- KPI cards:
  - Revenue
  - Gross Margin %
  - EBITDA
  - Opex
  - Cash
- 12-month Revenue Trend:
  - Actual Revenue
  - Budget Revenue
  - Forecast Revenue
- EBITDA Variance by Business Unit
- Actual vs Budget vs Forecast table
- Revenue Variance by Region or Product to fill right-side space with useful insight

Required slicers:

- Year
- BU
- Region
- Product

Slicer design:

- Use short labels such as `Year`, `BU`, `Region`, `Product`.
- Turn off duplicate slicer headers if they repeat the title.
- Use dropdown slicers by default.
- If requested, categorical slicers can be changed to horizontal tile/chiclet style.
- If the slicer is date or numeric, use a Between slider.

### Page 2: Variance Bridge

Purpose: explain movement from Budget to Actual.

Required visuals:

- Budget to Actual EBITDA Waterfall Bridge
- Revenue Variance by Product
- Variance Detail table by BU and Region

Metrics:

- Actual Revenue
- Budget Revenue
- Revenue Var vs Budget
- Actual EBITDA
- EBITDA Var vs Budget

### Page 3: Dimension Drilldown

Purpose: allow performance diagnosis by customer, product, and region.

Required visuals:

- Top Customers by Revenue
- Revenue by Region
- EBITDA Variance by Product
- Customer / Product / Region detail table

### Page 4: Opex & Cash

Purpose: monitor cost control, cash balance, and working capital.

Required visuals:

- Actual Opex card
- Budget Opex card
- Cash Balance card
- Cash Variance card
- Weighted DSO card
- Department Opex chart
- Cash Balance Trend
- Cash Detail by Region table

## Data Model Requirements

Use a star schema where possible.

Recommended dimension tables:

- DimDate
- DimScenario
- DimBusinessUnit
- DimProduct
- DimRegion
- DimCustomer
- DimDepartment

Recommended fact tables:

- FactFinancials
- FactOpexDepartment
- FactCash
- FactBridge

Relationships:

- Fact tables should connect to shared dimensions by keys.
- Date, scenario, BU, product, region, customer, and department filters should work where applicable.

## Required Measures

Core measures:

```DAX
Revenue = SUM ( FactFinancials[Revenue] )
COGS = SUM ( FactFinancials[COGS] )
Gross Margin = [Revenue] - [COGS]
Gross Margin % = DIVIDE ( [Gross Margin], [Revenue] )
Allocated Opex = SUM ( FactFinancials[AllocatedOpex] )
EBITDA = [Gross Margin] - [Allocated Opex]
EBITDA % = DIVIDE ( [EBITDA], [Revenue] )
Orders = SUM ( FactFinancials[Orders] )
```

Scenario measures:

```DAX
Actual Revenue = CALCULATE ( [Revenue], DimScenario[Scenario] = "Actual" )
Budget Revenue = CALCULATE ( [Revenue], DimScenario[Scenario] = "Budget" )
Forecast Revenue = CALCULATE ( [Revenue], DimScenario[Scenario] = "Forecast" )

Actual EBITDA = CALCULATE ( [EBITDA], DimScenario[Scenario] = "Actual" )
Budget EBITDA = CALCULATE ( [EBITDA], DimScenario[Scenario] = "Budget" )
Forecast EBITDA = CALCULATE ( [EBITDA], DimScenario[Scenario] = "Forecast" )

Actual Opex = CALCULATE ( [Allocated Opex], DimScenario[Scenario] = "Actual" )
Budget Opex = CALCULATE ( [Allocated Opex], DimScenario[Scenario] = "Budget" )
```

Variance measures:

```DAX
Revenue Var vs Budget = [Actual Revenue] - [Budget Revenue]
Revenue Var % vs Budget = DIVIDE ( [Revenue Var vs Budget], [Budget Revenue] )
EBITDA Var vs Budget = [Actual EBITDA] - [Budget EBITDA]
EBITDA Var % vs Budget = DIVIDE ( [EBITDA Var vs Budget], [Budget EBITDA] )
Opex Var vs Budget = [Actual Opex] - [Budget Opex]
```

Current month measures:

```DAX
Latest Actual DateKey =
CALCULATE (
    MAX ( FactFinancials[DateKey] ),
    DimScenario[Scenario] = "Actual",
    REMOVEFILTERS ( DimDate )
)

Actual Revenue Current Month =
VAR LatestActualDateKey = [Latest Actual DateKey]
RETURN
    CALCULATE (
        [Revenue],
        DimScenario[Scenario] = "Actual",
        DimDate[DateKey] = LatestActualDateKey
    )

Actual EBITDA Current Month =
VAR LatestActualDateKey = [Latest Actual DateKey]
RETURN
    CALCULATE (
        [EBITDA],
        DimScenario[Scenario] = "Actual",
        DimDate[DateKey] = LatestActualDateKey
    )

Actual Cash Balance Current Month =
VAR LatestActualDateKey = [Latest Actual DateKey]
RETURN
    CALCULATE (
        SUM ( FactCash[CashBalance] ),
        DimScenario[Scenario] = "Actual",
        DimDate[DateKey] = LatestActualDateKey
    )
```

## Visual Requirements

- Use native Power BI visuals:
  - Card
  - Slicer
  - Clustered column chart
  - Bar chart
  - Table / matrix
  - Waterfall chart
- Do not build the dashboard from hundreds of textboxes or shape layers.
- Page-title textboxes are allowed.
- Use chart titles and subtitles, but keep them short.
- Avoid long narrative paragraphs.
- Make sure the first page contains enough insight drivers, not only KPI cards.
- Use the right side of the page for driver charts such as:
  - Revenue Variance by Region
  - EBITDA Variance by BU
  - Revenue Variance by Product
  - Top Customers by Revenue

## Layout Requirements

- Canvas: 16:9 Power BI report page.
- KPI cards should be in one clean row.
- Slicers should sit in the top-right area.
- Main trend chart should be the largest visual on Executive page.
- Right-side visual should provide driver insight.
- Bottom section should contain scenario comparison and/or another driver chart.
- Avoid large unused blank space.
- Avoid visual overlap.
- Avoid placing content too close to the right edge if Power BI Desktop edit mode crops the viewport.

## QA Checklist

Before final handoff, verify:

- PBIX opens in Power BI Desktop.
- Power BI package validation passes if available.
- All 4 pages are present.
- KPI cards show real values, not blank or `0.0MM`.
- Cash card uses latest actual month logic.
- Commentary sections are removed unless requested.
- Slicers do not show duplicated labels.
- Right side of dashboard is not empty.
- Visuals do not overlap or crop.
- Report uses native visuals, not static textbox/shape layers.
- Screenshot QA is saved.

## Final Deliverables

Required output files:

- `output/dashboard_final.pbix`
- `output/screenshots/dashboard_final.png`
- `qa/pbix_validation.json`
- `docs/handoff_notes.md`
- `docs/changelog.md`

## Prompt To Use

Copy and paste this prompt when asking an AI agent to build the dashboard:

```text
Build a complete Power BI dashboard product using this specification.

Create a Monthly FP&A Performance Pack with orange theme.
Use native Power BI visuals and a star-schema semantic model.
The dashboard must include Executive KPI, Variance Bridge, Dimension Drilldown, and Opex & Cash pages.

Prioritize important FP&A KPIs:
Revenue, Gross Margin %, EBITDA, Opex, Cash, Budget vs Actual variance, Forecast, DSO, and Cash Balance.

Do not add long commentary sections.
Use the right side of the dashboard for useful driver charts, not blank space.
Make slicers clean, short, and non-duplicated.
Use dropdown slicers by default. For categorical slicer bars, use horizontal tile/chiclet style. For date or numeric slicers, use Between slider.

Validate the PBIX, check KPI DAX results, and provide a screenshot before handoff.
```
