# reconintel — Extraction & Rating Guide

This is the canonical instruction set for turning ONE new treaty (Contract + I&L) into ONE JSON
record in the project's standard schema. It is fed to the extraction subagent verbatim. The lens is
always **Cover Re as the REINSURER**.

The authoritative rating rules live in
`_Comparison Report/data/_rubric_calibration.md` — read that file too; the summary below is a
convenience copy and the calibration file governs if they ever diverge.

## Output: exactly one JSON object, this schema

```json
{
  "ref": "ReYYYY-NNNN",                         // from folder name, or "INCOMING-<slug>" if unknown
  "program": "<Cedent short name + program>",    // e.g. "Acme Casualty GL"
  "vintage": "2026",                             // treaty year
  "lob": "<one of the 7 LOBs below>",
  "structure": "Quota Share | Excess of Loss | Excess QS",
  "cedent": "<ceding company legal name>",
  "producer": "<broker / intermediary>",
  "effective": "<effective date or term>",
  "economics": {
    "cession_share": "", "ceding_commission": "", "profit_contingent_commission": "",
    "retention_limit": "", "reinsurance_premium": "", "min_deposit_premium": "", "brokerage": ""
  },
  "clauses": {
    "<key>": { "summary": "", "verbatim_excerpt": "", "rating": "green|yellow|red|na", "notes": "" }
  }
}
```

- `summary`: one scannable line (no prose paragraphs).
- `verbatim_excerpt`: the actual contract words that drive the rating (quote, trimmed). This is what
  the reviewer clicks to read — get it right.
- `rating`: favorability to Cover Re. `na` only if the clause genuinely does not exist / does not
  apply to the structure (e.g. reinstatements on a pure QS).
- `notes`: the *why* behind the rating + any open question for the reviewer.

## LOB values (pick one)

`General Liability` · `Commercial Auto` · `Workers' Compensation` · `Homeowners` ·
`Commercial Property` · `Personal Auto` · `Multi-Line`
(If none fit, choose the closest and say so in a top-level note — do not invent a new LOB string,
it must match for benchmarking to find peers.)

## The 35 clause keys (ALL must be present), grouped by section

**Scope & Coverage**
- `business_covered` — classes/lines reinsured. Favorable = narrow, well-defined.
- `reinsuring_coverage_clause` — the grant. Favorable = tightly bounded to defined business.
- `territory` — favorable = defined/limited.
- `special_acceptances` — RED if deemed-consent-on-silence, auto-inheritance of predecessor SAs, or
  lead-binds-all. GREEN if narrow, affirmative written consent only.
- `original_conditions` — follow-form. Favorable = follow-form with clear carve-outs.

**Exclusions**
- `exclusions_general` — RED only for high-severity GAPS: missing PFAS (all books), missing
  communicable disease (all books); habitational also missing abuse/molestation + habitability;
  contractors also missing action-over / labor-law. GREEN = robust modern package, no gap.
- `exclusions_endorsements` — attached endorsements (nuclear, cyber LMA, comm-disease LMA, terror).

**Term & Termination**
- `term_commencement` — commencement & term.
- `special_termination` — triggers. GREEN = strong reinsurer triggers (surplus drop, downgrade,
  control change) intact; RED if the I&L disapplies Cover Re's triggers.
- `runoff_vs_cutoff` — RED if run-off default with long tail, or cut-off is the cedent's sole option.
  GREEN = cut-off default (best-in-class).
- `sunset` — absence = YELLOW where the trust commutes at end of Reporting Period (note as
  mitigation); RED only if no commutation/collateral-release mechanic either. (Render normalizes any
  red here to yellow — rate honestly; the pipeline handles it.)

**Loss Provisions**
- `loss_occurrence_def` — favorable = tight, with hours clause / named-storm aggregation where cat-
  exposed (HO/property: explicit hours clause + named-storm = essential; absence = RED even with a
  per-occurrence cap).
- `losses_lae` — favorable = LAE within limit / capped.
- `ecl_eco` — Loss in Excess of Policy Limits / ECO / XPL. GREEN = tight co-participation or low
  sublimit; RED = full or high/loose sublimit incl. punitive.
- `loss_settlements` — follow-the-fortunes/settlements. RED = "sole judge" + participate-only-at-own-
  expense; GREEN = meaningful claims-cooperation/control rights.
- `salvage_subrogation` — favorable = pro-rata recoveries flow back; flag if inuring reinsurers
  recover first and dilute this layer.
- `aggregate_cat_caps` — hard occurrence/aggregate/LR caps. ~150-175% LR = best-in-class; 225%+ =
  RED; missing per-occurrence CSL cap on trucking/auto = RED; no cat aggregate on a cat book = RED.

**Reporting & Funds Flow**
- `reports_remittances` — cadence + lag. 30-day = GREEN, 45 = YELLOW, longer = RED.
- `account_settlement_timing` — when net balances change hands.
- `funding_collateral` — trust/LOC/funds-withheld. GREEN (best-in-class) = full obligations incl.
  IBNR ~110%, ~90% premium funded in, release only above 102%, segregated-cell recourse. RED = weak
  / release on cedent's sole judgment / IBNR not collateralized.
- `late_payments` — interest on overdue balances. GREEN = present, mutual, defined rate/grace.
- `offset` — GREEN = broad cross-agreement; YELLOW = this-contract-only / intermediary-limited.
- `currency_taxes` — currency + taxes/FET.

**Definitions**
- `key_definitions` — Net Liability, GNEPI/GNWPI, ECO, Loss Occurrence, etc. RED if a definition
  pulls in the MGA's ex-gratia/E&O or otherwise expands Cover Re's exposure.

**Legal / Governance**
- `insolvency` · `arbitration` (seat/panel/rules) · `service_of_suit` · `governing_law` ·
  `access_to_records` · `confidentiality` · `errors_omissions` · `sanctions_clause` (GREEN = standalone
  modern clause; OFAC-only / missing = flag) · `entire_agreement` · `notices_execution` ·
  `intermediary`.

## Rating shorthand

- 🟢 green — protective of Cover Re (tight grant/exclusions, hard caps, cut-off, strong trust, broad
  offset, short lags, real claims control, narrow SA authority).
- 🟡 yellow — standard mutual / market wording.
- 🔴 red — loose / cedent-favorable (uncapped, run-off default or cedent-only cut-off, weak collateral,
  follow-the-settlements "sole judge", broad SA / deemed consent, high-severity exclusion gap, long
  lags). These are the renewal-action items.

Rate honestly and consistently with the corpus. The benchmark step compares this record's ratings AND
wording against the best example of each clause already in the portfolio, so accuracy of both the
`rating` and the `verbatim_excerpt` is what makes the gap report useful.
