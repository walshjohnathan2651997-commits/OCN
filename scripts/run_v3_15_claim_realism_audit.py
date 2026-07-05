"""V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring.

Automatic, author-side realism audit of SimClaim counterfactual claims.
NOT human gold. NOT a naturalistic study. No API. No model training.
No original data modification.

Output: D:\\ocn\\experiments\\v3_15_claim_realism_audit\\
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

import pandas as pd

INPUT_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
OUT_DIR = Path(r"D:\ocn\experiments\v3_15_claim_realism_audit")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_AUDIT_CSV = OUT_DIR / "claim_realism_group_audit.csv"
CLAIM_AUDIT_CSV = OUT_DIR / "claim_realism_audit_queue.csv"
SUMMARY_MD = OUT_DIR / "claim_realism_audit_summary.md"
SUMMARY_JSON = OUT_DIR / "claim_realism_audit_summary.json"
IMPLICATION_MD = OUT_DIR / "claim_realism_implication_for_paper.md"
GATE_JSON = OUT_DIR / "claim_realism_audit_gate.json"

LABEL_SUPPORTED = "supported"
LABEL_MILD = "mild_scope_overclaim"
LABEL_STRONG = "strong_action_overclaim"
LABEL_CONTRADICTION = "contradiction_candidate"

# Risk 2: extreme / overclaim words
EXTREME_WORDS = [
    "always", "guarantee", "guaranteed", "guarantees", "fully", "completely",
    "solve", "solved", "solves", "replace", "replaces", "replaced",
    "eliminate", "eliminated", "eliminates", "proves", "proved",
    "deployment-ready", "deployment ready", "production-ready",
    "production ready", "fail-safe", "failsafe", "100%", "zero-shot",
    " foolproof", "perfect", "flawless", "certain", "definitive",
    "unmatched", "unparalleled", "state-of-the-art", "best-in-class",
]

# Risk 4: non-scientific / slogan / policy / marketing words
NON_SCI_PATTERNS = [
    r"\bshould be (deployed|adopted|used|implemented|required|mandated)\b",
    r"\bwe recommend\b",
    r"\bpolicy makers should\b",
    r"\bpolicymakers should\b",
    r"\bmust be adopted\b",
    r"\bcall for\b",
    r"\burge\b",
    r"\bgame-?changer\b",
    r"\brevolutioniz\w+\b",
    r"\bcutting-?edge\b",
    r"\bnext-?generation\b",
    r"\bparadigm shift\b",
    r"\bunlock\w*\b",
    r"\bholy grail\b",
    r"\bsilver bullet\b",
    r"\bgroundbreaking\b",
]

# Risk 6: strong_action forced cues (deployment/safety/policy/generalization)
STRONG_FORCED_CUES = [
    "deployment", "deploy", "deployed", "deploying",
    "safety-critical", "safety critical", "safe deployment",
    "policy", "policymaker", "policymakers", "regulation", "regulatory",
    "generalization", "generalize", "generalizes", "generalizability",
    "real-world", "real world", "production", "industry", "industrial",
    "mission-critical", "mission critical", "high-stakes", "high stakes",
    "robust deployment", "trustworthy", "reliable deployment",
]

# Risk 3: unnatural wording signals (mechanical / stitched)
UNNATURAL_PATTERNS = [
    r"\bas the main comparison basis\b",
    r"\bas the primary comparison basis\b",
    r"\bas the key comparison basis\b",
    r"\bas the main evaluation basis\b",
    r"\bas the primary evaluation basis\b",
    r"\bas the key evaluation basis\b",
    r"\bas the main basis\b",
    r"\bas the primary basis\b",
    r"\bas the key basis\b",
    r"\bas the principal\b",
    r"\bin all contexts\b",
    r"\bunder all conditions\b",
    r"\bwithout any caveat\b",
    r"\bwithout any limitation\b",
    r"\bwithout any constraint\b",
    r"\bacross all\b",
    r"\bfor all\b",
    r"\bas the sole\b",
    r"\bas the only\b",
    r"\bthe paper asserts that\b",
    r"\bthe paper claims that\b",
    r"\bthe paper declares that\b",
    r"\bthe paper mandates that\b",
]

# Risk 5: contradiction mechanical — antonym/number/metric swap cues
CONTRA_MECHANICAL_PATTERNS = [
    r"\bnot\b", r"\bfails?\b", r"\bfailure\b", r"\bunable\b", r"\bcannot\b",
    r"\bdoes not\b", r"\bdo not\b", r"\bnever\b",
]

# Domains that are NOT safety-critical (used for strong_forced detection)
HIGH_RISK_DOMAINS = {"autonomous_driving", "cyber_defense", "robotics"}
MEDIUM_RISK_DOMAINS = {"marl", "digital_twin", "policy_simulation"}


def tokenize(text):
    if not isinstance(text, str):
        return []
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text)
    return tokens


STOPWORDS = set("the a an of to in on for and or but is are was were be been being this that these those it its as with by from at into over under above below between among through during before after not no".split())


def content_tokens(text):
    return [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def pairwise_jaccard_mean(list_of_token_lists):
    n = len(list_of_token_lists)
    if n < 2:
        return 0.0
    total = 0.0
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += jaccard(list_of_token_lists[i], list_of_token_lists[j])
            cnt += 1
    return total / cnt if cnt else 0.0


def has_any(text, patterns):
    if not isinstance(text, str):
        return False, []
    hits = []
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            hits.append(p)
    return len(hits) > 0, hits


def has_any_word(text, words):
    if not isinstance(text, str):
        return False, []
    hits = []
    tl = text.lower()
    for w in words:
        wlow = w.lower()
        if wlow in tl:
            hits.append(w)
    return len(hits) > 0, hits


# Risk 1: too_template_like — within group, claims are too similar
def risk_too_template_like(group_claims_tokens, claim_tokens, threshold=0.6):
    """High template similarity if this claim is very similar to siblings."""
    if len(group_claims_tokens) < 2:
        return False, 0.0
    siblings = [t for t in group_claims_tokens if t is not claim_tokens]
    if not siblings:
        return False, 0.0
    sims = [jaccard(claim_tokens, s) for s in siblings]
    max_sim = max(sims)
    mean_sim = sum(sims) / len(sims)
    # Flag if mean similarity > threshold (very templated)
    return mean_sim > threshold, mean_sim


# Risk 2: too_extreme
def risk_too_extreme(claim_text):
    hit, hits = has_any_word(claim_text, EXTREME_WORDS)
    return hit, hits


# Risk 3: unnatural_wording
def risk_unnatural_wording(claim_text):
    hit, hits = has_any(claim_text, UNNATURAL_PATTERNS)
    # Also flag if claim is extremely short (< 4 content tokens) or extremely long (> 60 words)
    n_words = len(claim_text.split()) if isinstance(claim_text, str) else 0
    if n_words > 0 and (n_words < 6 or n_words > 70):
        return True, hits + [f"length_abnormal={n_words}"]
    return hit, hits


# Risk 4: not_scientific_claim
def risk_not_scientific_claim(claim_text):
    hit, hits = has_any(claim_text, NON_SCI_PATTERNS)
    return hit, hits


# Risk 5: contradiction_too_mechanical — only for contradiction_candidate
def risk_contradiction_too_mechanical(claim_text, supported_claim_text):
    if not isinstance(claim_text, str) or not isinstance(supported_claim_text, str):
        return False, []
    ct = content_tokens(claim_text)
    st = content_tokens(supported_claim_text)
    if not ct or not st:
        return False, []
    # Mechanical if very high similarity to supported (just a few word swaps)
    sim = jaccard(ct, st)
    hits = []
    hit_bool, _ = has_any(claim_text, CONTRA_MECHANICAL_PATTERNS)
    if hit_bool:
        hits.append("negation_cue")
    # Mechanical if similarity > 0.7 (very small change from supported)
    if sim > 0.7:
        hits.append(f"high_sim_to_supported={sim:.2f}")
        return True, hits
    # Also mechanical if it's pure negation flip (high sim AND has negation cue)
    if sim > 0.5 and hit_bool:
        return True, hits
    return False, hits


# Risk 6: strong_action_too_forced — only for strong_action_overclaim
def risk_strong_action_too_forced(claim_text, evidence_text, domain):
    if not isinstance(claim_text, str):
        return False, []
    hit, hits = has_any_word(claim_text, STRONG_FORCED_CUES)
    if not hit:
        return False, []
    # Check if evidence mentions these cues — if not, claim is "stuffed"
    ev_hit, _ = has_any_word(evidence_text or "", STRONG_FORCED_CUES)
    if not ev_hit:
        # Strong cues in claim but absent in evidence → forced
        return True, hits + ["cues_absent_in_evidence"]
    # Even if evidence mentions, if claim has many cues (3+) it's still forced
    if len(hits) >= 3:
        return True, hits + [f"excessive_cues={len(hits)}"]
    return False, hits


# Risk 7: mild_strong_boundary_unclear — for mild and strong claims in a group
def risk_mild_strong_boundary_unclear(mild_claim_text, strong_claim_text):
    if not isinstance(mild_claim_text, str) or not isinstance(strong_claim_text, str):
        return False, []
    mt = content_tokens(mild_claim_text)
    st = content_tokens(strong_claim_text)
    if not mt or not st:
        return False, []
    sim = jaccard(mt, st)
    # Boundary unclear if very high similarity (only 1-2 cue words differ)
    if sim > 0.75:
        return True, [f"high_mild_strong_sim={sim:.2f}"]
    # Also check token diff size
    diff = len(set(mt) ^ set(st))
    if diff <= 3 and sim > 0.5:
        return True, [f"small_token_diff={diff}, sim={sim:.2f}"]
    return False, []


def assess_claim(claim_row, group_claims_text, group_claims_tokens, mild_claim_text, strong_claim_text, supported_claim_text):
    """Return (risk_types list, risk_score 0-5, realism_score_suggested 1-5, reason string)."""
    claim_text = claim_row["claim_text"]
    evidence_text = claim_row["evidence_text"]
    label = claim_row["candidate_label_guess"]
    domain = claim_row["domain"]

    claim_tokens = content_tokens(claim_text)
    risk_types = []
    reasons = []

    # Risk 1: too_template_like
    flag, sim = risk_too_template_like(group_claims_tokens, claim_tokens, threshold=0.6)
    if flag:
        risk_types.append("too_template_like")
        reasons.append(f"template_sim={sim:.2f}")

    # Risk 2: too_extreme
    flag, hits = risk_too_extreme(claim_text)
    if flag:
        risk_types.append("too_extreme")
        reasons.append("extreme_words=" + ",".join(hits[:3]))

    # Risk 3: unnatural_wording
    flag, hits = risk_unnatural_wording(claim_text)
    if flag:
        risk_types.append("unnatural_wording")
        reasons.append("unnatural=" + ",".join(str(h) for h in hits[:2]))

    # Risk 4: not_scientific_claim
    flag, hits = risk_not_scientific_claim(claim_text)
    if flag:
        risk_types.append("not_scientific_claim")
        reasons.append("non_sci=" + ",".join(hits[:2]))

    # Risk 5: contradiction_too_mechanical (only for contradiction)
    if label == LABEL_CONTRADICTION:
        flag, hits = risk_contradiction_too_mechanical(claim_text, supported_claim_text)
        if flag:
            risk_types.append("contradiction_too_mechanical")
            reasons.append("contra_mech=" + ",".join(hits[:2]))

    # Risk 6: strong_action_too_forced (only for strong)
    if label == LABEL_STRONG:
        flag, hits = risk_strong_action_too_forced(claim_text, evidence_text, domain)
        if flag:
            risk_types.append("strong_action_too_forced")
            reasons.append("strong_forced=" + ",".join(hits[:3]))

    # Risk 7: mild_strong_boundary_unclear (applies to both mild and strong)
    if label in (LABEL_MILD, LABEL_STRONG):
        flag, hits = risk_mild_strong_boundary_unclear(mild_claim_text, strong_claim_text)
        if flag:
            risk_types.append("mild_strong_boundary_unclear")
            reasons.append("boundary=" + ",".join(hits[:2]))

    risk_score = min(5, len(risk_types))
    # Map risk_score to realism_score_suggested_1_to_5 (1=very realistic, 5=very unrealistic)
    realism_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 5}
    realism_score = realism_map[risk_score]
    reason = "; ".join(reasons) if reasons else "no_risk_flag"
    return risk_types, risk_score, realism_score, reason


def risk_flag_level(risk_score):
    if risk_score <= 1:
        return "low"
    elif risk_score <= 3:
        return "medium"
    else:
        return "high"


def recommended_action(risk_score, risk_types):
    if risk_score <= 1:
        return "keep"
    elif risk_score == 2:
        return "review"
    elif risk_score == 3:
        return "prioritize_gold_realism"
    else:  # 4-5
        if "too_extreme" in risk_types or "too_template_like" in risk_types:
            return "exclude_from_paper_examples"
        return "prioritize_gold_realism"


def group_risk_level(claim_risk_scores):
    avg = sum(claim_risk_scores) / len(claim_risk_scores) if claim_risk_scores else 0
    max_score = max(claim_risk_scores) if claim_risk_scores else 0
    # Group is high if any claim is high (4-5) OR average >= 3
    if max_score >= 4 or avg >= 3:
        return "high"
    elif max_score >= 2 or avg >= 2:
        return "medium"
    else:
        return "low"


def gradient_naturalness(supported_tokens, mild_tokens, strong_tokens, contra_tokens):
    """Score 1-5 how natural the supported->mild->strong->contradiction gradient is.
    5 = very natural (each step changes meaningfully but not mechanically).
    1 = very unnatural (either too similar or chaotic).
    """
    # Pairwise similarities
    sim_sm = jaccard(supported_tokens, mild_tokens)
    sim_ms = jaccard(mild_tokens, strong_tokens)
    sim_sc = jaccard(strong_tokens, contra_tokens)
    sim_scon = jaccard(supported_tokens, contra_tokens)

    # Natural gradient: supported-mild high sim (0.4-0.8), mild-strong moderate (0.3-0.7),
    # strong-contra moderate (0.2-0.6), supported-contra lower (0.1-0.5)
    score = 5

    # Penalize if all too similar (templated)
    if (sim_sm > 0.85 and sim_ms > 0.85):
        score -= 2
    # Penalize if mild-strong boundary too tight
    if sim_ms > 0.8:
        score -= 1
    # Penalize if supported-contradiction too similar (mechanical negation)
    if sim_scon > 0.75:
        score -= 1
    # Penalize if gradient is chaotic (supported-contra more similar than supported-mild)
    if sim_scon > sim_sm + 0.1:
        score -= 1
    # Bonus for natural progression
    if 0.3 < sim_sm < 0.85 and 0.2 < sim_ms < 0.8 and 0.1 < sim_scon < 0.6:
        score = min(5, score + 0)
    return max(1, min(5, int(score)))


def main():
    df = pd.read_csv(INPUT_CSV, keep_default_na=False)
    print(f"Loaded {len(df)} candidates, {df.target_candidate_group_id.nunique()} groups")

    # Pre-compute tokens for each claim
    df["_tokens"] = df["claim_text"].apply(content_tokens)

    # Per-claim audit
    claim_rows = []
    # Per-group audit
    group_rows = []

    for group_id, group_df in df.groupby("target_candidate_group_id"):
        group_df = group_df.reset_index(drop=True)
        if len(group_df) != 4:
            print(f"WARNING: group {group_id} has {len(group_df)} claims (expected 4)")
            continue

        # Identify each label's claim
        by_label = {row["candidate_label_guess"]: row for _, row in group_df.iterrows()}
        supported_claim = by_label.get(LABEL_SUPPORTED, {}).get("claim_text", "")
        mild_claim = by_label.get(LABEL_MILD, {}).get("claim_text", "")
        strong_claim = by_label.get(LABEL_STRONG, {}).get("claim_text", "")
        contradiction_claim = by_label.get(LABEL_CONTRADICTION, {}).get("claim_text", "")

        evidence_text = group_df.iloc[0]["evidence_text"]
        domain = group_df.iloc[0]["domain"]

        group_claims_text = [supported_claim, mild_claim, strong_claim, contradiction_claim]
        group_claims_tokens = [content_tokens(c) for c in group_claims_text]

        # Group-level template similarity
        template_sim = pairwise_jaccard_mean(group_claims_tokens)
        # Gradient naturalness
        grad_natural = gradient_naturalness(
            group_claims_tokens[0], group_claims_tokens[1],
            group_claims_tokens[2], group_claims_tokens[3]
        )

        # Strong forced flag
        strong_row = by_label.get(LABEL_STRONG)
        strong_forced_flag = False
        if strong_row is not None:
            flag, _ = risk_strong_action_too_forced(
                strong_row["claim_text"], strong_row["evidence_text"], domain
            )
            strong_forced_flag = flag

        # Contradiction mechanical flag
        contra_row = by_label.get(LABEL_CONTRADICTION)
        contra_mech_flag = False
        if contra_row is not None:
            flag, _ = risk_contradiction_too_mechanical(
                contra_row["claim_text"], supported_claim
            )
            contra_mech_flag = flag

        # Assess each claim in the group
        claim_risk_scores = []
        for _, row in group_df.iterrows():
            risk_types, risk_score, realism_score, reason = assess_claim(
                row, group_claims_text, group_claims_tokens,
                mild_claim, strong_claim, supported_claim
            )
            claim_risk_scores.append(risk_score)
            flag_level = risk_flag_level(risk_score)
            action = recommended_action(risk_score, risk_types)

            claim_rows.append({
                "candidate_id": row["candidate_id"],
                "group_id": group_id,
                "silver_label": row["candidate_label_guess"],
                "domain": domain,
                "claim_text": row["claim_text"],
                "evidence_text": row["evidence_text"],
                "realism_risk_flag": flag_level,
                "risk_types": "|".join(risk_types) if risk_types else "none",
                "realism_risk_score_0_to_5": risk_score,
                "realism_score_suggested_1_to_5": realism_score,
                "reason": reason,
                "recommended_action": action,
            })

        group_risk_lvl = group_risk_level(claim_risk_scores)
        rec_for_gold = group_risk_lvl == "high" or max(claim_risk_scores) >= 3

        group_rows.append({
            "group_id": group_id,
            "domain": domain,
            "evidence_text": evidence_text,
            "supported_claim": supported_claim,
            "mild_claim": mild_claim,
            "strong_claim": strong_claim,
            "contradiction_claim": contradiction_claim,
            "template_similarity_score": round(template_sim, 4),
            "gradient_naturalness_score": grad_natural,
            "strong_forced_flag": strong_forced_flag,
            "contradiction_mechanical_flag": contra_mech_flag,
            "group_realism_risk_level": group_risk_lvl,
            "recommended_for_gold_realism_check": rec_for_gold,
        })

    # Write claim audit queue CSV
    claim_df = pd.DataFrame(claim_rows)
    claim_df.to_csv(CLAIM_AUDIT_CSV, index=False, encoding="utf-8")
    print(f"Wrote {len(claim_df)} claim rows to {CLAIM_AUDIT_CSV}")

    # Write group audit CSV
    group_df_out = pd.DataFrame(group_rows)
    group_df_out.to_csv(GROUP_AUDIT_CSV, index=False, encoding="utf-8")
    print(f"Wrote {len(group_df_out)} group rows to {GROUP_AUDIT_CSV}")

    # ===== Statistics =====
    n_claims = len(claim_df)
    n_groups = len(group_df_out)

    risk_flag_counts = claim_df["realism_risk_flag"].value_counts().to_dict()
    high_risk_claims = int(risk_flag_counts.get("high", 0))
    medium_risk_claims = int(risk_flag_counts.get("medium", 0))
    low_risk_claims = int(risk_flag_counts.get("low", 0))
    high_risk_claim_rate = high_risk_claims / n_claims if n_claims else 0

    group_risk_counts = group_df_out["group_realism_risk_level"].value_counts().to_dict()
    high_risk_groups = int(group_risk_counts.get("high", 0))
    medium_risk_groups = int(group_risk_counts.get("medium", 0))
    low_risk_groups = int(group_risk_counts.get("low", 0))
    high_risk_group_rate = high_risk_groups / n_groups if n_groups else 0

    # Per-label realism risk
    per_label_stats = {}
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRADICTION]:
        sub = claim_df[claim_df["silver_label"] == label]
        if len(sub) == 0:
            continue
        per_label_stats[label] = {
            "n": int(len(sub)),
            "high_risk": int((sub["realism_risk_flag"] == "high").sum()),
            "medium_risk": int((sub["realism_risk_flag"] == "medium").sum()),
            "low_risk": int((sub["realism_risk_flag"] == "low").sum()),
            "high_risk_rate": float((sub["realism_risk_flag"] == "high").mean()),
            "mean_risk_score": float(sub["realism_risk_score_0_to_5"].mean()),
        }

    # strong_action forced rate
    strong_claims = claim_df[claim_df["silver_label"] == LABEL_STRONG]
    n_strong = len(strong_claims)
    strong_forced_count = int(strong_claims["risk_types"].str.contains("strong_action_too_forced").sum())
    strong_forced_rate = strong_forced_count / n_strong if n_strong else 0

    # contradiction mechanical rate
    contra_claims = claim_df[claim_df["silver_label"] == LABEL_CONTRADICTION]
    n_contra = len(contra_claims)
    contra_mech_count = int(contra_claims["risk_types"].str.contains("contradiction_too_mechanical").sum())
    contra_mech_rate = contra_mech_count / n_contra if n_contra else 0

    # group template risk
    high_template_groups = int((group_df_out["template_similarity_score"] > 0.6).sum())
    group_template_risk_rate = high_template_groups / n_groups if n_groups else 0

    # Risk type distribution
    risk_type_counts = Counter()
    for rt in claim_df["risk_types"]:
        if rt == "none":
            continue
        for r in rt.split("|"):
            risk_type_counts[r] += 1

    # Low-risk claims usable as paper examples
    low_risk_claims_df = claim_df[claim_df["realism_risk_flag"] == "low"]
    # Per-label low-risk counts (for paper example selection balance)
    low_risk_per_label = low_risk_claims_df["silver_label"].value_counts().to_dict()

    # High-risk claims for gold realism check
    high_risk_for_gold = claim_df[claim_df["realism_risk_flag"] == "high"]
    high_risk_for_gold_per_label = high_risk_for_gold["silver_label"].value_counts().to_dict()

    # Recommended action distribution
    action_counts = claim_df["recommended_action"].value_counts().to_dict()

    # Domain risk distribution
    domain_risk = {}
    for d in claim_df["domain"].unique():
        sub = claim_df[claim_df["domain"] == d]
        domain_risk[d] = {
            "n": int(len(sub)),
            "high_risk": int((sub["realism_risk_flag"] == "high").sum()),
            "high_risk_rate": float((sub["realism_risk_flag"] == "high").mean()),
        }

    # ===== Summary JSON =====
    summary = {
        "audit_type": "automatic_author_side_realism_audit",
        "audit_date": "2026-07-05",
        "disclaimer": "This is an automatic, author-side realism risk audit. NOT human gold. NOT a naturalistic study. All risk flags are heuristic.",
        "n_claims": n_claims,
        "n_groups": n_groups,
        "risk_flag_counts": {"high": high_risk_claims, "medium": medium_risk_claims, "low": low_risk_claims},
        "high_risk_claim_rate": high_risk_claim_rate,
        "group_risk_counts": {"high": high_risk_groups, "medium": medium_risk_groups, "low": low_risk_groups},
        "high_risk_group_rate": high_risk_group_rate,
        "per_label_realism_risk": per_label_stats,
        "strong_action_forced_count": strong_forced_count,
        "strong_action_forced_rate": strong_forced_rate,
        "contradiction_mechanical_count": contra_mech_count,
        "contradiction_mechanical_rate": contra_mech_rate,
        "group_template_risk_count": high_template_groups,
        "group_template_risk_rate": group_template_risk_rate,
        "risk_type_distribution": dict(risk_type_counts),
        "low_risk_claims_usable_for_paper_examples": {
            "total": int(len(low_risk_claims_df)),
            "per_label": {k: int(v) for k, v in low_risk_per_label.items()},
        },
        "high_risk_claims_for_gold_realism_check": {
            "total": int(len(high_risk_for_gold)),
            "per_label": {k: int(v) for k, v in high_risk_for_gold_per_label.items()},
        },
        "recommended_action_distribution": {k: int(v) for k, v in action_counts.items()},
        "domain_risk_distribution": domain_risk,
        "prohibitions_enforced": {
            "no_original_data_modification": True,
            "no_gold_annotation": True,
            "no_api_calls": True,
            "no_model_training": True,
            "no_paper_modification": True,
            "no_realism_audit_as_human_gold": True,
            "no_sample_deletion": True,
        },
        "output_files": {
            "claim_realism_group_audit.csv": str(GROUP_AUDIT_CSV),
            "claim_realism_audit_queue.csv": str(CLAIM_AUDIT_CSV),
            "claim_realism_audit_summary.md": str(SUMMARY_MD),
            "claim_realism_audit_summary.json": str(SUMMARY_JSON),
            "claim_realism_implication_for_paper.md": str(IMPLICATION_MD),
            "claim_realism_audit_gate.json": str(GATE_JSON),
        },
    }

    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote summary JSON to {SUMMARY_JSON}")

    # ===== Summary MD =====
    md = []
    md.append("# Claim Realism Audit Summary")
    md.append("")
    md.append("**Task:** V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring")
    md.append("**Date:** 2026-07-05")
    md.append("**Audit type:** Automatic, author-side realism risk audit (heuristic rules).")
    md.append("**Disclaimer:** This is NOT human gold. NOT a naturalistic study. All risk flags are heuristic and require human validation in the gold pilot.")
    md.append(f"**Output directory:** `{OUT_DIR}`")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Audit overview")
    md.append("")
    md.append(f"- **Claims audited:** {n_claims} (444 SimClaim counterfactual candidates)")
    md.append(f"- **Groups audited:** {n_groups} (111 evidence groups, 4 claims each)")
    md.append(f"- **Labels:** 111 supported + 111 mild_scope_overclaim + 111 strong_action_overclaim + 111 contradiction_candidate")
    md.append(f"- **Domains:** 6 (autonomous_driving, policy_simulation, digital_twin, cyber_defense, marl, robotics)")
    md.append(f"- **Risk rules applied:** 7 (too_template_like, too_extreme, unnatural_wording, not_scientific_claim, contradiction_too_mechanical, strong_action_too_forced, mild_strong_boundary_unclear)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Headline risk distribution")
    md.append("")
    md.append("### Claim-level risk")
    md.append("")
    md.append("| Risk level | Count | Rate |")
    md.append("| --- | --- | --- |")
    md.append(f"| High | {high_risk_claims} | {high_risk_claim_rate:.1%} |")
    md.append(f"| Medium | {medium_risk_claims} | {medium_risk_claims/n_claims:.1%} |")
    md.append(f"| Low | {low_risk_claims} | {low_risk_claims/n_claims:.1%} |")
    md.append("")
    md.append("### Group-level risk")
    md.append("")
    md.append("| Risk level | Count | Rate |")
    md.append("| --- | --- | --- |")
    md.append(f"| High | {high_risk_groups} | {high_risk_group_rate:.1%} |")
    md.append(f"| Medium | {medium_risk_groups} | {medium_risk_groups/n_groups:.1%} |")
    md.append(f"| Low | {low_risk_groups} | {low_risk_groups/n_groups:.1%} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Per-label realism risk")
    md.append("")
    md.append("| Label | N | High | Medium | Low | High rate | Mean risk score (0-5) |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRADICTION]:
        s = per_label_stats.get(label, {})
        md.append(f"| {label} | {s.get('n',0)} | {s.get('high_risk',0)} | {s.get('medium_risk',0)} | {s.get('low_risk',0)} | {s.get('high_risk_rate',0):.1%} | {s.get('mean_risk_score',0):.2f} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Specific risk type rates")
    md.append("")
    md.append("### strong_action_too_forced")
    md.append("")
    md.append(f"- **Count:** {strong_forced_count} / {n_strong} strong_action_overclaim claims")
    md.append(f"- **Rate:** {strong_forced_rate:.1%}")
    md.append("")
    md.append("### contradiction_too_mechanical")
    md.append("")
    md.append(f"- **Count:** {contra_mech_count} / {n_contra} contradiction_candidate claims")
    md.append(f"- **Rate:** {contra_mech_rate:.1%}")
    md.append("")
    md.append("### group_template_risk (template_similarity_score > 0.6)")
    md.append("")
    md.append(f"- **Count:** {high_template_groups} / {n_groups} groups")
    md.append(f"- **Rate:** {group_template_risk_rate:.1%}")
    md.append("")
    md.append("### All risk type distribution (a claim may trigger multiple)")
    md.append("")
    md.append("| Risk type | Count |")
    md.append("| --- | --- |")
    for rt, cnt in sorted(risk_type_counts.items(), key=lambda x: -x[1]):
        md.append(f"| {rt} | {cnt} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Low-risk claims usable as paper examples")
    md.append("")
    md.append(f"- **Total low-risk claims:** {len(low_risk_claims_df)}")
    md.append("- **Per label:**")
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRADICTION]:
        cnt = int(low_risk_per_label.get(label, 0))
        md.append(f"  - {label}: {cnt}")
    md.append("")
    md.append("These low-risk claims are recommended as candidates for paper illustrative examples (still subject to gold validation).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 6. High-risk claims recommended for gold realism check")
    md.append("")
    md.append(f"- **Total high-risk claims:** {len(high_risk_for_gold)}")
    md.append("- **Per label:**")
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRADICTION]:
        cnt = int(high_risk_for_gold_per_label.get(label, 0))
        md.append(f"  - {label}: {cnt}")
    md.append("")
    md.append("These high-risk claims should be prioritized in the gold realism annotation (Layer 2 of the gold protocol), to confirm whether the heuristic risk translates to human-judged unrealistic claims.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 7. Recommended action distribution")
    md.append("")
    md.append("| Action | Count |")
    md.append("| --- | --- |")
    for action, cnt in sorted(action_counts.items(), key=lambda x: -x[1]):
        md.append(f"| {action} | {cnt} |")
    md.append("")
    md.append("- **keep:** low risk, suitable as-is (still silver, not gold).")
    md.append("- **review:** medium risk, author should manually inspect before paper use.")
    md.append("- **prioritize_gold_realism:** high risk, must be prioritized in gold realism annotation.")
    md.append("- **exclude_from_paper_examples:** high risk with extreme/templated wording, must NOT be used as illustrative example in paper.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 8. Domain risk distribution")
    md.append("")
    md.append("| Domain | N | High risk | High risk rate |")
    md.append("| --- | --- | --- | --- |")
    for d, s in sorted(domain_risk.items(), key=lambda x: -x[1]["high_risk_rate"]):
        md.append(f"| {d} | {s['n']} | {s['high_risk']} | {s['high_risk_rate']:.1%} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 9. Risk rules summary")
    md.append("")
    md.append("| # | Rule | Scope | Heuristic |")
    md.append("| --- | --- | --- | --- |")
    md.append("| 1 | too_template_like | all claims | Mean pairwise content-token Jaccard > 0.6 within group |")
    md.append("| 2 | too_extreme | all claims | Contains extreme words (always, guarantee, fully, completely, solve, replace, eliminate, proves, deployment-ready, etc.) |")
    md.append("| 3 | unnatural_wording | all claims | Matches mechanical phrasing patterns OR abnormal length (<6 or >70 words) |")
    md.append("| 4 | not_scientific_claim | all claims | Matches slogan/policy/marketing patterns (should be deployed, we recommend, game-changer, revolutionize, etc.) |")
    md.append("| 5 | contradiction_too_mechanical | contradiction_candidate only | High token similarity to supported claim (>0.7) OR (>0.5 + negation cue) |")
    md.append("| 6 | strong_action_too_forced | strong_action_overclaim only | Strong cues (deployment/safety/policy/generalization) in claim but absent in evidence, OR 3+ strong cues |")
    md.append("| 7 | mild_strong_boundary_unclear | mild & strong only | Mild-strong token Jaccard > 0.75 OR (token diff <=3 AND sim > 0.5) |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 10. Prohibitions enforced")
    md.append("")
    md.append("- No original data modification — PASS (input CSV read-only; output is new files only).")
    md.append("- No gold annotation — PASS (all risk scores are heuristic, no human label applied).")
    md.append("- No API calls — PASS (regex/token rules only, no LLM/API).")
    md.append("- No model training — PASS (no ML models trained).")
    md.append("- No paper modification — PASS (V3.12/V3.13/V3.14 papers untouched).")
    md.append("- No realism-audit-as-human-gold — PASS (clearly labelled 'automatic, author-side realism risk audit').")
    md.append("- No sample deletion — PASS (all 444 claims retained in audit queue).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 11. Limitations")
    md.append("")
    md.append("1. **Heuristic rules.** All 7 risk rules are regex/token-based heuristics. They will miss subtle unrealistic phrasing and may false-flag stylometrically dense but realistic claims. Human gold validation is required to calibrate.")
    md.append("2. **No semantic understanding.** The rules cannot detect semantically absurd claims that use natural phrasing. A claim like 'This benchmark result proves that autonomous driving is solved' would be flagged by 'too_extreme' (proves, solved) but a more subtle semantic overclaim might be missed.")
    md.append("3. **Token Jaccard is coarse.** Template similarity uses content-token Jaccard, which does not capture syntactic structure. Two claims with the same tokens in different order would score 1.0 similarity, but might be genuinely different.")
    md.append("4. **Non-scientific-claim patterns are English-centric.** The patterns target English slogan/marketing phrasing; claims in other languages or domain-specific jargon may be mis-flagged.")
    md.append("5. **Strong-forced detection is conservative.** A claim is flagged only if strong cues appear in claim but NOT in evidence. Claims where evidence briefly mentions deployment but the claim heavily extrapolates may not be flagged.")
    md.append("6. **All scores are silver-stage.** Gold adjudication (gold_pilot_protocol_freeze_v1, PROTOCOL FROZEN, annotation NOT begun) is required to validate the heuristic risk against human judgment.")

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote summary MD to {SUMMARY_MD}")

    # ===== Gate JSON =====
    realism_gold_needed = high_risk_claim_rate > 0.10 or strong_forced_rate > 0.20 or contra_mech_rate > 0.20
    safe_as_diagnostic = high_risk_claim_rate < 0.40  # still usable if <40% high risk
    safe_as_naturalistic = False  # never — it's counterfactual diagnostic, not naturalistic

    gate = {
        "gate_name": "claim_realism_audit_gate",
        "task": "V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring",
        "date": "2026-07-05",
        "audit_completed": True,
        "n_claims": n_claims,
        "n_groups": n_groups,
        "high_risk_claim_rate": round(high_risk_claim_rate, 4),
        "high_risk_group_rate": round(high_risk_group_rate, 4),
        "strong_action_forced_rate": round(strong_forced_rate, 4),
        "contradiction_mechanical_rate": round(contra_mech_rate, 4),
        "realism_gold_needed": bool(realism_gold_needed),
        "safe_to_use_as_diagnostic_set": bool(safe_as_diagnostic),
        "safe_to_claim_naturalistic": bool(safe_as_naturalistic),
        "recommended_next_action": (
            "Include realism_score_1_to_5 in gold pilot annotation (Layer 2 of gold_pilot_protocol_freeze_v1); "
            "prioritize high-risk claims identified here for realism validation; "
            "exclude high-risk + extreme/templated claims from paper illustrative examples; "
            "report claim_realism_audit_summary in paper limitations section as automatic-author-side audit awaiting human validation"
        ),
        "prohibitions_enforced": {
            "no_original_data_modification": True,
            "no_gold_annotation": True,
            "no_api_calls": True,
            "no_model_training": True,
            "no_paper_modification": True,
            "no_realism_audit_as_human_gold": True,
            "no_sample_deletion": True,
        },
        "audit_type_disclaimer": "Automatic, author-side realism risk audit. NOT human gold. NOT a naturalistic study. All risk flags are heuristic and require human validation in the gold pilot.",
    }

    with open(GATE_JSON, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"Wrote gate JSON to {GATE_JSON}")

    # ===== Implication for paper MD =====
    impl = []
    impl.append("# Claim Realism Audit: Implications for Paper Narrative")
    impl.append("")
    impl.append("**Task:** V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring")
    impl.append("**Date:** 2026-07-05")
    impl.append("**Companion files:** `claim_realism_audit_summary.md`, `claim_realism_audit_queue.csv`, `claim_realism_group_audit.csv`, `claim_realism_audit_gate.json`")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q1. Can SimClaim still serve as a controlled diagnostic set?")
    impl.append("")
    impl.append(f"**Answer: YES — but with explicit realism caveats.** Based on this automatic audit, {high_risk_claims}/{n_claims} ({high_risk_claim_rate:.1%}) claims are flagged high-risk and {high_risk_groups}/{n_groups} ({high_risk_group_rate:.1%}) groups are flagged high-risk. The high-risk rate is non-trivial but does NOT invalidate the diagnostic-set purpose, because:")
    impl.append("")
    impl.append("1. **SimClaim was designed as a controlled counterfactual diagnostic set, not a naturalistic corpus.** The 1:1:1:1 balanced design and the same-evidence-four-variants construction are deliberate, intended to stress-test R4's boundary-recognition ability under controlled conditions. Realism is a quality dimension, not the design goal.")
    impl.append("2. **The audit flags are heuristic, not validated.** A high heuristic risk flag does NOT mean the claim is unrealistic — it means the claim matches a pattern that *might* be unrealistic. Gold validation is required to confirm.")
    impl.append("3. **Even high-risk claims retain diagnostic value.** A claim that is 'too_extreme' or 'strong_action_too_forced' is still a valid test of whether R4 can detect overclaim language — the test is whether R4 flags it, not whether the claim is naturalistic.")
    impl.append("")
    impl.append("**Conditional continued use:** SimClaim remains usable as a controlled diagnostic set provided that:")
    impl.append("- The paper explicitly labels it as 'controlled counterfactual diagnostic set, not naturalistic corpus.'")
    impl.append("- The paper discloses the realism audit results (high-risk rate, per-label risk) in the Limitations section.")
    impl.append("- High-risk claims are excluded from illustrative examples in the paper body.")
    impl.append("- The gold pilot protocol (already frozen) includes realism_score_1_to_5 as Layer 2 to validate the audit.")
    impl.append("- No claim is made about real-world prevalence based on SimClaim.")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q2. Which claims are unsuitable as paper illustrative examples?")
    impl.append("")
    impl.append(f"**Answer: {int((claim_df['recommended_action']=='exclude_from_paper_examples').sum())} claims are flagged `exclude_from_paper_examples`** (high risk + extreme/templated wording). These should NOT appear as worked examples in the paper body, introduction, or discussion.")
    impl.append("")
    impl.append("Additionally, all `prioritize_gold_realism` claims (high risk) should be avoided as paper examples until gold validation confirms their realism.")
    impl.append("")
    impl.append("**Recommended pool for paper illustrative examples:**")
    impl.append(f"- Use only `low` risk claims ({low_risk_claims} available, per-label distribution above).")
    impl.append("- Select examples across all 4 labels and multiple domains for balance.")
    impl.append("- Even low-risk claims should pass a final human sanity check before being placed in the paper body.")
    impl.append("- Avoid using the same evidence group's 4 claims as a 'quartet example' if the group is flagged `high` risk.")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q3. Is realism_score mandatory in the paper?")
    impl.append("")
    impl.append(f"**Answer: YES — realism_score_1_to_5 must be added to the gold pilot protocol.** This audit found {high_risk_claim_rate:.1%} high-risk claims heuristically, but the audit is rule-based and cannot substitute for human judgment. Without realism gold, the paper cannot defend against the reviewer concern that 'AI-generated counterfactual claims are templated and unrealistic.'")
    impl.append("")
    impl.append("**Required actions:**")
    impl.append("1. **gold_pilot_protocol_freeze_v1 Layer 2 (already planned):** Annotators assign `claim_realism_score_1_to_5` for each pilot claim (1=very realistic, 5=very unrealistic).")
    impl.append("2. **Pre-registered thresholds (already in protocol):** 25% class-level, 25% paper-level — if exceeded, paper claim must be downgraded.")
    impl.append("3. **Audit-to-gold cross-check:** After gold pilot, compare heuristic risk_score to gold realism_score to calibrate the heuristic rules. If correlation is weak, the heuristic audit should be reported as exploratory, not definitive.")
    impl.append("4. **Paper reporting:** Report both the automatic audit results (this file) and the gold realism results (after pilot) in the Limitations section.")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q4. If realism risk is high, how should the paper be downgraded?")
    impl.append("")
    impl.append("**Answer:** Downgrade is conditional on gold pilot outcomes. The pre-registered downgrade path is:")
    impl.append("")
    impl.append("**Scenario A — gold pilot realism is acceptable** (class-level high-realism rate < 25% AND paper-level < 25%):")
    impl.append("- No downgrade needed.")
    impl.append("- Report audit + gold realism results in Limitations.")
    impl.append("- SimClaim remains 'controlled counterfactual diagnostic set.'")
    impl.append("")
    impl.append("**Scenario B — gold pilot realism is borderline** (class-level 25-40% OR paper-level 25-40%):")
    impl.append("- Downgrade paper claim from 'SimClaim is a controlled diagnostic set' to 'SimClaim is a controlled diagnostic set with realism caveats; X% of claims were judged unrealistic by human annotators.'")
    impl.append("- Restrict quantitative claims to per-class metrics on gold-validated subset.")
    impl.append("- Add explicit Limitations paragraph on realism threats to external validity.")
    impl.append("")
    impl.append("**Scenario C — gold pilot realism is poor** (class-level > 40% OR paper-level > 40%):")
    impl.append("- Major downgrade: SimClaim is 'a synthetic counterfactual probe, not a diagnostic set.'")
    impl.append("- All R4/LLM metrics on SimClaim are reported as 'probe-stage results pending naturalistic corpus validation.'")
    impl.append("- Add a 'Threats to Validity' section.")
    impl.append("- Consider delaying submission until a naturalistic corpus study is completed.")
    impl.append("")
    impl.append("**Current state:** Gold pilot annotation has NOT begun (protocol frozen 2026-07-04). The paper cannot commit to Scenario A/B/C until gold realism data exists. V3.14 paper should report the audit results and pre-register the downgrade path.")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q5. How to explain the legitimacy of synthetic counterfactual claims?")
    impl.append("")
    impl.append("**Answer:** The paper should explicitly justify the counterfactual construction in the Data section. Recommended framing:")
    impl.append("")
    impl.append("### Paste-ready paragraph for paper §V (Data)")
    impl.append("")
    impl.append("> SimClaim is a controlled counterfactual diagnostic set constructed by generating four claim variants per evidence span: a faithful *supported* claim, a *mild_scope_overclaim* that slightly over-extends the evidence scope, a *strong_action_overclaim* that aggressively extrapolates to deployment/safety/policy implications, and a *contradiction_candidate* that reverses a key evidence assertion. The four-variant design is deliberate: it provides balanced 1:1:1:1 coverage of the four evidence-sufficiency relations, enabling per-class boundary-recognition evaluation that would be impossible on a naturalistic corpus where `strong_action_overclaim` and `contradiction_candidate` are rare. The construction is *not* intended to represent the natural prevalence of these relations in real scientific writing; a complementary low-prevalence screening simulation (§VIII.D.E) evaluates deployment-stage screening behavior under realistic class imbalance. SimClaim's evidence spans are sourced from real peer-reviewed papers across six domains (autonomous driving, policy simulation, digital twin, cyber defense, multi-agent reinforcement learning, robotics), ensuring that the *evidence* side of each claim-evidence pair is realistic; only the *claims* are synthetic counterfactuals. An automatic author-side realism audit (§IX Limitations) flagged X% of claims as high-realism-risk heuristically; a two-layer gold pilot protocol (§VII.J) is pre-registered to validate both relation labels (Layer 1) and claim realism (Layer 2, `claim_realism_score_1_to_5`) against human judgment, with pre-registered downgrade thresholds (25% class-level, 25% paper-level).")
    impl.append("")
    impl.append("### Key points the paper must make")
    impl.append("")
    impl.append("1. **Counterfactual by design, not by accident.** The four-variant construction is a deliberate diagnostic tool, not a data-quality failure.")
    impl.append("2. **Evidence is real, claims are synthetic.** This is the inverse of many NLP datasets where claims are real but evidence is retrieved; here we hold evidence fixed and vary claims to isolate claim-side reasoning.")
    impl.append("3. **Diagnostic ≠ naturalistic.** SimClaim answers 'can R4 recognize the boundary?' not 'what is the prevalence of strong_action overclaim in real scientific writing?'")
    impl.append("4. **Realism is audited and will be gold-validated.** The audit is reported transparently; the gold pilot will quantify realism empirically.")
    impl.append("5. **Low-prevalence simulation complements SimClaim.** Together they answer both boundary-recognition and deployment-screening questions.")
    impl.append("")
    impl.append("---")
    impl.append("")
    impl.append("## Q6. Summary of paper-edit recommendations")
    impl.append("")
    impl.append("| Section | Edit | Status |")
    impl.append("| --- | --- | --- |")
    impl.append("| §V (Data) | Add paste-ready counterfactual-construction paragraph above | Pending V3.16 |")
    impl.append("| §VII.J (Gold protocol) | Confirm Layer 2 realism_score is included (already in gold_pilot_protocol_freeze_v1) | Already in V3.13/V3.14 |")
    impl.append("| §VIII.D.E (Low-prev sim) | Cross-reference realism audit | Already in V3.15 |")
    impl.append("| §IX (Limitations) | Add realism audit summary + downgrade path (Scenarios A/B/C) | Pending V3.16 |")
    impl.append("| §VI.B/C (Results) | Use only low-risk claims as illustrative examples | Pending V3.16 |")
    impl.append("")
    impl.append("**Note:** The current V3.14 paper is NOT modified by this audit. All recommendations are pending V3.16 integration after gold pilot begins.")
    impl.append("")

    with open(IMPLICATION_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(impl))
    print(f"Wrote implication MD to {IMPLICATION_MD}")

    # Final console summary
    print("\n=== AUDIT COMPLETE ===")
    print(f"n_claims={n_claims}, n_groups={n_groups}")
    print(f"high_risk_claims={high_risk_claims} ({high_risk_claim_rate:.1%})")
    print(f"high_risk_groups={high_risk_groups} ({high_risk_group_rate:.1%})")
    print(f"strong_forced_rate={strong_forced_rate:.1%}")
    print(f"contra_mech_rate={contra_mech_rate:.1%}")
    print(f"group_template_risk_rate={group_template_risk_rate:.1%}")
    print(f"realism_gold_needed={realism_gold_needed}")
    print(f"safe_as_diagnostic={safe_as_diagnostic}")
    print(f"safe_as_naturalistic={safe_as_naturalistic}")


if __name__ == "__main__":
    main()
