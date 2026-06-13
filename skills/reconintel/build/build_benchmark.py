#!/usr/bin/env python3
"""reconintel - benchmark ONE new treaty against a portfolio of treaty records (cross-platform).

Best-in-class is computed LIVE from the corpus YOU supply via --corpus (an array of treaty records
in the standard schema), so it always reflects whatever portfolio you point it at. The skill ships
NO treaty data of its own. No third-party dependencies (pure standard library); Windows/macOS/Linux.

    python build_benchmark.py <new_record.json> --corpus <your_portfolio.json>
    python build_benchmark.py <new_record.json> --corpus <your_portfolio.json> --out-html <path>
"""
import json, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
  ("Scope & Coverage", ["business_covered","reinsuring_coverage_clause","territory","special_acceptances","original_conditions"]),
  ("Exclusions", ["exclusions_general","exclusions_endorsements"]),
  ("Term & Termination", ["term_commencement","special_termination","runoff_vs_cutoff","sunset"]),
  ("Loss Provisions", ["loss_occurrence_def","losses_lae","ecl_eco","loss_settlements","salvage_subrogation","aggregate_cat_caps"]),
  ("Reporting & Funds Flow", ["reports_remittances","account_settlement_timing","funding_collateral","late_payments","offset","currency_taxes"]),
  ("Definitions", ["key_definitions"]),
  ("Legal / Governance", ["insolvency","arbitration","service_of_suit","governing_law","access_to_records","confidentiality","errors_omissions","sanctions_clause","entire_agreement","notices_execution","intermediary"]),
]
LBL = {"business_covered":"Business Covered","reinsuring_coverage_clause":"Reinsuring / Coverage","territory":"Territory","special_acceptances":"Special Acceptances","original_conditions":"Original Conditions / Follow-Form","exclusions_general":"General Exclusions","exclusions_endorsements":"Exclusion Endorsements","term_commencement":"Commencement & Term","special_termination":"Special Termination","runoff_vs_cutoff":"Run-off vs Cut-off","sunset":"Sunset","loss_occurrence_def":"Loss / Loss Occurrence Def.","losses_lae":"Losses & LAE","ecl_eco":"Loss in Excess of Policy Limits / ECO","loss_settlements":"Loss Settlements (Follow-the-Fortunes)","salvage_subrogation":"Salvage & Subrogation","aggregate_cat_caps":"Aggregate / Cat / LR Caps","reports_remittances":"Reports & Remittances","account_settlement_timing":"Account Settlement Timing","funding_collateral":"Funding / Collateral","late_payments":"Late Payments","offset":"Offset","currency_taxes":"Currency / Taxes & FET","key_definitions":"Key Definitions","insolvency":"Insolvency","arbitration":"Arbitration","service_of_suit":"Service of Suit","governing_law":"Governing Law","access_to_records":"Access to Records / Audit","confidentiality":"Confidentiality","errors_omissions":"Errors & Omissions / Delays","sanctions_clause":"Sanctions","entire_agreement":"Entire Agreement","notices_execution":"Notices & Execution","intermediary":"Intermediary"}
ECON = [("cession_share","Cover Re Share"),("ceding_commission","Ceding Commission"),("profit_contingent_commission","Profit / Contingent Comm."),("retention_limit","Retention / Limit / Caps"),("reinsurance_premium","Reinsurance Premium"),("min_deposit_premium","Min / Deposit Premium"),("brokerage","Brokerage")]
ALLKEYS = [k for _, keys in SECTIONS for k in keys]

RANK = {"green":3, "yellow":2, "red":1, "na":0}
RANKNAME = {3:"green", 2:"yellow", 1:"red", 0:"na"}

def norm_rating(key, rt):
    rt = (rt or "na").lower()
    if key == "sunset" and rt == "red":
        return "yellow"
    return rt

def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def clause_of(rec, key):
    return (rec.get("clauses") or {}).get(key)

