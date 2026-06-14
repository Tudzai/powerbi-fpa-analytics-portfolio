# Aesthetic Redesign Brief: AML / Fraud Monitoring Command Center

## Design Intent

Create a polished Power BI command center for AML, fraud operations, and rule governance users. The report should feel dense, controlled, and audit-ready: a dark monitoring surface with restrained accent colors, high contrast text, compact visual hierarchy, and risk states that stand out only when action is needed.

The visual language should support repeated daily use by compliance leaders, MLROs, fraud operations teams, AML analysts, and the rule governance board. Avoid marketing-style composition, oversized decorative panels, and saturated color floods. The experience should feel like an operational control room: focused, calm, and precise.

## Core Theme

- Canvas: near-black blue charcoal, `#071018`, to create a command-center base without pure black glare.
- Visual surfaces: layered blue-gray panels, `#111B24`, `#162230`, and `#0D1822`, with subtle borders instead of heavy shadows.
- Primary accent: teal, `#2DD4BF`, for selected states, monitoring focus, and positive investigative flow.
- Secondary accents: blue, `#5EA8FF`, for analysis and neutral comparison; violet, `#8B7CF6`, for governance and filed/audited states.
- Risk accents: amber, `#F2B84B`, for watch states and SLA pressure; red, `#F05D5E`, only for critical risk, escalations, overdue breaches, or excessive false positives.
- Text: primary `#E7EDF3`, secondary `#A3B3C5`, muted `#728397`.

## Typography

Use Aptos or Segoe UI as the practical Power BI stack. Keep typography compact:

- Page titles: 18 px, bold.
- Section titles: 12 px, bold, uppercase, muted unless the section is the current analytical focus.
- KPI values: 25 px, bold, high contrast.
- Labels and table text: 9 to 10 px for dense scanability.

Do not use viewport-scaled typography or decorative lettering. The report should look engineered and legible, not editorial.

## Layout System

- Base page size: 1280 x 720.
- Page margin: 24 px.
- Grid: 12 columns, 12 px gutters.
- Header height: 48 px.
- KPI strip height: about 104 px.
- Standard visual gap: 12 px.
- Card radius: 6 px or less.

Use a stable header plus a compact global filter rail. Filters should look integrated into the monitoring surface, not like detached white controls. Reserve the widest center region for trends, funnels, scatter diagnostics, and tables that require comparison.

## Cards and KPIs

KPI cards should be quiet, rectangular, and information-first:

- Dark raised surface with a one-pixel blue-gray border.
- Uppercase label, large value, and a small delta/status line.
- Use teal or green for favorable movement, amber for watch states, red for breach states.
- Avoid icon clutter unless the icon clarifies status or ownership.
- Keep all KPI cards aligned to the same height and value baseline.

## Chart Treatment

- Lines: 2.5 px strokes with small markers only where they aid inspection. Use reference bands for targets or compliance thresholds.
- Bars: descending sort by risk, volume, or operational pressure. Use muted non-focus bars and a single accent for selected or breached categories.
- Donuts: limit to five slices, use a center metric when useful, and do not rely on color alone for severity.
- Scatter: use quadrants for precision versus false-positive rate. Amber and red should identify rules requiring tuning.
- Tables: prioritize evidence. Use compact row height, subtle alternate rows, sticky-looking headers, and status pills for risk/SLA fields.

## Page Composition Guidance

### Fraud & Compliance Overview

This page is the executive monitoring surface. Use a page header with latest complete month, a five-card KPI strip, a wide monthly trend, typology bar, corridor risk table, and severity donut.

Recommended emphasis:

- Exposure, alerts, SAR conversion, false positives, and SLA breach rate in the KPI strip.
- A 12 to 18 month trend as the main center visual.
- Corridor risk and severity distribution on the right side for quick triage.
- Red only for confirmed critical states, not general visual emphasis.

### Alert & Customer Risk Deep Dive

This page should help users decide where to investigate next. Use an alert funnel, rule precision scatter, high-risk customer table, channel quality view, and rule detail panel.

Recommended emphasis:

- Make the alert-to-case funnel clear without making it look like a marketing graphic.
- Use scatter quadrants to separate noisy high-volume rules from high-yield rules.
- Keep customer and rule evidence in tables so analysts can scan IDs, segments, channels, typologies, and next actions.
- Use amber for review pressure and red for true escalation.

### Case SLA & Rule Governance

This page is operational and audit-oriented. Use backlog/status columns, analyst workload, precision/FPR monitoring, and a governance log.

Recommended emphasis:

- Overdue and escalated cases should be visually immediate.
- Analyst workload should use consistent axes so comparisons remain fair.
- Rule precision and FPR should show target lines or reference bands.
- The governance log should include decision, owner, effective date, rationale, and evidence link fields.

## Power BI Implementation Notes

- Preserve the dark page background across all pages and avoid white plot areas.
- Use the top-level theme aliases in `build/config/theme.json` when scripts expect simple keys such as `background`, `surface`, `ink`, `teal`, `amber`, and `red`.
- Use semantic tokens for risk, alert severity, case status, and rule quality when conditional formatting is available.
- Keep visual headers off unless they are needed for export or accessibility.
- Prefer border and spacing hierarchy over heavy shadows.
- Make slicers compact and dark, with selected values using teal accents.

