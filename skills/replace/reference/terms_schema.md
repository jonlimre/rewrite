# `replace` spec JSON — field dictionary

Both builders (`build_approval_html.py`, `build_authorization_pdf.py`) read **one** spec
JSON. Write it to `<OUT_DIR>/.replace_spec.json`. UTF-8, no BOM.

Top-level keys: `meta`, `narrative`, `charts`, `terms`. All are objects. Missing optional
fields are simply skipped by the builders — never insert placeholder text like "TBD" to
fill a gap; resolve gaps with the user first (see SKILL.md step 4).

```json
{
  "meta": { ... },
  "narrative": { ... },
  "charts": { ... },
  "terms": { ... }
}
```

## `meta` — document identity

| Key | Req? | Notes |
|---|---|---|
| `reinsurer` | no | Branding line on both docs. Default: `COVER REINSURANCE SPC, LTD. acting on behalf of and for COVER REINSURANCE SEGREGATED PORTFOLIO #1`. |
| `reference` | no | Submission/treaty reference, e.g. `Re2026-0142`. Currently **not displayed** in the header of either document (the "Ref:" line was removed by request); the field is retained for future use. |
| `title` | no | Override the HTML title. Default `Reinsurance Authorization Request`. |
| `prepared_by` | no | Underwriter / preparer name. |
| `date` | no | ISO date string. Default: today (build time). |

## `narrative` — drafted by Claude, confirmed by the user (HTML only)

| Key | Type | Notes |
|---|---|---|
| `recommendation` | string | The ask — 1–3 sentences. Rendered as the lead callout. |
| `business_summary` | string | 2–4 sentences on the cedent/program. |
| `risk_profile_notes` | string | Optional prose introducing the risk-profile section. |
| `strengths` | array of strings | Bulleted. |
| `weaknesses` | array of objects | Each `{"point": "...", "mitigant": "..."}`. **Mitigant is required** — never a weakness without its "why we're okay" rationale. |
| `noteworthy` | array of strings | Optional. Other items the committee should see. |
| `other_metrics` | array of objects | Optional. Each `{"label": "...", "value": "..."}` — rendered as KPI tiles (e.g. policy count, average limit, top state share). |

## `charts` — numeric data for inline-SVG charts (HTML only)

Each chart is an array of `{"label": "...", "value": <number>}`. Values may be percentages
(0–100) or absolute amounts; the builder normalizes bar widths to the max in the series.
Omit a chart entirely (omit the key) if you have no data — never fabricate a distribution.

| Key | Chart | Notes |
|---|---|---|
| `geo` | horizontal bar | Geographic mix (state/region/country). |
| `class` | horizontal bar | Class / line-of-business mix. |
| `limits` | horizontal bar | Limit or attachment bands. |

Recommended: keep each series to ≤ 8 rows; group the long tail into "Other".

## `terms` — authorization terms (HTML proposed-terms table + the whole PDF)

Only `collateral_factors`, `remittance`, `authorization_expiration`, and `reinsurer` may be
auto-supplied. Every other value must come from the user's named terms source.

| Key | Req? | Notes |
|---|---|---|
| `cedent` | yes | Ceding company. |
| `mga` | cond | Include only if an MGA is relevant. |
| `reinsurance_broker` | yes | Intermediary. |
| `term` | yes | Object: `{"basis": "RAD"\|"LOD", "effective": "YYYY-MM-DD", "expiry": "YYYY-MM-DD"}`. `basis` renders as `Risk Attaching During (RAD)` / `Losses Occurring During (LOD)`. |
| `subject_business` | yes | Description of the subject business. |
| `subject_premium` | yes | Subject premium (with currency). |
| `share` | yes | Reinsurer participation, e.g. `25% quota share`. |
| `premium_caps` | cond | Only if applicable. |
| `ceding_commission` | cond | Flat % or provisional %. |
| `sliding_scale` | cond | Either a string, or an array of `{"loss_ratio": "...", "commission": "..."}` rows (rendered as a sub-table). Include `provisional`, `min`, `max` context in the string/rows. |
| `loss_corridor` | cond | e.g. `Cedent retains 100% of losses between 75%–85% LR`. |
| `profit_commission` | cond | e.g. `20% after 15% margin`. |
| `aggregate_cat_cap` | cond | Aggregate catastrophe cap. |
| `eco_xpl_cap` | cond | ECO / XPL (Extra-Contractual Obligations / Excess of Policy Limits) cap. |
| `aggregate_loss_ratio_cap` | cond | Aggregate loss-ratio cap. |
| `reporting_requirements` | cond | Cadence + contents (e.g. `Monthly bordereaux within 30 days; quarterly loss runs`). |
| `collateral_factors` | prefilled | Default: `110% of unpaid loss + 100% of unearned ceded premium net of receivables`. |
| `remittance` | prefilled | Default: `90% to trust account / 10% to operating account`. |
| `authorization_expiration` | prefilled | Use the string `"auto"` to have the PDF builder compute **tomorrow + 7 days** at build time. Or pass an explicit ISO date to override. |

### PDF section grouping

The PDF builder groups `terms` into these sections (a field is shown only if present):

1. **Parties** — cedent, mga, reinsurance_broker
2. **Structure & Term** — term (basis + dates), subject_business, subject_premium, share, premium_caps
3. **Economics** — ceding_commission, sliding_scale, loss_corridor, profit_commission
4. **Caps & Limits** — aggregate_cat_cap, eco_xpl_cap, aggregate_loss_ratio_cap
5. **Collateral & Remittance** — collateral_factors, remittance
6. **Reporting** — reporting_requirements
7. **Authorization** — authorization_expiration
