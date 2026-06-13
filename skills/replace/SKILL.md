---
name: replace
description: Produce a reinsurance authorization-approval package for committee evaluation. Takes a reinsurance submission plus a stated source for the authorization terms and emits (1) an email-safe HTML approval request (business summary, risk profile with inline-SVG charts, strengths, weaknesses + mitigants, proposed terms) and (2) a branded reportlab authorization-terms PDF. Use when the user asks to "run replace", "draft an authorization request", "prepare the committee approval", "write the LOA", or "put together the approval email + terms sheet" for a submission. Produces approval_request.html + authorization_terms.pdf.
argument-hint: "[path-to-submission-folder]"
allowed-tools: Read Glob Grep Bash Skill AskUserQuestion Write
---

# replace — REinsurance Proposed Letter of Authorization for Committee Evaluation

The name expands to **RE**insurance **P**roposed **L**etter of **A**uthorization for
**C**ommittee **E**valuation. The skill turns a reinsurance submission into a
committee-ready approval package:

1. `approval_request.html` — a **standalone, email-safe** approval request the user can
   paste straight into Outlook/Gmail. Inline CSS, inline-SVG charts, HTML tables. **No
   JavaScript, no external assets, no web fonts** (email clients strip all three).
2. `authorization_terms.pdf` — a branded, auto-populated **authorization terms sheet**
   built with `reportlab`. Terms only — no signature/sign-off blocks.

Both documents are branded for **COVER REINSURANCE SPC, LTD. acting on behalf of and for
COVER REINSURANCE SEGREGATED PORTFOLIO #1** (overridable via the spec) and styled to match
**coverre.com**: a warm tan accent (`#C49A6C`), a lowercase `cover re` wordmark (light +
bold), Cormorant-serif display headings (Georgia fallback in email), and Inter/Arial body
text. The HTML email is **light** (white / warm off-white with dark text) so it stays
legible even when Outlook drops cell backgrounds on paste; the PDF pairs a near-black
header band with a light, printable body. Both carry the tan accent and the wordmark.

Bundled assets live under `${CLAUDE_PLUGIN_ROOT}/skills/replace/`:

- `reference/terms_schema.md` — the **field dictionary** for the spec JSON (narrative +
  authorization terms). Read this before populating anything.
- `reference/approval_html_guide.md` — the section structure of the HTML approval request
  and the email-safe inline-SVG chart recipes. Read this before drafting the narrative.
- `scripts/build_approval_html.py` — writes `approval_request.html` from a spec JSON.
- `scripts/build_authorization_pdf.py` — writes `authorization_terms.pdf` from the same
  spec JSON.

## Core principle: draft the narrative, never invent the terms

- The **narrative** (business summary, risk profile, strengths, weaknesses + mitigants,
  noteworthy items) is **drafted by you from the submission** and presented for the user's
  confirmation/editing.
- The **authorization terms** come **only** from the source the user names (a term sheet,
  a slip, a `regulr` pricing output, or values the user states in chat). Never invent a
  term value. Anything missing after extraction is filled with `AskUserQuestion`.

## Step-by-step flow

### 1. Resolve the two sources

You need two things; both come from the user:

- **The submission** — `$1` if set, else attached files, else ask for a folder/path. This
  is the basis for the narrative.
- **The terms source** — ask the user to be explicit about where the authorization terms
  come from if they haven't said. Do not pull terms from the submission silently.

Set `OUT_DIR` to the submission folder unless the user asks for a different output
location.

### 2. Extract content

`Glob` the submission (non-recursive first). For each relevant file, extract with the
matching skill, running independent extractions in parallel:

| Extension | How to extract |
|---|---|
| `.pdf` | `Skill(anthropic-skills:pdf)` |
| `.xlsx` / `.xlsm` / `.xls` / `.csv` | `Skill(anthropic-skills:xlsx)` |
| `.docx` | `Skill(anthropic-skills:docx)` |
| `.pptx` | `Skill(anthropic-skills:pptx)` |
| `.png` / `.jpg` / `.jpeg` | `Read` (multimodal vision) |

Extract the terms source the same way if it is a file.

### 3. Draft the narrative and assemble the terms

Read `reference/approval_html_guide.md` and `reference/terms_schema.md` first.

