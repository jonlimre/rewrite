# rewrite — Reinsurance Underwriting Toolkit

A Claude plugin bundling two reinsurance skills:

| Skill | What it does |
|---|---|
| [`regulr`](skills/regulr/SKILL.md) | **RE**insurance **G**round **U**p **L**oss **R**atio — ingests a reinsurance submission (PDFs, Word, Excel, PowerPoint, images) and produces the cedent's ground-up loss ratio analysis: `pricing_inputs.xlsx`, a formula-driven `pricing_analysis.xlsx`, and a one-page `pricing_report.pdf`. |
| [`reconintel`](skills/reconintel/SKILL.md) | **RE**insurance **CON**tracts **INTEL**ligence — benchmarks a new reinsurance treaty against an in-force portfolio across 35 functional clauses, computing best-in-class wording live from your corpus, and emits a focused gap report (HTML + markdown). |

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
    └── reconintel/
        ├── SKILL.md
        ├── build/          # pure-stdlib benchmark builder + HTML template
        ├── examples/       # sample treaty / portfolio JSON
        └── reference/      # extraction guide
```

## Requirements

Python 3.8+. `reconintel`'s builder is pure standard library; `regulr`'s
engine and input builder use `openpyxl`/`reportlab` (installed on demand).