def build(new_path, corpus_path, template_path, out_html, out_md):
    corpus = load_json(corpus_path)
    new = load_json(new_path)
    new_lob = new.get("lob") or ""

    rows = {}
    focus_count = 0
    lob_focus_count = 0
    for key in ALLKEYS:
        ex_all = []
        for t in corpus:
            c = clause_of(t, key)
            rt = norm_rating(key, c.get("rating") if c else None)
            same = (t.get("lob") or "") == new_lob
            rk = RANK[rt]
            if rk > 0:
                ex_all.append({"rank":rk, "rating":rt, "ref":t.get("ref",""), "program":t.get("program",""),
                    "vintage":str(t.get("vintage","")), "structure":t.get("structure",""), "lob":t.get("lob",""),
                    "sameLob":same, "summary":(c.get("summary","") if c else ""),
                    "verbatim":(c.get("verbatim_excerpt","") if c else ""), "notes":(c.get("notes","") if c else "")})
        # best-in-class computed TWO ways: across the whole book, and within the same LOB only
        ex_lob = [e for e in ex_all if e["sameLob"]]
        all_rank = max((e["rank"] for e in ex_all), default=0)
        lob_rank = max((e["rank"] for e in ex_lob), default=0)
        all_ex = [e for e in ex_all if e["rank"] == all_rank][:4]
        lob_ex = [e for e in ex_lob if e["rank"] == lob_rank][:4]

        nc = clause_of(new, key)
        new_rating = norm_rating(key, nc.get("rating") if nc else None)
        new_rank = RANK[new_rating]

        # verdict vs the whole-book best (drives Focus list + headline; unchanged semantics)
        if new_rank == 0 and all_rank > 0:
            verdict = "not_addressed"
        elif new_rank < all_rank:
            verdict = "below"
        elif new_rank == all_rank:
            verdict = "matches"
        else:
            verdict = "exceeds"
        # verdict vs the same-LOB best ("no_peers" when no same-LOB treaty rates this clause)
        if lob_rank == 0:
            lob_verdict = "no_peers"
        elif new_rank == 0:
            lob_verdict = "not_addressed"
        elif new_rank < lob_rank:
            lob_verdict = "below"
        elif new_rank == lob_rank:
            lob_verdict = "matches"
        else:
            lob_verdict = "exceeds"
        if verdict in ("below", "not_addressed"):
            focus_count += 1
        if lob_verdict in ("below", "not_addressed"):
            lob_focus_count += 1

        rows[key] = {"label":LBL[key], "newRating":new_rating,
            "newSummary":(nc.get("summary","") if nc else ""), "newVerbatim":(nc.get("verbatim_excerpt","") if nc else ""),
            "newNotes":(nc.get("notes","") if nc else ""),
            "allBest":{"rating":RANKNAME[all_rank], "exemplars":all_ex},
            "lobBest":{"rating":RANKNAME[lob_rank], "exemplars":lob_ex},
            "verdict":verdict, "lobVerdict":lob_verdict}

    # score the new treaty
    g=y=r=n=0
    for key in ALLKEYS:
        rt = rows[key]["newRating"]
        if rt=="green": g+=1
        elif rt=="yellow": y+=1
        elif rt=="red": r+=1
        else: n+=1
    den = g+y+r
    pct = round((g+0.5*y)/den*100) if den else 0
    lob_peers = sum(1 for t in corpus if (t.get("lob") or "") == new_lob)

    econ_rows = []
    for key, label in ECON:
        econ_rows.append([label, str((new.get("economics") or {}).get(key, "") or "")])

    data = {
        "meta": {"ref":new.get("ref",""), "program":new.get("program",""), "vintage":str(new.get("vintage","")),
            "lob":new_lob, "structure":new.get("structure",""), "cedent":new.get("cedent",""),
            "producer":new.get("producer",""), "effective":new.get("effective",""),
            "corpusCount":len(corpus), "lobPeers":lob_peers, "focusCount":focus_count,
            "lobFocusCount":lob_focus_count,
            "score":{"g":g,"y":y,"r":r,"n":n,"pct":pct}},
        "econ": econ_rows,
        "sections": [{"t":t, "keys":keys} for t, keys in SECTIONS],
        "rows": rows,
    }
    data_js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    with open(template_path, encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("__DATA__", data_js)
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    with open(out_html, "w", encoding="utf-8", newline="") as f:
        f.write(html)

    # markdown focus summary
    order = {"red":0,"na":1,"yellow":2,"green":3}
    lines = []
    lines.append(f"# reconintel benchmark - {new.get('program','')} {new.get('vintage','')}  [{new_lob} / {new.get('structure','')}]")
    lines.append("")
    lob_label = new_lob or "same LOB"
    lines.append(f"Benchmarked against {len(corpus)} treaties ({lob_peers} in same LOB: {lob_label}). "
                 f"Favorability score (Cover Re): {pct}/100  (green {g} | yellow {y} | red {r} | n/a {n}).")
    lines.append(f"FOCUS: {focus_count} of {len(ALLKEYS)} clauses below best-in-class across the book; "
                 f"{lob_focus_count} below best-in-class within {lob_label}.")
    lines.append("")
    lines.append("## Focus areas (below best-in-class across the book / not addressed)")
    lines.append("")
    lines.append(f"| Clause | New | Best (all LOBs) | Best in {lob_label} | Gap |")
    lines.append("|---|---|---|---|---|")

    def ex_label(best):
        exs = best["exemplars"]
        if not exs:
            return "—"
        e0 = exs[0]
        return f"{best['rating']} · {e0['program']} {e0['vintage']}"

    focus = [(key, rows[key]) for key in ALLKEYS if rows[key]["verdict"] in ("below","not_addressed")]
    focus.sort(key=lambda kr: order[kr[1]["newRating"]])
    for key, rw in focus:
        all_cell = ex_label(rw["allBest"])
        lob_cell = ex_label(rw["lobBest"]) if rw["lobBest"]["exemplars"] else f"— (no {lob_label} peer)"
        gap = "not addressed" if rw["verdict"]=="not_addressed" else "below"
        lines.append(f"| {rw['label']} | {rw['newRating']} | {all_cell} | {lob_cell} | {gap} |")
    if not focus:
        lines.append("| (none - meets or beats best-in-class on every clause) | | | | |")
    md = "\n".join(lines) + "\n"
    with open(out_md, "w", encoding="utf-8", newline="") as f:
        f.write(md)

    print(f"RECONINTEL_OK html={out_html} md={out_md} focus={focus_count} lobfocus={lob_focus_count} score={pct} red={r}")
    print()
    print(md)

def main():
    # ensure the markdown we print survives non-UTF-8 consoles (e.g. Windows cp1252)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Benchmark one new treaty against YOUR portfolio of treaty records.")
    ap.add_argument("new_record", help="path to the new treaty JSON (one object)")
    ap.add_argument("--corpus", default="", help="REQUIRED: path to your portfolio JSON (array of treaty records, same schema). The skill ships no treaty data of its own.")
    ap.add_argument("--template", default=os.path.join(HERE, "benchmark_template.html"))
    ap.add_argument("--out-html", default="")
    ap.add_argument("--out-md", default="")
    a = ap.parse_args()

    if not a.corpus:
        sys.exit("ERROR: --corpus is required. Pass --corpus <your portfolio JSON> "
                 "(an array of treaty records in the standard schema). The skill ships no treaty data.")
    corpus = os.path.abspath(a.corpus)
    if not os.path.exists(corpus):
        sys.exit("ERROR: corpus file not found: " + corpus)

    ref = (load_json(a.new_record).get("ref") or "INCOMING")
    slug = "".join(ch if (ch.isalnum() or ch in "_-") else "_" for ch in ref)
    out_html = a.out_html or os.path.join(os.path.dirname(os.path.abspath(a.new_record)), "..", "_benchmarks", slug + "_Benchmark.html")
    out_html = os.path.normpath(out_html)
    out_md = a.out_md or os.path.splitext(out_html)[0] + ".md"
    build(os.path.abspath(a.new_record), corpus, os.path.normpath(a.template), out_html, out_md)

if __name__ == "__main__":
    main()
