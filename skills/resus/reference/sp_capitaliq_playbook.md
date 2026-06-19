# `resus` — S&P Capital IQ Pro pull playbook

S&P Capital IQ Pro is **web-login only** — there is no API key on this account. So the
financials pull is an **interactive, human-in-the-loop** step driven through the **Claude in
Chrome** MCP against the user's already-authenticated browser session. It does **not** run in
unattended/scheduled mode; in those modes, leave `sp_financials.available` unset and complete
it on the user's next interactive run (or ingest a manually-exported tearsheet — see bottom).

## Preconditions (confirm before starting)

- The user is **logged into Capital IQ Pro** in Chrome and the Claude in Chrome extension is
  connected to that tab. If not, ask them to log in first — do not attempt to handle
  credentials or MFA.
- Entity is **resolved and confirmed** (Gate 1 passed). You pull S&P only for confirmed
  entities, using `resolved.legal_name` + `resolved.identifiers` to land on the right company.

## S&P coverage checklist — capture every category, or log why not

For a carrier (the cedent / any risk-bearing entity) **all five categories below are
mandatory.** For each one you either transcribe a table **or** record an explicit reason you
did not — a *silent* omission is a defect, because a missing category reads as "covered and
clean" when it was never looked at. The reason lives in `sp_financials` (a one-line note in
`annual_statement` / `notes`, or a stub table whose `commentary` explains the N/A), exactly the
way Schedule P is marked "NM" for a ~100%-ceding fronting carrier. Before you finish the pull,
walk this list and confirm each row is either a table or a logged reason.

Each category also **feeds a research dimension** — do not leave the figures stranded in the
financials block. Lift the decision-relevant number into a **cited finding inside that
dimension** (`assessment: "single-source"`, S&P as the source), so the narrative and the
statutory table say the same thing. The `sp_financials` tables are the auditable backup; the
dimensions are where the figure actually informs the flag.

| # | S&P category (CIQ page) | Capture | Feeds dimension(s) | Skip only if… |
|---|---|---|---|---|
| 1 | **P&C Financial Highlights** (Financials ▸ U.S. Statutory) | C&S, surplus notes, net admitted assets, DPW/NPW, combined ratio, **ROAE / ROAA / pre-tax operating margin**, net yield, RBC, liquidity ratio; premium growth & mix | `financial_distress` (profitability, capital), `other` (growth, premium mix) | never — mandatory for any carrier |
| 2 | **RBC & Capital Adequacy** (P&C Capital Adequacy) | RBC (TAC/ACL), leverage, liquidity, investment-risk ratios; **NAIC IRIS** if a page exists | `financial_distress` | never — if IRIS is absent at the SNL *group* level, say so rather than omitting silently |
| 3 | **Reinsurance recoverables & relationships** (CIQ: U.S. Reinsurance Relationships / P&C Reinsurance) | ceded premium, **unauthorized (non-US) cession share**, recoverables ÷ C&S, **overdue** recoverables | `partners` (collateral / counterparty risk — the Vesttoo lens), `financial_distress` | never for a cedent / fronting carrier |
| 4 | **Investments** (P&C Investment Analysis) | asset mix (cash/ST vs bonds), net yield, NII trend, **credit quality / below-investment-grade (NAIC 3–6) share**, duration | `financial_distress` (asset risk) | only with a logged reason (e.g. negligible invested assets) |
| 5 | **Schedule P** (U.S. P&C Schedule P) — **LOB-filtered** | incurred + paid loss ratios, reserve development (% of initial, paid-to-ultimate) | `financial_distress` (reserve adequacy), `other` | log "NM — ~100% ceded" for a fronting carrier; lean on the industry-comparison rows instead |

The step-by-step below walks these in detail. The numbering there is ordered for the browser
workflow, not the checklist — what matters is that **every row above ends as a table or a
reason**.

## Step-by-step (per confirmed entity)

1. **Locate the connected tab.** Use the Claude in Chrome MCP (`list_connected_browsers` /
   `select_browser`, then `navigate` / `read_page` / `get_page_text` / `find` /
   `screenshot`). Work in the user's existing authenticated session — never open a fresh
   unauthenticated login flow.
