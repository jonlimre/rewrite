# rewrite — Reinsurance Underwriting Toolkit

A Claude plugin bundling four reinsurance skills:

| Skill | What it does |
|---|---|
| [`regulr`](skills/regulr/SKILL.md) | **RE**insurance **G**round **U**p **L**oss **R**atio — ingests a reinsurance submission (PDFs, Word, Excel, PowerPoint, images) and produces the cedent's ground-up loss ratio analysis: `pricing_inputs.xlsx`, a formula-driven `pricing_analysis.xlsx`, and a one-page `pricing_report.pdf`. |
| [`reconintel`](skills/reconintel/SKILL.md) | **RE**insurance **CON**tracts **INTEL**ligence — benchmarks a new reinsurance treaty against an in-force portfolio across 35 functional clauses, computing best-in-class wording live from your corpus, and emits a focused gap report (HTML + markdown). |
| [`replace`](skills/replace/SKILL.md) | **RE**insurance **P**roposed **L**etter of **A**uthorization for **C**ommittee **E**valuation — turns a submission plus a stated terms source into a committee-ready package: an email-safe `approval_request.html` (business summary, risk profile with charts, strengths, weaknesses + mitigants, proposed terms) and a branded `authorization_terms.pdf`. |
| [`resus`](skills/resus/SKILL.md) | **RE**insurance re**S**earch **U**nderwriting **S**ubmissions — runs sourced counterparty due diligence on the **cedent, MGA, and TPA** of a submission: entity resolution with a confirmation gate, cited + verified open-web research (financial distress, leadership, partner relationships, litigation, customer reviews, other intel), and an interactive S&P Capital IQ Pro pull (P&C statutory financial highlights + Schedule P loss-ratio reserves, with trend/outlier callouts). Emits a branded `diligence_report.pdf`. |

## Install

### Via plugin marketplace

```
/plugin marketplace add jonlimre/rewrite
/plugin install rewrite@rewrite
```

### One-off (single Claude Code session)

```bash
git clone https://github.com/jonlimre/rewrite.git
claude --plugin-dir ./rewrite
```

## Usage

- **Price a submission:** point Claude at a folder of broker/cedent exhibits and ask to "run regulr" / "price this submission".
- **Benchmark a treaty:** give Claude a new treaty PDF plus your portfolio JSON and ask to "recon" / benchmark it against the book.
- **Prepare a committee authorization:** point Claude at a submission, name where the authorization terms come from, and ask to "run replace" / "draft the authorization request". Produces an email-safe HTML approval request and an authorization-terms PDF.
- **Vet the counterparties:** point Claude at a submission folder (or give the Reference code) and ask to "run resus" / "vet the cedent, MGA and TPA". Resolves each entity (you confirm the matches), runs cited + verified open-web due diligence, pulls S&P Capital IQ financials interactively, and produces a sourced PDF diligence report.

## Layout

```
rewrite/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
└── skills/
    ├── regulr/
    │   ├── SKILL.md
    │   ├── flr/            # actuarial pricing engine (pricing.py)
    │   ├── scripts/        # pricing_inputs.xlsx builder
    │   └── reference/      # schema + extraction hints
    ├── reconintel/
    │   ├── SKILL.md
    │   ├── build/          # pure-stdlib benchmark builder + HTML template
    │   ├── examples/       # sample treaty / portfolio JSON
    │   └── reference/      # extraction guide
    ├── replace/
    │   ├── SKILL.md
    │   ├── scripts/        # email-safe HTML builder + reportlab PDF builder
    │   └── reference/      # terms schema + HTML approval guide
    └── resus/
        ├── SKILL.md
        ├── scripts/        # reportlab PDF builder
        ├── examples/       # sample report spec JSON
        └── reference/      # report schema + research dimensions + S&P playbook
```

## Requirements

Python 3.8+. `reconintel`'s builder and `replace`'s HTML builder are pure
standard library; `regulr`'s engine/input builder and the PDF builders in
`replace` / `resus` use `openpyxl`/`reportlab` (installed on demand). `regulr`
additionally needs `pandas` and the `libreoffice` (or `soffice`) CLI — the CLI
is used only for the PDF leg, which evaluates the analysis workbook's formulas
before reading values. `resus` also uses web search/fetch for research and the
Claude in Chrome MCP for the interactive S&P Capital IQ Pro pull.
