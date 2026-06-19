# `resus` — research dimensions & verification rules

This is the methodology the open-web research phase follows for **each confirmed entity**
(cedent, MGA, TPA). The output of this phase populates the `dimensions[]` of the report spec.

## The sourcing contract (non-negotiable)

`resus` runs in **strict mode**. Every dimension obeys all of these:

1. **Cite everything.** Each factual claim carries ≥1 source with `title`, `publisher`, `url`,
   and `date`. No URL → it is not a finding, at most an `inference` (labelled as such).
2. **Two sources for negatives.** Any *material adverse* claim (insolvency/distress, fraud,
   sanctions, executive misconduct, litigation outcome, license revocation, partner dispute)
   must have **≥2 independent sources** to be marked `verified`. One source → `single-source`
   and flagged in the report. Two outlets republishing one wire story = **one** source.
3. **Fact vs. inference.** Never assert beyond what a source says. Your own reasoning is
   `assessment: "inference"`, written as such ("This *suggests*…"), never as established fact.
4. **State the negative explicitly.** If a dimension turns up nothing, set
   `nothing_found: true`. The report says "No adverse findings located" — silence is not
   allowed (an empty section reads as "not checked").
5. **No fabrication, ever.** Do not invent a quote, a case number, a figure, a date, or a URL.
   If unsure a source says what you think, fetch and re-read it before citing.
6. **Point-in-time.** Date-stamp the report; findings reflect what was searchable on that day.
7. **Distinguish the entity from look-alikes.** Confirm each finding is about *the resolved
   legal entity*, not a similarly-named company, an affiliate, or an unrelated person. This is
   the most common error — guard against it actively (see Entity resolution below).

## Source quality tiers

Prefer higher tiers; when only a low tier is available, say so in the finding.

| Tier | Sources | Weight |
|---|---|---|
| **Primary / regulatory** | SEC EDGAR filings, NAIC, state DOI (filings, orders, enforcement), court dockets (PACER/CourtListener), official company filings & press releases, rating-agency reports (AM Best, S&P, Moody's, Fitch, KBRA, Demotech) | Strongest; can stand alone for *factual* (non-adverse) claims |
| **Reputable trade / news** | Insurance Insider, Artemis, Reinsurance News, The Insurer, Business Insurance, AM Best News, Reuters, Bloomberg, WSJ, FT, S&P Global Market Intelligence | Strong; two independent of these satisfy the ≥2 rule for negatives |
| **Reviews / forums / low-signal** | Glassdoor, Google/Trustpilot reviews, Reddit, Indeed, anonymous blogs | Use only for `reviews` dimension or as corroboration; never the sole basis for a material adverse claim |

## Entity resolution (Phase 0, before any of the below)

For each of cedent, MGA, TPA, establish a single canonical identity and record it in
`resolved`:

- **Legal name** (full), **domain**, **jurisdiction / HQ**.
- **Regulator identifiers:** for US insurers, the **NAIC company code** (search
  `naic.org` / state DOI lookups). For MGAs/TPAs, the licensing state(s). These pin the entity.
- **Public-company status:** ticker / SEC CIK if listed (drives SEC EDGAR + S&P coverage).
- **Affiliate disambiguation:** insurers often have a same-name *agency/MGA* affiliate (e.g.
  "Meridian Coastal Insurance **Company**" vs "Meridian Coastal Insurance **Agency** LLC"). Note the
  distinction in `resolved.note` so findings don't get cross-attributed.
- Assign `confidence` (High/Medium/Low). Low/Medium matches are exactly what **Gate 1** exists
  to catch — surface them for the user before researching.

Bootstrap hints already available: the deal **folder name** encodes `{Cedent} ({MGA})`, and the
Submissions sheet row gives `Cedent`, `MGA`, `Broker`. The **TPA is usually not captured at
intake** — derive it from the submission documents (slip, program summary, claims-handling
agreement). If no TPA is named, record that and set its flags to `grey`.

## The six dimensions

For each, run a small fan-out of targeted searches (vary the query: legal name, common name,
key executives, "+ lawsuit / insolvency / rating / review"), fetch the promising hits, and
extract findings. Run dimensions/entities in parallel where possible.

**Fold the S&P pull into these dimensions.** The Capital IQ statutory data (see
`sp_capitaliq_playbook.md`) is not a separate silo — each of its five mandatory categories
**feeds a dimension below**, and the decision-relevant figure belongs in that dimension as a
cited finding (`assessment: "single-source"`, S&P as the source), with the full table living in
`sp_financials` as backup. The **"S&P feed"** line under the dimensions below says which
category lands where. Every S&P category is captured or carries a logged reason — don't let one
(Investment Analysis is the easy miss) drop silently.

### 1. `financial_distress` — Financial distress
- Rating actions & outlooks: AM Best, S&P, Moody's, Fitch, KBRA, **Demotech** (common for FL
  carriers) — downgrades, "under review", withdrawals.