- **Narrative** — from the submission, draft: a 2–4 sentence business summary; the risk
  profile (geographic mix, class/line-of-business mix, limits/attachment bands, plus any
  other relevant cuts — policy count, average limit, top exposures); strengths; weaknesses
  **each paired with a mitigant** ("why we're okay with it"); and any noteworthy items.
  Every chart needs numeric data — capture it as the arrays documented in the guide.
- **Terms** — pull each field in the schema from the named terms source, recording the
  value AND its source (`file:page` or "user-stated"). For every field, see step 4.

### 4. Apply prefilled defaults; collect required gaps

**Prefilled per house policy (state them in the draft as PREFILLED, let the user override):**

| Field | Default |
|---|---|
| `collateral_factors` | "110% of unpaid loss + 100% of unearned ceded premium net of receivables" |
| `remittance` | "90% to trust / 10% to operating account" |
| `authorization_expiration` | computed at build time as **tomorrow + 7 days** (do not hardcode) |
| `reinsurer` | "COVER REINSURANCE SPC, LTD. acting on behalf of and for COVER REINSURANCE SEGREGATED PORTFOLIO #1" |

**Required — must come from the terms source or the user.** Use `AskUserQuestion` for any
still missing after extraction:

- `cedent`, `reinsurance_broker`
- `term` — effective & expiry dates AND the basis (**RAD** = Risk Attaching During, or
  **LOD** = Losses Occurring During)
- `subject_business` (description) and `subject_premium`
- `share` (the reinsurer's participation %)

**Conditional — include only if relevant; ask if you're unsure whether they apply:**

- `mga`, `premium_caps`
- `ceding_commission` and any `sliding_scale` (provisional, min/max, slide rates by LR)
- `loss_corridor`, `profit_commission`
- `aggregate_cat_cap`, `eco_xpl_cap`, `aggregate_loss_ratio_cap`
- `reporting_requirements`

### 5. Present draft summary — wait for confirmation

Render a markdown summary to the user with: the proposed narrative (headline points), and
every term with its value + source citation, every PREFILLED field flagged, and any
remaining gaps with the resolution route.

End with: **"Confirm to write `approval_request.html` and `authorization_terms.pdf`, or
tell me what to adjust."** Wait for explicit confirmation. Do not write files
speculatively.

### 6. Write the spec and build

Once confirmed:

1. `Write` the spec JSON to `<OUT_DIR>/.replace_spec.json` (shape: see
   `reference/terms_schema.md`).
2. Build the two artifacts:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/replace/scripts/build_approval_html.py" \
     "<OUT_DIR>/.replace_spec.json" "<OUT_DIR>/approval_request.html"

   python "${CLAUDE_PLUGIN_ROOT}/skills/replace/scripts/build_authorization_pdf.py" \
     "<OUT_DIR>/.replace_spec.json" "<OUT_DIR>/authorization_terms.pdf"
   ```

   PowerShell uses the same calls with `$env:CLAUDE_PLUGIN_ROOT`.

The HTML builder is **pure standard-library Python** (no install). The PDF builder needs
`reportlab` (verify before running; install only with the user's permission — `regulr`
already relies on it).

### 7. Report back

Reply with:

- Links to both outputs: `approval_request.html`, `authorization_terms.pdf`.
- A 1–2 sentence headline: cedent / line / share / subject premium and the authorization
  expiration date.
- A reminder that the HTML is email-safe and can be pasted directly into an email; the PDF
  is the attachable terms sheet.

## Guardrails

- **Never invent authorization terms.** If the named source can't supply a required term,
  ask. PREFILLED house defaults are the only values you may supply unasked.
- The HTML must stay **email-safe**: inline CSS only, charts as inline SVG, no `<script>`,
  no external images, no web fonts. The builder enforces this — don't bolt JS charts on.
- There is **no authorization-expiration callout in the HTML**; the expiration lives in the
  PDF terms sheet only.
- Do not overwrite a pre-existing `approval_request.html` / `authorization_terms.pdf` in
  `OUT_DIR` without warning and offering a `.bak` rename.
- If documents disagree on a term, surface both in the draft summary and let the user pick.
- Weaknesses must always be paired with a mitigant — never list a weakness without the
  "why we're okay with it" rationale.
