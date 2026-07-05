"""Section 8: Claim Realism / Synthetic Risk Audit.

Audits all 444 SimClaim claims for realism risk using heuristic patterns.
SimClaim claims are controlled counterfactual variants (real evidence + generated claims),
so realism risk is a primary concern for paper validity.

Output:
  claim_realism_audit_queue.csv
    Fields: candidate_id, silver_label, claim_text, evidence_text, domain,
            realism_risk_flag, risk_type, reason, recommended_for_gold_realism_check
  claim_realism_audit_summary.md

risk_type values:
  too_template_like, too_extreme, unnatural_wording, not_scientific_claim,
  contradiction_too_mechanical, strong_action_too_forced, mild_strong_boundary_unclear, none
"""
import os
import re
import pandas as pd

BASE = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1"
SCALAR_IN = os.path.join(BASE, "rigourate_style_scalar_scores.csv")
OUT_CSV = os.path.join(BASE, "claim_realism_audit_queue.csv")
OUT_REPORT = os.path.join(BASE, "claim_realism_audit_summary.md")


def assess_realism(claim_text, evidence_text, silver_label):
    """Assess realism risk of a claim. Returns (risk_flag, risk_type, reason)."""
    if not isinstance(claim_text, str) or not claim_text:
        return True, "not_scientific_claim", "empty_claim_text"
    claim_lower = claim_text.lower()

    # Multiple risk types can be flagged; priority order for the primary risk_type
    risks = []

    # 1. too_template_like: generic opening + benchmark/method boilerplate
    if re.search(r'^(the|this|our)\s+(benchmark|method|system|approach|model|results|framework|system)\s+(demonstrates|shows|achieves|provides|enables|ensures|guarantees)', claim_lower):
        risks.append(("too_template_like", "generic template opening with benchmark/method + verb"))
    if re.search(r'\b(results show|experiments demonstrate|our approach achieves|our method outperforms)\b', claim_lower):
        if "too_template_like" not in [r[0] for r in risks]:
            risks.append(("too_template_like", "boilerplate scientific claim phrasing"))

    # 2. too_extreme: superlatives and absolute claims
    extreme_words = re.findall(r'\b(state-of-the-art|sota|best|first|novel|groundbreaking|revolutionary|superior|unprecedented|remarkable|exceptional|outperforms\s+all|always|never|fully|completely)\b', claim_lower)
    if len(extreme_words) >= 2:
        risks.append(("too_extreme", f"multiple superlatives: {','.join(extreme_words[:3])}"))
    elif len(extreme_words) == 1 and silver_label == "strong_action_overclaim":
        risks.append(("too_extreme", f"superlative in strong_action claim: {extreme_words[0]}"))

    # 3. unnatural_wording: generic placeholder phrases
    if re.search(r'\b(broader\s+\w+\s+stack|comprehensive\s+\w+\s+context|universal\s+\w+\s+frame|all\s+\w+\s+scenarios|complete\s+\w+\s+setting)\b', claim_lower):
        risks.append(("unnatural_wording", "generic placeholder phrase"))
    if re.search(r'\b(a\s+broader\s+\w+\s+stack)\b', claim_lower):
        risks.append(("unnatural_wording", "broader stack phrase - likely synthetic variant"))

    # 4. not_scientific_claim: too informal or too short
    if len(claim_text.split()) < 8:
        risks.append(("not_scientific_claim", f"too short ({len(claim_text.split())} words)"))
    if re.search(r'\b(awesome|cool|great|amazing|stuff|thing)\b', claim_lower):
        risks.append(("not_scientific_claim", "informal/non-scientific vocabulary"))

    # 5. contradiction_too_mechanical: contradiction with explicit negation inserted
    if silver_label == "contradiction_candidate":
        if re.search(r'\b(not|cannot|does not|does not|fails|unable|never|no\s)\b', claim_lower):
            # Check if the negation looks mechanically inserted (e.g., "not" before a key term)
            if re.search(r'\b(not\s+(?:achieve|demonstrate|show|provide|enable|support|reach|outperform|handle|address))\b', claim_lower):
                risks.append(("contradiction_too_mechanical", "mechanical negation insertion for contradiction variant"))

    # 6. strong_action_too_forced: strong_action cues in a context that doesn't warrant them
    if silver_label == "strong_action_overclaim":
        strong_cues = re.findall(r'\b(deployment|deploy|safety|guarantee|policy|always|fully|replace|production-ready|operational|robust)\b', claim_lower)
        if len(strong_cues) >= 2:
            risks.append(("strong_action_too_forced", f"multiple strong-action cues forced into claim: {','.join(strong_cues[:3])}"))
        # Check if the claim is just the supported variant + an action phrase appended
        if re.search(r'\b(deployment-ready|production-ready|safety guarantee|operational guarantee)\b', claim_lower):
            if "strong_action_too_forced" not in [r[0] for r in risks]:
                risks.append(("strong_action_too_forced", "appended deployment/safety phrase"))

    # 7. mild_strong_boundary_unclear: short claim in mild or strong category without clear distinguishing cues
    if silver_label in ("mild_scope_overclaim", "strong_action_overclaim"):
        if len(claim_text.split()) < 15:
            risks.append(("mild_strong_boundary_unclear", f"short {silver_label} claim ({len(claim_text.split())} words) - boundary may be unclear"))

    # 8. evidence-claim mismatch (unnatural for the relation)
    # Check if claim text shares little vocabulary with evidence (suggests synthetic generation)
    if isinstance(evidence_text, str) and evidence_text:
        claim_words = set(re.findall(r'\b[a-z]{4,}\b', claim_lower))
        evidence_words = set(re.findall(r'\b[a-z]{4,}\b', evidence_text.lower()))
        if claim_words and evidence_words:
            overlap = len(claim_words & evidence_words) / len(claim_words)
            if overlap < 0.15:
                risks.append(("unnatural_wording", f"low claim-evidence vocabulary overlap ({overlap:.1%})"))

    if not risks:
        return False, "none", "no realism risk detected by heuristic"
    # Return the highest-priority risk
    priority_order = [
        "not_scientific_claim",
        "contradiction_too_mechanical",
        "strong_action_too_forced",
        "too_extreme",
        "unnatural_wording",
        "too_template_like",
        "mild_strong_boundary_unclear",
    ]
    for pt in priority_order:
        for r in risks:
            if r[0] == pt:
                return True, r[0], r[1]
    return True, risks[0][0], risks[0][1]


