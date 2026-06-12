# `pricing_inputs.xlsx` schema

Every field that `pricing.py` reads. Match sheet names and column headers
exactly — `pricing.py` parses them by string.

Accident years (AYs) are always **oldest first**. The oldest AY sits at the
terminal development age; each newer AY moves one step earlier in the
`DevAges` list.

---

## Sheet `latest_data` — required

One row per AY.

| Column | Type | Meaning |
|---|---|---|
| `AccidentYear` | int | The AY (e.g. 2016). |
| `EarnedPremium` | float | Subject earned premium for the AY, currency units. |
| `OnLevelFactor` | float | Multiplier to bring historic premium to current rate level. 1.0 = no adjustment. |
| `PaidLoss` | float | Cumulative paid loss at the AY's current valuation age. |
| `ReportedLoss` | float | Cumulative reported (incurred) loss at the AY's current valuation age. |
| `LossTrend` | float | Annual loss trend in decimal form (0.04 = 4 % / yr). |
| `ExposureTrend` | float | Annual exposure trend in decimal form (0.02 = 2 % / yr). |

## Sheet `ldf_inputs` — required

One row per AY, each cell holds the AY's **current-age-to-next-age** ATA.
For the oldest AY these cells act as tail factors.

| Column | Type | Source |
|---|---|---|
| `AccidentYear` | int | Must match `latest_data`. |
| `UserPaid` | float | User's selected paid ATA. |
| `UserReported` | float | User's selected reported ATA. |
| `IndustryPaid` | float | Industry-benchmark paid ATA. |
| `IndustryReported` | float | Industry-benchmark reported ATA. |
| `BrokerPaid` | float | Broker-supplied paid ATA. |
| `BrokerReported` | float | Broker-supplied reported ATA. |

## Sheet `triangle_paid` — optional

`AccidentYear` in column A; development ages (months) as the rest of row 1.
Cell values are cumulative paid losses. Blank cells beyond the diagonal are
fine.

## Sheet `triangle_reported` — optional

Same shape as `triangle_paid`, with cumulative reported losses.

## Sheet `assumptions` — required

Two columns: `Parameter` and `Value`.

| Parameter | Type | Meaning |
|---|---|---|
| `TargetEffectiveDate` | date | Effective date of the upcoming treaty period. Drives prospective trending. |
| `TailFactor_Paid` | float | Tail factor applied beyond the oldest AY's terminal age, paid basis. |
| `TailFactor_Reported` | float | Tail factor, reported basis. |
| `DevAges` | str | Comma-separated development ages, e.g. `"12,24,36,48,60,72,84,96,108,120"`. Length must equal `len(latest_data)`. |

---

## Constraints `pricing.py` enforces

- `len(DevAges)` should equal the number of AYs; mismatches truncate the
  shorter side and emit a warning.
- Fewer than 3 AYs disables BF a-priori / CC ELR multi-year anchors.
- AY order: oldest → newest, top to bottom.
- If `triangle_*` is omitted, Selected ATAs fall back to `UserPaid` /
  `UserReported`.
