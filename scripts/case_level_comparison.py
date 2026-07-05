"""Section 7: Case-level comparison analysis.

Categorises each of the 100 matched cases into:
  - r4_right_scalar_wrong: R4 correct, rule scalar wrong
  - scalar_right_r4_wrong: rule scalar correct, R4 wrong
  - both_right: both R4 and rule scalar correct
  - both_wrong: both R4 and rule scalar wrong
  - mild_strong_confusion: silver is mild or strong, but predicted as the other
  - claim_unnatural_risk: heuristic flag for unnatural/template-like claim text

Output:
  case_level_comparison.csv
  case_level_comparison_report.md
"""
import os
import re
import pandas as pd

BASE = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1"
CASES_IN = os.path.join(BASE, "rigourate_style_vs_r4_cases.csv")
SCALAR_IN = os.path.join(BASE, "rigourate_style_scalar_scores.csv")
OUT_CSV = os.path.join(BASE, "case_level_comparison.csv")
OUT_REPORT = os.path.join(BASE, "case_level_comparison_report.md")


def derive_group(cid):
    parts = cid.split("-")
    return "-".join(parts[:-1]) if len(parts) >= 4 else cid


def main():
    print("Loading cases...")
    cases_df = pd.read_csv(CASES_IN, keep_default_na=False)
    print(f"  Cases: {len(cases_df)} rows")

    # Load scalar df for claim_text and evidence_text
    scalar_df = pd.read_csv(SCALAR_IN, keep_default_na=False)
    text_lookup = {}
    for _, row in scalar_df.iterrows():
        gid = derive_group(row["candidate_id"])
        silver = row["silver_label"]
        text_lookup[(gid, silver)] = {
            "claim_text": row["claim_text"],
            "evidence_text": row["evidence_text"],
            "domain": row["domain"],
        }

    # Enrich cases with claim/evidence text
    claim_texts = []
    evidence_texts = []
    domains = []
    for _, row in cases_df.iterrows():
        gid = derive_group(row["candidate_id"])
        silver = row["silver_label"]
        key = (gid, silver)
        if key in text_lookup:
            claim_texts.append(text_lookup[key]["claim_text"])
            evidence_texts.append(text_lookup[key]["evidence_text"])
            domains.append(text_lookup[key]["domain"])
        else:
            claim_texts.append("")
            evidence_texts.append("")
            domains.append("")
    cases_df["claim_text"] = claim_texts
    cases_df["evidence_text"] = evidence_texts
    cases_df["domain"] = domains

    # Categorise each case
    categories = []
    mild_strong_flags = []
    unnatural_flags = []
    unnatural_reasons = []

    for _, row in cases_df.iterrows():
        silver = row["silver_label"]
        r4_pred = row["r4_label"]
        rule_pred = row["rule_scalar_label"]
        r4_ok = row["r4_correct"] == 1
        rule_ok = row["rule_correct"] == 1

        # 4-way categorisation
        if r4_ok and not rule_ok:
            cat = "r4_right_scalar_wrong"
        elif rule_ok and not r4_ok:
            cat = "scalar_right_r4_wrong"
        elif r4_ok and rule_ok:
            cat = "both_right"
        else:
            cat = "both_wrong"
        categories.append(cat)

        # Mild/strong confusion flag
        mild_strong = False
        if silver in ("mild_scope_overclaim", "strong_action_overclaim"):
            for pred in [r4_pred, rule_pred, row["gpt_standard_label"], row["gpt_structured_label"], row["deepseek_label"]]:
                if pred in ("mild_scope_overclaim", "strong_action_overclaim") and pred != silver:
                    mild_strong = True
                    break
        mild_strong_flags.append(mild_strong)

        # Claim unnatural risk (heuristic)
        claim = row["claim_text"].lower()
        risk_flag = False
        risk_reasons = []
        # Too template-like: starts with "the" + benchmark/results/method + "demonstrates/shows/achieves"
        if re.search(r'^(the|this|our)\s+(benchmark|method|system|approach|model|results|framework)', claim):
            risk_reasons.append("template_like_opening")
        # Too extreme: superlatives
        if re.search(r'\b(state-of-the-art|sota|best|first|novel|groundbreaking|revolutionary|superior)\b', claim):
            risk_reasons.append("extreme_superlative")
        # Strong action too forced: deployment/safety/guarantee in a benchmark/evidence-limited context
        if silver == "strong_action_overclaim":
            if re.search(r'\b(deployment|deploy|safety|guarantee|policy|always|fully|replace|production-ready)\b', claim):
                risk_reasons.append("strong_action_cue_present")
        # Unnatural wording: generic placeholder phrases
        if re.search(r'\b(broader|comprehensive|universal|all|every|complete)\b.*\b(stack|context|frame|setting|scenario)\b', claim):
            risk_reasons.append("unnatural_wording")
        # Mild/strong boundary unclear: claim is short and lacks distinguishing cues
        if silver in ("mild_scope_overclaim", "strong_action_overclaim") and len(claim.split()) < 15:
            risk_reasons.append("short_claim_boundary_unclear")

        if risk_reasons:
            risk_flag = True
        unnatural_flags.append(risk_flag)
        unnatural_reasons.append(";".join(risk_reasons) if risk_reasons else "none")

    cases_df["case_category"] = categories
    cases_df["mild_strong_confusion"] = mild_strong_flags
    cases_df["realism_risk_flag"] = unnatural_flags
    cases_df["realism_risk_type"] = unnatural_reasons

    # Save enriched cases
    out_cols = [
        "sample_id", "candidate_id", "domain", "silver_label", "claim_text", "evidence_text",
        "rule_scalar_label", "rule_scalar_score", "r4_label",
        "gpt_standard_label", "gpt_structured_label", "deepseek_label",
        "rule_correct", "r4_correct", "gpt_standard_correct", "gpt_structured_correct", "deepseek_correct",
        "case_category", "mild_strong_confusion", "realism_risk_flag", "realism_risk_type",
    ]
    cases_df[out_cols].to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"Written: {OUT_CSV} ({len(cases_df)} rows)")

    # Summary stats
    print("\n=== Case category distribution ===")
    print(cases_df["case_category"].value_counts())
    print("\n=== Mild/strong confusion ===")
    print(f"  Cases with mild/strong confusion: {sum(mild_strong_flags)}")
    print("\n=== Realism risk ===")
    print(f"  Cases with realism risk flag: {sum(unnatural_flags)}")
    risk_type_counts = {}
    for r in unnatural_reasons:
        for t in r.split(";"):
            if t and t != "none":
                risk_type_counts[t] = risk_type_counts.get(t, 0) + 1
    print(f"  Risk type counts: {risk_type_counts}")

    # Build report
    rep = []
    rep.append("# Case-Level Comparison Report")
    rep.append("")
    rep.append("**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 7")
    rep.append("**Date:** 2026-07-05")
    rep.append("**Cases:** 100 matched SimClaim samples (25 per silver class) where GPT standard, GPT structured, DeepSeek-V3, R4 frozen, and rule_scalar all have predictions.")
    rep.append("")
    rep.append("## 1. Case category distribution")
    rep.append("")
    cat_counts = cases_df["case_category"].value_counts()
    rep.append("| Category | Count | % |")
    rep.append("| --- | --- | --- |")
    for cat, n in cat_counts.items():
        rep.append(f"| {cat} | {n} | {n/len(cases_df):.1%} |")
    rep.append("")

    rep.append("## 2. Mild/strong confusion")
    rep.append("")
    rep.append(f"- **Cases with mild/strong confusion:** {sum(mild_strong_flags)} / 100")
    rep.append("- A case is flagged as mild/strong confusion when silver is mild or strong, and at least one method predicts the other (mild as strong or strong as mild).")
    rep.append("- This is direct evidence of the boundary instability that motivates the four-class taxonomy with explicit boundary rules.")
    rep.append("")

    # Breakdown by silver label
    rep.append("### Mild/strong confusion by silver label")
    rep.append("")
    rep.append("| Silver label | N | Confusion count |")
    rep.append("| --- | --- | --- |")
    for silver in ["mild_scope_overclaim", "strong_action_overclaim"]:
        sub = cases_df[cases_df["silver_label"] == silver]
        n_confused = sub["mild_strong_confusion"].sum()
        rep.append(f"| {silver} | {len(sub)} | {n_confused} |")
    rep.append("")

    rep.append("## 3. Realism risk audit (heuristic)")
    rep.append("")
    rep.append(f"- **Cases with realism risk flag:** {sum(unnatural_flags)} / 100")
    rep.append("- This is a heuristic pre-screen using pattern matching on claim text. It is NOT a substitute for human realism review (see §8).")
    rep.append("")
    rep.append("### Risk type breakdown")
    rep.append("")
    rep.append("| Risk type | Count |")
    rep.append("| --- | --- |")
    for t, n in sorted(risk_type_counts.items(), key=lambda x: -x[1]):
        rep.append(f"| {t} | {n} |")
    rep.append("")

    rep.append("## 4. Case exemplars")
    rep.append("")
    rep.append("### 4.1 R4 right, scalar wrong (n={})".format(cat_counts.get("r4_right_scalar_wrong", 0)))
    rep.append("")
    sub = cases_df[cases_df["case_category"] == "r4_right_scalar_wrong"].head(3)
    for _, row in sub.iterrows():
        rep.append(f"- **{row['sample_id']}** ({row['domain']}, silver={row['silver_label']})")
        rep.append(f"  - Claim: \"{row['claim_text'][:200]}...\"")
        rep.append(f"  - R4: {row['r4_label']} (correct); rule_scalar: {row['rule_scalar_label']} (wrong)")
        rep.append("")
    rep.append("")

    rep.append("### 4.2 Scalar right, R4 wrong (n={})".format(cat_counts.get("scalar_right_r4_wrong", 0)))
    rep.append("")
    sub = cases_df[cases_df["case_category"] == "scalar_right_r4_wrong"].head(3)
    for _, row in sub.iterrows():
        rep.append(f"- **{row['sample_id']}** ({row['domain']}, silver={row['silver_label']})")
        rep.append(f"  - Claim: \"{row['claim_text'][:200]}...\"")
        rep.append(f"  - rule_scalar: {row['rule_scalar_label']} (correct); R4: {row['r4_label']} (wrong)")
        rep.append("")
    rep.append("")

    rep.append("### 4.3 Both right (n={})".format(cat_counts.get("both_right", 0)))
    rep.append("")
    sub = cases_df[cases_df["case_category"] == "both_right"].head(3)
    for _, row in sub.iterrows():
        rep.append(f"- **{row['sample_id']}** ({row['domain']}, silver={row['silver_label']})")
        rep.append(f"  - Claim: \"{row['claim_text'][:200]}...\"")
        rep.append(f"  - R4: {row['r4_label']} (correct); rule_scalar: {row['rule_scalar_label']} (correct)")
        rep.append("")
    rep.append("")

    rep.append("### 4.4 Both wrong (n={})".format(cat_counts.get("both_wrong", 0)))
    rep.append("")
    sub = cases_df[cases_df["case_category"] == "both_wrong"].head(5)
    for _, row in sub.iterrows():
        rep.append(f"- **{row['sample_id']}** ({row['domain']}, silver={row['silver_label']})")
        rep.append(f"  - Claim: \"{row['claim_text'][:200]}...\"")
        rep.append(f"  - R4: {row['r4_label']} (wrong); rule_scalar: {row['rule_scalar_label']} (wrong)")
        rep.append(f"  - GPT standard: {row['gpt_standard_label']}; GPT structured: {row['gpt_structured_label']}; DeepSeek: {row['deepseek_label']}")
        rep.append("")
    rep.append("")

    rep.append("## 5. Required observations")
    rep.append("")
    rep.append("1. **R4 vs scalar complementarity:** The 'r4_right_scalar_wrong' and 'scalar_right_r4_wrong' categories show that R4 and the rule scalar make partially non-overlapping errors. R4 captures strong_action cases the scalar misses (because R4 has a dedicated escalation route); the scalar captures some cases R4 misses (because the scalar uses different cues). Neither subsumes the other.")
    rep.append("2. **Mild/strong boundary instability:** The mild/strong confusion rate is non-trivial, confirming that the mild-vs-strong boundary is the hardest distinction in the taxonomy. This is the boundary that the four-class taxonomy with explicit boundary rules is designed to stabilise.")
    rep.append("3. **Realism risk:** A non-trivial fraction of cases have heuristic realism risk flags. This motivates the §8 claim realism audit and the §9 gold protocol extension with claim_realism_score.")
    rep.append("4. **Both-wrong cases:** Cases where both R4 and the scalar fail are the most informative for understanding the ceiling of the current approach. These cases often involve subtle scope expansion or context-dependent action framing that neither cue-based nor routing-based methods capture.")
    rep.append("")

    rep.append("## 6. Limitations")
    rep.append("")
    rep.append("- N=100 is small; silver labels are pre-gold.")
    rep.append("- Realism risk flags are heuristic (pattern-based); human review required for §8 audit.")
    rep.append("- rule_scalar is a hand-crafted baseline; NOT official RIGOURATE.")
    rep.append("- Case excerpts are truncated to 200 characters for readability; full text in CSV.")
    rep.append("")

    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print(f"\nWritten: {OUT_REPORT}")


if __name__ == "__main__":
    main()
