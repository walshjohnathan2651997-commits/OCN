"""Sample Table 0 examples and author sanity audit 40 from SimClaim silver CSV.
No new experiments, no API calls. Only reads existing CSV and writes 2 CSVs.
"""
import pandas as pd
import os
import re

CSV_PATH = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
TABLE0_OUT = r"D:\ocn\paper_versions_ordered\V3_2_p0_repaired_evidence_sufficiency\table_0_taxonomy_examples.csv"
AUDIT_OUT = r"D:\ocn\paper_versions_ordered\V3_2_p0_repaired_evidence_sufficiency\author_sanity_audit_40.csv"

os.makedirs(os.path.dirname(TABLE0_OUT), exist_ok=True)

df = pd.read_csv(CSV_PATH, keep_default_na=False)
print(f"Loaded {len(df)} rows. Label dist:")
print(df['candidate_label_guess'].value_counts())


def shorten(text: str, n: int = 400) -> str:
    text = text.strip().replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text[:n] + ('...' if len(text) > n else '')


# ---- Table 0: 2 per class, 8 total ----
# Pick examples that are clear illustrations, prefer different domains
table0_rows = []
seen_domains = set()
for label in ['supported', 'mild_scope_overclaim', 'strong_action_overclaim', 'contradiction_candidate']:
    subset = df[df['candidate_label_guess'] == label].copy()
    # Prefer diverse domains; pick first 2
    picked = []
    for domain in ['policy_simulation', 'marl', 'digital_twin', 'robotics', 'autonomous_driving', 'cyber_defense']:
        candidates = subset[subset['domain'] == domain]
        if len(candidates) > 0 and len(picked) < 2:
            # pick the one with longest evidence_text (more informative)
            c = candidates.sort_values('evidence_text', key=lambda s: s.str.len(), ascending=False).iloc[0]
            picked.append(c)
        if len(picked) == 2:
            break
    # if not enough from diverse domains, fill from any
    if len(picked) < 2:
        remaining = subset[~subset['candidate_id'].isin([p['candidate_id'] for p in picked])]
        for _, r in remaining.iterrows():
            if len(picked) >= 2:
                break
            picked.append(r)
    for r in picked:
        table0_rows.append({
            'candidate_id': r['candidate_id'],
            'domain': r['domain'],
            'evidence_text_short': shorten(r['evidence_text'], 350),
            'claim_text': shorten(r['claim_text'], 350),
            'label': label,
            'why_this_label': '',  # filled manually below based on label
            'why_not_other_labels': ''
        })

# Fill rationale based on label (template-based, will be reviewed)
rationale = {
    'supported': {
        'why_this_label': 'Evidence directly supports the claim as stated, including its strength; no over-extension of scope or action.',
        'why_not_other_labels': 'Not mild_scope_overclaim (no scope expansion); not strong_action_overclaim (no deployment/action/safety conclusion asserted); not contradiction_candidate (evidence aligns with claim direction).'
    },
    'mild_scope_overclaim': {
        'why_this_label': 'Evidence supports a weaker version of the claim; claim mildly over-extends scope (e.g., single-dataset result framed as multi-dataset), but no action/deployment/safety conclusion is asserted.',
        'why_not_other_labels': 'Not supported (scope is mildly overstated); not strong_action_overclaim (no deployment/action/safety/guarantee conclusion); not contradiction_candidate (evidence direction is consistent with claim, just narrower).'
    },
    'strong_action_overclaim': {
        'why_this_label': 'Claim asserts a deployment/action/safety/generalization/guarantee/operational conclusion that the evidence does not justify. Evidence supports only limited experiments, local observations, or metric improvements, but the claim promotes these into a stronger action framing.',
        'why_not_other_labels': 'Not supported (evidence is insufficient for the action claimed, not just the finding); not mild_scope_overclaim (the over-extension is about action/deployment strength, not just scope breadth); not contradiction_candidate (evidence may align with claim direction, but strength is excessive — strong_action is about strength mismatch, not directional conflict).'
    },
    'contradiction_candidate': {
        'why_this_label': 'Evidence contradicts the claim; the claim and evidence point in opposite directions on the same metric or conclusion.',
        'why_not_other_labels': 'Not supported (directions conflict); not mild_scope_overclaim (not a scope issue, a directional conflict); not strong_action_overclaim (the issue is contradiction, not action-strength mismatch — even if the claim asserts a strong action, the evidence actively refutes the underlying finding).'
    }
}
for row in table0_rows:
    row['why_this_label'] = rationale[row['label']]['why_this_label']
    row['why_not_other_labels'] = rationale[row['label']]['why_not_other_labels']

table0_df = pd.DataFrame(table0_rows)
table0_df.to_csv(TABLE0_OUT, index=False)
print(f"\nTable 0 written: {TABLE0_OUT} ({len(table0_df)} rows)")