2. **Search the company.** Enter the legal name in Capital IQ's search. If multiple hits,
   disambiguate using `resolved.identifiers` (NAIC code, ticker/CIK, jurisdiction, exact legal
   name). Open the correct entity's page. If you cannot confidently identify the entity, stop
   and ask — do **not** pull the wrong company's financials.
3. **Capture the entity identity.** Record the S&P entity name/ID shown and the page URL —
   this becomes `sp_financials.source_url`. (For an insurer, the **SNL P&C Group** record gives
   consolidated group statutory data; the side menu often has saved **My Links** to the exact
   pages below.)
4. **Pull P&C Financial Highlights (Financials ▸ U.S. Statutory ▸ P&C Financial Highlights).**
   Set the period selector to show **the latest quarter, the latest year-end, and the prior
   year-end** (e.g. FY2024, FY2025, Q1 2026). Transcribe the key rows into an
   `sp_financials.tables` entry (`columns` = the three periods; one `row` per metric). Capture:
   capital & surplus, surplus notes, net admitted assets, direct & net premiums written,
   combined ratio, **ROAE / ROAA / pre-tax operating margin**, net investment yield, **RBC ratio
   (TAC/ACL)**, and a liquidity ratio (cash & ST investments / liabilities). In that table's
   `commentary`, **call out concerning trends or outliers** (a loss year, negative ROE, yield
   compression, a liquidity drop, surplus propped up by debt/surplus notes, rapid premium
   growth).
5. **Pull Schedule P (U.S. P&C Schedule P Reserves) — FILTER TO THE SUBMISSION'S LINE OF
   BUSINESS FIRST.** Schedule P is line-of-business specific. Open the **FILTERS** bar, set
   **Line of Business** to the line being placed (e.g. *Commercial Auto Liability* for a
   commercial-auto program; add *Auto Physical Damage* if relevant), and **Apply Filters** before
   reading anything. Then capture **Incurred Loss Ratios**, **Paid Loss Ratios**, and the
   **reserve development** (the "% of Initial Incurred" column, and the *Reported/Paid to
   Ultimate* pages) into `tables`. Note that for a **fronting carrier** that cedes ~100%, the
   *net* Schedule P loss ratios and reserve development are ~0/NM and not meaningful — the
   program experience sits with reinsurers, so lean on the **industry-comparison** rows (loss-
   ratio level and adverse-development pattern for that line) and compare them to the cedent's
   projected loss pick.
6. **Also pull (standard for a cedent/fronting carrier):**
   - **Reinsurance recoverables / U.S. Reinsurance Relationships** (P&C Reinsurance) — the single
     most important view for a fronting carrier: ceded premium, **unauthorized (non-US) cession
     share**, **recoverables / capital & surplus**, and any **overdue** recoverables (collateral
     adequacy is the key risk — this is where Vesttoo-type exposure lives).
   - **RBC & capital adequacy** (P&C Capital Adequacy) — RBC ratio (TAC/ACL), leverage, liquidity,
     and **investment-risk** ratios (bond quality, junk-bond share). **NAIC IRIS ratios** if a
     page is available (note: IRIS is filed per individual insurer, so it may be absent at the
     SNL *group* level — say so rather than omitting silently).
   - **Investments** (P&C Investment Analysis) — asset mix (cash/ST vs bonds), net yield, net
     investment income trend, credit quality.
   Add each as its own `table` with a `commentary` flagging trends/outliers.
