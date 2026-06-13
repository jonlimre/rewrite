---
name: reconintel
description: Benchmark a NEW reinsurance treaty against Cover Re's in-force portfolio, clause by clause. Extracts the new Contract + I&L into the project's standard 35-clause schema, computes best-in-class wording live from the existing treaties, and produces a focused gap report (HTML + markdown) showing where the new treaty's language falls short of best-in-class so a contracts reviewer knows exactly where to focus. Use when a new treaty PDF arrives and someone asks to benchmark / compare / "recon" it against our book.
---

# reconintel — new-treaty benchmark

This skill takes ONE new reinsurance treaty (lens: the **reinsurer**), scores it against 35
functional clauses, and surfaces every clause whose language is **below best-in-class** in a
portfolio you supply. Best-in-class is computed *live* from the corpus you pass via `--corpus` (an
array of treaty records in the standard schema) — **the skill ships no treaty data of its own**, so
it always benchmarks against whatever book you point it at.

Output goal: a contracts reviewer opens the report and immediately sees the short list of clauses
that aren't comparable to the strongest wording in the book — and the exact best-in-class language to
negotiate toward.

> **Corpus is required.** The skill ships no treaty data, so always pass `--corpus <your portfolio
> JSON>` (an array of treaty records in the standard schema). No `--corpus` → the build exits with a
> clear message rather than guessing.

## Inputs

The user points at the new treaty. Accept any of:
- a folder (ideally a `ReYYYY-NNNN <Cedent> <LOB> <Structure>` folder) containing the Contract +
  I&L PDFs,
- explicit PDF path(s),
- or, if they've already produced a JSON record in the schema, that file (skip to step 4).

If nothing is specified, ask which folder/PDF to benchmark. **Scope = Contract + I&L only** (treaty
wording + economics). UW/authorization forms are out of scope.

## Procedure

### 1. Locate & extract text
- Find the Contract (treaty wording) and the I&L / signature page in the target.
- `pdftotext -layout "<pdf>" "<out>.txt"` each into a temp working dir, e.g.
  `_Comparison Report/text/_incoming/`.
- If a PDF yields ~0 lines it's a scan: read it visually with the Read tool and transcribe the key
  terms into the `.txt` (note it was transcribed). Do not skip scanned economics.

### 2. Extract one JSON record
- Read this skill's `reference/extraction_guide.md` AND your project's rubric calibration file, if you
  have one (the calibration governs the ratings).
- Spawn a `general-purpose` subagent whose prompt is the extraction guide + the extracted text,
  instructing it to emit **exactly one JSON object** in the schema (all 35 clause keys present,
  verbatim excerpts, ratings, notes). For a single contract you may do the extraction inline instead
  of via subagent — either is fine; the guide is the contract.
- `lob` MUST be one of the seven canonical strings (see guide) or peers won't be found.

### 3. Save the record
- Write it to `_Comparison Report/data/_incoming/<ref>.json` (one object). Validate it parses:
  `python -c "import json;json.load(open('<path>',encoding='utf-8'));print('OK')"`.

### 4. Build the benchmark
The builder is **pure-Python, cross-platform, no dependencies** (`build_benchmark.py`). It ships **no
treaty data**, so `--corpus` (your portfolio JSON, array of records in the standard schema) is required:
```
python "${CLAUDE_PLUGIN_ROOT}/skills/reconintel/build/build_benchmark.py" \
  "<path>/<ref>.json" \
  --corpus "<your portfolio>/_data_combined.json"
```
- Best-in-class is recomputed live from the corpus you pass each run (two ways: across the whole book
  and within the new treaty's LOB — see below).
- Outputs (default): `<incoming>/../_benchmarks/<ref>_Benchmark.html` and the matching `.md`. The
  script prints a `RECONINTEL_OK …` line (with `focus=` and `lobfocus=` counts) then the markdown focus
  table to stdout.
- Verify: the stdout starts with `RECONINTEL_OK` and reports `focus=`/`lobfocus=`. If you want to
  eyeball the HTML, it renders in the preview panel; confirm the console logs `RECONINTEL_RENDER_OK`.

### 5. Report to the user
- Lead with the **focus list**: the clauses rated below best-in-class or not addressed, worst
  (🔴) first. Each row carries **two** best-in-class columns — best in book (all LOBs) and best in the
  treaty's own LOB — so call out where the same-LOB ceiling is lower than the absolute ceiling (i.e.
  the realistic negotiation target vs the aspirational one). Paste the markdown focus table.
- Give the one-line headline: favorability score /100, and both counts — "N of 35 below best-in-class
  across the book; M below best-in-class within <LOB>."
- Send/deliver the HTML report (it's the deliverable — focus table on top, full clause matrix below,
  click any cell for verbatim new-vs-both-exemplars wording).
- Offer, but don't do unprompted: fold the new record into the main corpus (drop it in
  `data/<lob>/`, re-merge `_data_combined.json`, rerun the two main builds per `_Comparison Report/CLAUDE.md`).

## How best-in-class & the gap are computed (so you can explain it)

- Each clause rating is normalized first (sunset red→yellow, per calibration).
- Rank: green 3 > yellow 2 > red 1 > n/a 0.
- **Two best-in-class columns are computed per clause:**
  1. **Best in book (all LOBs)** = the highest rank present across the **whole portfolio**, with an
     exemplar treaty (any line of business; the panel labels its LOB when it's cross-LOB).
  2. **Best in <LOB>** = the highest rank present among **same-LOB peers only**, with a same-LOB
     exemplar. If no same-LOB peer rates the clause, the cell shows "no peer".
  The two often differ — the absolute ceiling may sit in another line, while the strongest *comparable*
  wording (the realistic negotiation target) is the same-LOB best.
- **Verdict** per clause is computed **both ways**: vs the whole-book best (drives the **Focus** list
  and the headline `focusCount`) and vs the same-LOB best (`lobFocusCount`, shown as a "vs <LOB>" tag
  and a summary card). Each verdict is `below` (new rank < best), `not_addressed` (new is n/a while
  best > 0), `matches` (equal), or `exceeds` (new beats that benchmark). Focus = below + not_addressed
  against the whole-book best.

## Notes / gotchas
- `build_benchmark.py` is pure standard-library Python (3.8+) — no install needed. It reads JSON as
  UTF-8, writes HTML as UTF-8 **without BOM**, and escapes `</`→`<\/` before injecting.
- The taxonomy (35 keys, labels, sections) is defined identically in `build_benchmark.py`, the
  extraction guide, the main `report_template.html`, and `_Comparison Report/build/build.py`. If a key
  is added to the project, add it in all places.
- This skill never edits existing records or the main deliverables; it only writes under
  `data/_incoming/` and `data/_benchmarks/` unless the user asks to merge.