- Regulatory financial signals: state DOI orders, RBC/solvency actions, **supervision /
  rehabilitation / liquidation**, NAIC filings, going-concern notes in audited statements.
- Capital & liquidity: raises, distress financing, missed obligations, reserve strengthening,
  adverse development, parent/affiliate stress.
- Public-co signals (if listed): 8-K material events, auditor changes, covenant breaches.
- Reinsurance-specific: trade press on the carrier's reinsurance recoverables, collateral
  disputes, fronting-program collapses.
- **S&P feed:** the core landing spot for statutory data. **P&C Financial Highlights**
  (profitability, ROAE/ROAA, combined ratio, net loss years), **RBC & Capital Adequacy**
  (RBC ratio, leverage, IRIS), **Investments** (asset risk, credit quality / below-IG share,
  yield), and the reserve-adequacy read from **Schedule P** all inform this flag. Cite the
  moving figures here, not just in the `sp_financials` tables.

### 2. `leadership` — Leadership & governance
- Senior leaders (CEO, CUO, CFO, founder, controlling owner) — background, prior failures,
  bans, regulatory orders against them.
- Misconduct: fraud, SEC/DOJ actions, sanctions/OFAC, disbarment, prior insolvencies they ran.
- Governance: rapid C-suite/board churn, auditor/actuary resignations, related-party concerns.
- Reputation: credible investigative reporting (weigh source tier; corroborate negatives).

### 3. `partners` — Partner relationships
- Disputes with reinsurers, fronting carriers, MGAs/MGUs, TPAs, capacity providers.
- Program terminations, non-renewals, capacity pulled, public fallouts.
- Counterparty complaints about claims handling, reporting, or remittance (relevant to the
  cedent↔MGA↔TPA chain in this very submission).
- Collateral / trust / commutation disputes.
- **S&P feed:** **Reinsurance recoverables & relationships** — ceded premium,
  unauthorized (non-US) cession share, recoverables ÷ C&S, and any overdue recoverables. For a
  fronting carrier this is the collateral-adequacy lens (the Vesttoo exposure category); surface
  it as a finding here, not only as a table.

### 4. `litigation` — Litigation (ongoing + settled)
- Court dockets: **CourtListener / PACER**, state court portals. Capture caption, court, case
  number, filing date, status/outcome.
- Regulatory enforcement: DOI market-conduct actions, consent orders, fines.
- Class actions, bad-faith claims-handling suits, coverage disputes, employment suits against
  named executives.
- Distinguish *party* vs *outcome*: "named in a suit" ≠ "found liable". State the status.

### 5. `reviews` — Customer reviews
- Policyholder/agent sentiment: Google, Trustpilot, BBB (rating + complaint volume/patterns),
  state DOI complaint indices.
- Claims-handling reputation (especially for the **TPA**): recurring themes of delay/denial.
- Employee signals: Glassdoor/Indeed for stability/turnover red flags (corroborate; low tier).
- Report **patterns**, not isolated anecdotes; quantify where possible ("BBB: 1.2★, 340
  complaints, 80% claims-related").

### 6. `other` — Other relevant intel
- Ownership/PE backing, M&A, recent restructurings, layoffs, office closures.
- Cyber incidents / data breaches, regulatory probes outside insurance.
- Geographic/LOB concentration risk relevant to this treaty.
- Anything materially useful to an underwriter that doesn't fit the five above.
- **S&P feed:** premium **growth and line-of-business mix** from **P&C Financial Highlights**
  (rapid DPW growth, a shift in mix), and any Schedule P signal that reads as a book-quality
  trend rather than pure reserve adequacy.

## Adversarial verification pass

Before finalizing, re-examine every `red`/`amber` finding with a skeptic's eye:
- Is it the **right entity** (not a namesake/affiliate)? Re-confirm against `resolved`.
- Are the sources **independent**, or one story echoed? Downgrade to `single-source` if echoed.
- Is the claim **current** (not a resolved 2015 matter presented as live)? Date it.
- Could it be **refuted**? If a later source resolves/overturns it, record `assessment:
  "refuted"` and lower the flag.
- Would the finding **survive the user reading the cited source**? If not, fix or drop it.

A finding that can't clear this pass is downgraded or removed — not published on a hunch.