7. **Annual statement & source.** Note the latest statutory annual-statement filing date in
   `annual_statement`. Set `source_url` (the Capital IQ page) and `captured` (today's date) so
   every figure traces back. Where useful, `screenshot` a page and save it to the deal's output
   folder as supporting evidence.

### Capturing a page — extract the DOM with JavaScript (primary method)

**Do not screen-grab the grids row by row.** Each CIQ report renders as real HTML `<table>`
elements inside a **same-origin `/web/client` iframe**, with the *entire* dataset in the DOM
(not canvas, not virtualized). One `javascript_tool` call returns every row exactly — far
faster than paging through screenshots, and with **no transcription error** (screen-grabbing a
dense 11-column triangle is exactly where mis-reads happen).

Run this in the page (via `javascript_tool`) after the report loads:

```js
(() => {
  const ifr = [...document.querySelectorAll('iframe')].find(f => (f.src||'').includes('/web/client'));
  const d = ifr.contentDocument;
  const rowsOf = t => [...t.querySelectorAll('tr')].map(tr =>
    [...tr.querySelectorAll('th,td')].map(c => c.innerText.replace(/\s+/g,' ').trim()));
  const ts = [...d.querySelectorAll('table')];
  // Layout A: label+values in one wide table (loss-ratio / Schedule P pages).
  // Layout B: a 1-column label table + an aligned multi-column value table
  //           (financial-highlights / capital-adequacy / reinsurance / investment pages) — zip by row index.
  const labelT = ts.find(t => { const r = rowsOf(t); return r.length>10 && Math.max(...r.map(x=>x.length),0)===1; });
  const valT   = ts.find(t => { const r = rowsOf(t); return r.length>10 && Math.max(...r.map(x=>x.length),0)>=4; });
  if (labelT && valT) {                          // Layout B
    const L = rowsOf(labelT), V = rowsOf(valT), out = [];
    for (let i=0;i<Math.max(L.length,V.length);i++){ const lab=(L[i]&&L[i][0])||''; const v=V[i]||[]; if(lab && v.some(x=>x!=='')) out.push([lab,...v]); }
    return JSON.stringify(out);
  }
  return JSON.stringify(ts.map(rowsOf).filter(t=>t.length>3));   // Layout A (also returns the industry-comparison table)
})()
```

Notes: set the **Periods** and **Line of Business** filters first (they change what the DOM
holds). Transcribe figures **verbatim** from the returned JSON — keep `NM`/`NA`/`-` as-is.
Screenshots are only a fallback if the iframe isn't same-origin or JS is unavailable; if you do
fall back, click a data cell and press **Page Down** to the bottom (the grid ignores the mouse
wheel), and never resize the window very tall (it can freeze the renderer).

## Accuracy rules (these mirror the strict posture)

- **Transcribe, never estimate.** If a figure isn't visible, leave it out — do not infer or
  round from memory. A missing metric is fine; a wrong one is not.
- **Right entity only.** Cross-check the S&P entity against `resolved` (NAIC/ticker/legal name)
  before recording anything. Same-name affiliates are the trap.
- **Period-label every number.** "$412.3M" is meaningless without "FY2025". Always set
  `period`.
- **No coverage ≠ blank.** If the entity isn't in Capital IQ (common for private MGAs/TPAs),
  set `available: false` and `not_available_reason`, and rely on regulatory/statutory sources
  (state DOI financials, NAIC) noted in the open-web phase instead.
- **No silent category skip.** Within a covered entity, every checklist category above is
  captured as a table or carries an explicit reason it was not (Schedule P "NM — ~100% ceded"
  is the model). Dropping a category without a logged reason — the way Investment Analysis is
  easy to forget — is the defect this checklist exists to prevent.
- **Weave it in.** Each statutory figure that moves a flag also appears as a cited finding in
  the dimension it feeds (per the checklist), not only in the `tables` block. A trend that sits
  unmentioned in the dimension narrative will be missed by a committee reader skimming the flags.
- **Respect the platform.** Pull what's needed for this submission's file; do not bulk-export
  or scrape beyond the deal at hand.

## Fallback: manual export drop

If the interactive pull isn't possible (not logged in, or running unattended), the user can
export the company **tearsheet / financials** from Capital IQ to a file and drop it in the deal
folder. Then ingest it like any submission document (`Skill(anthropic-skills:pdf)` /
`Skill(anthropic-skills:xlsx)`), transcribe the same `metrics[]`, and set `source_url` to
"Capital IQ Pro export (manual)" with the export date as `captured`.