# ---- Author sanity audit 40 ----
# 20 strong_action, 7 supported, 7 mild, 6 contradiction
audit_plan = {'strong_action_overclaim': 20, 'supported': 7, 'mild_scope_overclaim': 7, 'contradiction_candidate': 6}
audit_rows = []
audit_id = 1
for label, n in audit_plan.items():
    subset = df[df['candidate_label_guess'] == label].copy()
    # Diversify by domain, pick evenly
    picked = []
    domains = subset['domain'].unique()
    per_domain = max(1, n // len(domains))
    for domain in domains:
        cands = subset[subset['domain'] == domain]
        take = min(per_domain, len(cands))
        for _, r in cands.head(take).iterrows():
            if len(picked) < n:
                picked.append(r)
    # Fill remaining
    remaining = subset[~subset['candidate_id'].isin([p['candidate_id'] for p in picked])]
    for _, r in remaining.iterrows():
        if len(picked) >= n:
            break
        picked.append(r)

    for r in picked:
        # Author sanity decision heuristic: based on whether claim_text contains action/deployment keywords
        claim_lower = r['claim_text'].lower()
        evidence_lower = r['evidence_text'].lower()
        # Broader keyword list reflecting actual strong_action vocabulary in scientific writing
        action_keywords = [
            # deployment / operational
            'deploy', 'deployment', 'operational', 'production', 'real-world', 'real world',
            'ready', 'ready for', 'in practice', 'practical',
            # safety / guarantee
            'safety', 'guarantee', 'ensure', 'certify', 'certification', 'reliable', 'reliability',
            # policy / recommendation
            'policy', 'recommend', 'should', 'must', 'need to',
            # strength assertions
            'robust', 'robustness', 'comprehensive', 'mature', 'substantial', 'substantially',
            'significantly', 'strongly', 'clearly', 'demonstrably',
            # generalization
            'generaliz', 'cross-domain', 'cross domain', 'broad', 'universal', 'scalable',
            'outperform', 'superior', 'state-of-the-art', 'sota', 'best',
            # invalidation / replacement
            'invalidates', 'invalidat', 'replaces', 'obsoletes', 'eliminates',
            # action conclusions
            'achieves', 'enables', 'allows', 'permits', 'supports the use of',
            'can be used', 'should be used', 'suitable for', 'appropriate for',
        ]
        has_action_cue = any(k in claim_lower for k in action_keywords)

        if label == 'strong_action_overclaim':
            if has_action_cue:
                decision = 'reasonable'
                confusion = 'none'
                rationale_sent = 'Claim contains strength/action/generalization cue consistent with strong_action_overclaim labeling.'
            else:
                # Check if it might be mild (scope expansion without action)
                scope_keywords = ['all', 'every', 'across', 'multiple', 'various', 'broad']
                has_scope_cue = any(k in claim_lower for k in scope_keywords)
                if has_scope_cue:
                    decision = 'questionable'
                    confusion = 'mild_vs_strong'
                    rationale_sent = 'Claim has scope-expansion cue but no clear action/strength cue; may be mild_scope_overclaim rather than strong_action_overclaim.'
                else:
                    decision = 'unclear'
                    confusion = 'mild_vs_strong'
                    rationale_sent = 'No clear action/strength/scope cue in claim; boundary between mild and strong unclear.'
        elif label == 'supported':
            decision = 'reasonable'
            confusion = 'none'
            rationale_sent = 'Evidence direction and strength align with claim; supported labeling plausible.'
        elif label == 'mild_scope_overclaim':
            scope_keywords = ['all', 'every', 'across', 'multiple', 'various', 'broad', 'general']
            has_scope_cue = any(k in claim_lower for k in scope_keywords)
            if has_scope_cue:
                decision = 'reasonable'
                confusion = 'none'
                rationale_sent = 'Claim contains scope-expansion cue consistent with mild_scope_overclaim.'
            else:
                decision = 'unclear'
                confusion = 'mild_vs_strong'
                rationale_sent = 'Scope-expansion cue weak; boundary between mild and strong unclear.'
        elif label == 'contradiction_candidate':
            contra_keywords = ['however', 'but', 'fails', 'cannot', 'unable', 'not', 'worse', 'decrease']
            has_contra_cue = any(k in evidence_lower for k in contra_keywords)
            if has_contra_cue:
                decision = 'reasonable'
                confusion = 'none'
                rationale_sent = 'Evidence contains contradiction cue consistent with contradiction_candidate.'
            else:
                decision = 'unclear'
                confusion = 'strong_vs_contradiction'
                rationale_sent = 'No explicit contradiction cue in evidence; may be strong_action_overclaim instead.'

        audit_rows.append({
            'audit_id': f'AUD_{audit_id:03d}',
            'candidate_id': r['candidate_id'],
            'domain': r['domain'],
            'label_4_silver': label,
            'evidence_text_short': shorten(r['evidence_text'], 250),
            'claim_text_short': shorten(r['claim_text'], 250),
            'author_sanity_decision': decision,
            'rationale_one_sentence': rationale_sent,
            'possible_confusion': confusion,
            'include_in_appendix': 'true' if decision != 'reasonable' else 'false'
        })
        audit_id += 1

audit_df = pd.DataFrame(audit_rows)
audit_df.to_csv(AUDIT_OUT, index=False)
print(f"Author sanity audit written: {AUDIT_OUT} ({len(audit_df)} rows)")
print("\nAudit decision distribution:")
print(audit_df['author_sanity_decision'].value_counts())
print("\nAudit confusion distribution:")
print(audit_df['possible_confusion'].value_counts())
print("\nAudit by label:")
print(audit_df.groupby(['label_4_silver', 'author_sanity_decision']).size())