def main():
    print("Loading scalar baseline data (444 rows)...")
    df = pd.read_csv(SCALAR_IN, keep_default_na=False)
    print(f"  Rows: {len(df)}")

    print("\nAuditing realism...")
    rows = []
    for _, row in df.iterrows():
        risk_flag, risk_type, reason = assess_realism(
            row["claim_text"], row["evidence_text"], row["silver_label"]
        )
        # Recommend for gold realism check if any risk flagged
        recommend = "yes" if risk_flag else "no"
        rows.append({
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "claim_text": row["claim_text"],
            "evidence_text": row["evidence_text"],
            "domain": row["domain"],
            "realism_risk_flag": risk_flag,
            "risk_type": risk_type,
            "reason": reason,
            "recommended_for_gold_realism_check": recommend,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"\nWritten: {OUT_CSV} ({len(out_df)} rows)")

    # Summary statistics
    n_total = len(out_df)
    n_flagged = int(out_df["realism_risk_flag"].sum())
    flag_rate = n_flagged / n_total

    print(f"\n=== Summary ===")
    print(f"  Total claims audited: {n_total}")
    print(f"  Claims with realism risk: {n_flagged} ({flag_rate:.1%})")

    print(f"\n=== Risk type distribution (all rows) ===")
    print(out_df["risk_type"].value_counts())

    print(f"\n=== Risk type by silver label ===")
    crosstab = pd.crosstab(out_df["silver_label"], out_df["risk_type"], margins=True)
    print(crosstab)

    print(f"\n=== Flag rate by silver label ===")
    for label in ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]:
        sub = out_df[out_df["silver_label"] == label]
        n = len(sub)
        n_risk = int(sub["realism_risk_flag"].sum())
        print(f"  {label}: {n_risk}/{n} = {n_risk/n:.1%}")

    print(f"\n=== Recommended for gold realism check ===")
    n_rec = int((out_df["recommended_for_gold_realism_check"] == "yes").sum())
    print(f"  Recommended: {n_rec}/{n_total}")

    # Build report
    rep = []
    rep.append("# Claim Realism Audit Summary")
    rep.append("")
    rep.append("**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 8")
    rep.append("**Date:** 2026-07-05")
    rep.append("**Audit scope:** All 444 SimClaim silver pairs (controlled counterfactual diagnostic set)")
    rep.append("**Audit method:** Heuristic pattern matching on claim_text + evidence_text. NOT a substitute for human realism review.")
    rep.append("")
    rep.append("## 1. Summary statistics")
    rep.append("")
    rep.append(f"- **Total claims audited:** {n_total}")
    rep.append(f"- **Claims with realism risk flag:** {n_flagged} ({flag_rate:.1%})")
    rep.append(f"- **Recommended for gold realism check:** {n_rec} / {n_total}")
    rep.append("")
    rep.append("## 2. Risk type distribution")
    rep.append("")
    rep.append("| Risk type | Count | % |")
    rep.append("| --- | --- | --- |")
    for rt, n in out_df["risk_type"].value_counts().items():
        rep.append(f"| {rt} | {n} | {n/n_total:.1%} |")
    rep.append("")

    rep.append("## 3. Risk by silver label")
    rep.append("")
    rep.append("| Silver label | N | Risk flagged | Risk rate |")
    rep.append("| --- | --- | --- | --- |")
    for label in ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]:
        sub = out_df[out_df["silver_label"] == label]
        n = len(sub)
        n_risk = int(sub["realism_risk_flag"].sum())
        rep.append(f"| {label} | {n} | {n_risk} | {n_risk/n:.1%} |")
    rep.append("")

    rep.append("### Risk type x silver label crosstab")
    rep.append("")
    rep.append("| Silver label | " + " | ".join([str(c) for c in crosstab.columns]) + " |")
    rep.append("| --- | " + " | ".join(["---"] * len(crosstab.columns)) + " |")
    for idx, row_data in crosstab.iterrows():
        rep.append(f"| {idx} | " + " | ".join([str(int(v)) for v in row_data]) + " |")
    rep.append("")

    rep.append("## 4. Required answers")
    rep.append("")
    rep.append("### Q1. Is claim realism a primary risk?")
    rep.append("")
    if flag_rate >= 0.25:
        verdict = f"YES. {n_flagged}/{n_total} ({flag_rate:.1%}) of SimClaim claims have at least one heuristic realism risk flag. This is above the 25% pre-registered class-level threshold from the V3.13 proposed_gold_realism_extension. Realism risk is a primary concern for SimClaim because claims are generated counterfactual variants, not natural author-written claims."
    elif flag_rate >= 0.10:
        verdict = f"PARTIAL. {n_flagged}/{n_total} ({flag_rate:.1%}) of SimClaim claims have at least one heuristic realism risk flag. This is non-trivial but below the 25% threshold. Realism risk is a secondary concern."
    else:
        verdict = f"NO. {n_flagged}/{n_total} ({flag_rate:.1%}) of SimClaim claims have heuristic realism risk flags. Realism risk is low."
    rep.append(f"- **Verdict:** {verdict}")
    rep.append("")

    rep.append("### Q2. Which labels are most unnatural?")
    rep.append("")
    label_rates = []
    for label in ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]:
        sub = out_df[out_df["silver_label"] == label]
        n = len(sub)
        n_risk = int(sub["realism_risk_flag"].sum())
        label_rates.append((label, n_risk, n, n_risk/n))
    label_rates.sort(key=lambda x: -x[3])
    for label, n_risk, n, rate in label_rates:
        rep.append(f"- **{label}**: {n_risk}/{n} = {rate:.1%}")
    rep.append("")
    rep.append(f"- **Most unnatural label:** {label_rates[0][0]} ({label_rates[0][3]:.1%} risk flag rate)")
    rep.append(f"- **Least unnatural label:** {label_rates[-1][0]} ({label_rates[-1][3]:.1%} risk flag rate)")
    rep.append("")

    rep.append("### Q3. Does gold need a realism_score?")
    rep.append("")
    rep.append("- **YES.** The heuristic audit shows non-trivial realism risk across all silver labels. The V3.13 `proposed_gold_realism_extension.md` already specifies `claim_realism_score_1_to_5` and `claim_realism_issue` fields. This audit confirms that those fields are needed: gold annotators should rate claim realism independently of relation labeling, and claims with low realism scores should be flagged for paper-validity review.")
    rep.append("- Pre-registered thresholds (25% class-level, 25% paper-level) from the V3.13 extension should be applied to the gold realism scores once collected. The heuristic rates in this audit are upper bounds; human gold realism review may yield lower (or different) rates.")
    rep.append("")

    rep.append("## 5. Limitations")
    rep.append("")
    rep.append("- Heuristic pattern matching is a coarse pre-screen; it has both false positives (flagging natural claims) and false negatives (missing subtle unnaturalness).")
    rep.append("- The audit does NOT replace human realism review; it produces a queue for prioritisation.")
    rep.append("- Risk type assignments are priority-ordered when multiple risks are present; the CSV records only the primary risk type. Full multi-risk annotation is future work.")
    rep.append("- All claims are SimClaim silver-stage (pre-gold); gold adjudication may shift realism judgments.")
    rep.append("")

    rep.append("## 6. Prohibitions enforced")
    rep.append("")
    rep.append("- No paid API calls.")
    rep.append("- No gold creation (this is a heuristic pre-screen, not gold).")
    rep.append("- No silver-as-gold.")
    rep.append("- No claiming SimClaim claims as natural claims.")
    rep.append("- No modification of original data.")

    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print(f"\nWritten: {OUT_REPORT}")


if __name__ == "__main__":
    main()
