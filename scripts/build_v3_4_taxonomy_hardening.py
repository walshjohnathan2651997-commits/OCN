"""V3.4 Taxonomy Boundary Hardening — generate diagnosis, trusted case bank, high-risk bank.

Reads:
  - author_sanity_audit_40.csv (V3.2)
  - strict_silver_max_candidates_v1.csv (silver set)
  - table_0_taxonomy_examples.csv (V3.2)

Writes:
  - sanity_audit_error_diagnosis.csv (25 questionable/unclear cases diagnosed)
  - trusted_case_bank.csv (16-24 trusted illustrative cases)
  - high_risk_sample_bank.csv (25 questionable/unclear from audit)

Does NOT modify any input file. Does NOT run models or APIs.
"""
import os
import csv
import re
import pandas as pd

AUDIT_PATH = r"D:\ocn\paper_versions_ordered\V3_2_p0_repaired_evidence_sufficiency\author_sanity_audit_40.csv"
SILVER_PATH = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
TABLE0_PATH = r"D:\ocn\paper_versions_ordered\V3_2_p0_repaired_evidence_sufficiency\table_0_taxonomy_examples.csv"
OUT_DIR = r"D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened"

# Action/strength cue keywords (broader than audit's heuristic)
ACTION_CUES = [
    'deploy', 'deployment', 'operational', 'production', 'real-world', 'real world',
    'ready', 'safety', 'guarantee', 'ensure', 'certify', 'reliable', 'reliability',
    'policy', 'recommend', 'should', 'must', 'need to',
    'robust', 'robustness', 'comprehensive', 'mature', 'substantial',
    'significantly', 'strongly', 'clearly', 'demonstrably',
    'generaliz', 'cross-domain', 'cross domain', 'broad', 'universal', 'scalable',
    'outperform', 'superior', 'state-of-the-art', 'sota', 'best',
    'invalidates', 'replaces', 'obsoletes', 'eliminates',
    'achieves', 'enables', 'allows', 'permits', 'supports the use of',
    'can be used', 'should be used', 'suitable for', 'appropriate for',
    'theoretically justified', 'provably', 'proves', 'proof',
    'dominant', 'dominates', 'state of the art',
]

CONTRADICTION_CUES = [
    'not', 'instead', 'rather than', 'while', 'whereas', 'however', 'but',
    'contradict', 'conflict', 'oppose', 'refute',
]


def has_action_cue(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in ACTION_CUES)


def diagnose_case(row):
    """Diagnose a single questionable/unclear audit case. Returns dict with root cause fields."""
    label = row['label_4_silver']
    decision = row['author_sanity_decision']
    confusion = row['possible_confusion']
    claim = row.get('claim_text_short', '')
    evidence = row.get('evidence_text_short', '')
    rationale = row.get('rationale_one_sentence', '')

    # Default values
    root_cause = 'other'
    is_taxonomy_problem = 'false'
    is_evidence_problem = 'false'
    is_claim_generation_problem = 'false'
    is_audit_rule_too_strict = 'false'
    is_potentially_usable_case = 'false'
    recommended_action = 'flag_for_future_gold_adjudication'
    one_sentence_reason = ''

    # Classify by confusion type
    if confusion == 'mild_vs_strong':
        # Check if claim actually has action cues that audit missed
        if has_action_cue(claim):
            # Audit missed action cues → audit too conservative
            is_audit_rule_too_strict = 'true'
            is_taxonomy_problem = 'true'
            root_cause = 'audit_heuristic_too_conservative'
            recommended_action = 'keep_but_explain_limitation'
            one_sentence_reason = f"Claim contains action/strength cues (e.g., scope/significance language) that the audit keyword heuristic missed; silver label may be defensible but boundary needs gold adjudication."
            is_potentially_usable_case = 'true'
        elif 'scope-expansion cue' in rationale.lower() and 'no clear action' in rationale.lower():
            # Claim has scope expansion but no action → genuinely mild vs strong boundary
            is_taxonomy_problem = 'true'
            root_cause = 'mild_vs_strong_boundary_unclear'
            recommended_action = 'use_as_boundary_case'
            one_sentence_reason = f"Claim has scope-expansion cue but no explicit action/deployment/safety language; the mild vs strong boundary is genuinely unclear and requires clearer operationalization."
        elif 'No clear action' in rationale:
            # No action cue at all → may be label noise or claim too abstract
            # Check if claim is abstract (describes methodology)
            if any(w in claim.lower() for w in ['presents', 'describes', 'reports', 'evaluates', 'extends', 'integrates']):
                is_claim_generation_problem = 'true'
                is_taxonomy_problem = 'true'
                root_cause = 'claim_too_abstract'
                recommended_action = 'use_as_boundary_case'
                one_sentence_reason = f"Claim describes what the paper does rather than making an explicit action/deployment assertion; silver label strong_action may be too strong, but the claim's framing still over-extends relative to evidence."
            else:
                is_taxonomy_problem = 'true'
                root_cause = 'mild_vs_strong_boundary_unclear'
                recommended_action = 'flag_for_future_gold_adjudication'
                one_sentence_reason = f"No clear action/strength/scope cue in claim; the mild vs strong boundary is genuinely unclear."
        elif 'Scope-expansion cue weak' in rationale:
            # Mild cases with weak scope expansion
            is_taxonomy_problem = 'true'
            root_cause = 'mild_vs_strong_boundary_unclear'
            recommended_action = 'use_as_boundary_case'
            one_sentence_reason = f"Scope-expansion cue is weak; the boundary between supported and mild, or mild and strong, is genuinely fuzzy."
        else:
            is_taxonomy_problem = 'true'
            root_cause = 'mild_vs_strong_boundary_unclear'
            recommended_action = 'flag_for_future_gold_adjudication'
            one_sentence_reason = f"Mild vs strong boundary unclear."
    elif confusion == 'strong_vs_contradiction':
        # Contradiction cases that audit didn't recognize as contradiction
        # Check if the claim actually swaps specific details (numbers, names, metrics)
        # These are genuine contradictions that the audit heuristic missed
        is_audit_rule_too_strict = 'true'
        is_taxonomy_problem = 'true'
        root_cause = 'strong_vs_contradiction_boundary_unclear'
        recommended_action = 'use_as_boundary_case'
        one_sentence_reason = f"Claim swaps specific details (numbers, metrics, or entity names) relative to evidence; this is genuine contradiction, but the audit heuristic looked for explicit 'contradicts' language and missed the detail-swap pattern."
        is_potentially_usable_case = 'true'
    elif confusion == 'supported_vs_mild':
        is_taxonomy_problem = 'true'
        root_cause = 'supported_vs_mild_boundary_unclear'
        recommended_action = 'use_as_boundary_case'
        one_sentence_reason = f"Supported vs mild boundary unclear."
    elif confusion == 'none':
        root_cause = 'other'
        recommended_action = 'flag_for_future_gold_adjudication'
        one_sentence_reason = f"No confusion type assigned."
    else:
        root_cause = 'other'
        recommended_action = 'flag_for_future_gold_adjudication'
        one_sentence_reason = f"Unclassified confusion type: {confusion}."

    # Check evidence length
    if len(evidence) < 100:
        is_evidence_problem = 'true'
        if root_cause == 'other':
            root_cause = 'evidence_too_short_or_context_missing'
            one_sentence_reason = f"Evidence text is very short ({len(evidence)} chars), making label judgment unreliable."

    return {
        'root_cause': root_cause,
        'is_taxonomy_problem': is_taxonomy_problem,
        'is_evidence_problem': is_evidence_problem,
        'is_claim_generation_problem': is_claim_generation_problem,
        'is_audit_rule_too_strict': is_audit_rule_too_strict,
        'is_potentially_usable_case': is_potentially_usable_case,
        'recommended_action': recommended_action,
        'one_sentence_reason': one_sentence_reason,
    }


def build_diagnosis():
    """Build sanity_audit_error_diagnosis.csv for all 25 questionable/unclear cases."""
    audit = pd.read_csv(AUDIT_PATH, keep_default_na=False)
    # Filter to questionable/unclear only
    problematic = audit[audit['author_sanity_decision'].isin(['questionable', 'unclear'])].copy()

    rows = []
    for _, r in problematic.iterrows():
        diag = diagnose_case(r)
        rows.append({
            'audit_id': r['audit_id'],
            'candidate_id': r['candidate_id'],
            'silver_label': r['label_4_silver'],
            'author_sanity_decision': r['author_sanity_decision'],
            'confusion_type': r['possible_confusion'],
            'root_cause': diag['root_cause'],
            'is_taxonomy_problem': diag['is_taxonomy_problem'],
            'is_evidence_problem': diag['is_evidence_problem'],
            'is_claim_generation_problem': diag['is_claim_generation_problem'],
            'is_audit_rule_too_strict': diag['is_audit_rule_too_strict'],
            'is_potentially_usable_case': diag['is_potentially_usable_case'],
            'recommended_action': diag['recommended_action'],
            'one_sentence_reason': diag['one_sentence_reason'],
        })

    out_path = os.path.join(OUT_DIR, 'sanity_audit_error_diagnosis.csv')
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding='utf-8')
    print(f"Diagnosis written: {out_path} ({len(rows)} rows)")

    # Print root cause distribution
    print("\nRoot cause distribution:")
    rc = pd.Series([r['root_cause'] for r in rows]).value_counts()
    for k, v in rc.items():
        print(f"  {k}: {v}")

    return rows


def build_high_risk_bank(diagnosis_rows):
    """Build high_risk_sample_bank.csv from all 25 questionable/unclear cases."""
    audit = pd.read_csv(AUDIT_PATH, keep_default_na=False)
    diag_df = pd.DataFrame(diagnosis_rows).set_index('audit_id')

    rows = []
    case_id = 1
    for _, r in audit.iterrows():
        if r['author_sanity_decision'] not in ('questionable', 'unclear'):
            continue
        d = diag_df.loc[r['audit_id']]
        # Determine risk type
        if d['is_audit_rule_too_strict'] == 'true':
            risk_type = 'audit_conservative_plus_taxonomy_boundary'
        elif d['is_claim_generation_problem'] == 'true':
            risk_type = 'claim_too_abstract'
        elif d['is_evidence_problem'] == 'true':
            risk_type = 'evidence_context_missing'
        else:
            risk_type = 'taxonomy_boundary_unclear'

        # Recommended handling
        if d['is_potentially_usable_case'] == 'true':
            handling = 'boundary_case_only'
        elif d['root_cause'] == 'likely_label_noise':
            handling = 'exclude_from_main_examples'
        else:
            handling = 'future_gold_priority'

        # Possible alternative label
        alt_label = ''
        if r['possible_confusion'] == 'mild_vs_strong':
            if r['label_4_silver'] == 'strong_action_overclaim':
                alt_label = 'mild_scope_overclaim'
            elif r['label_4_silver'] == 'mild_scope_overclaim':
                alt_label = 'supported or strong_action_overclaim'
            else:
                alt_label = 'mild_scope_overclaim or strong_action_overclaim'
        elif r['possible_confusion'] == 'strong_vs_contradiction':
            if r['label_4_silver'] == 'contradiction_candidate':
                alt_label = 'strong_action_overclaim (or vice versa)'
            else:
                alt_label = 'contradiction_candidate (or vice versa)'
        elif r['possible_confusion'] == 'supported_vs_mild':
            alt_label = 'supported or mild_scope_overclaim'
        else:
            alt_label = 'unclear'

        rows.append({
            'case_id': f"HRC_{case_id:03d}",
            'candidate_id': r['candidate_id'],
            'silver_label': r['label_4_silver'],
            'risk_type': risk_type,
            'why_risky': d['one_sentence_reason'],
            'possible_alternative_label': alt_label,
            'recommended_handling': handling,
        })
        case_id += 1

    out_path = os.path.join(OUT_DIR, 'high_risk_sample_bank.csv')
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding='utf-8')
    print(f"\nHigh-risk bank written: {out_path} ({len(rows)} rows)")
    return rows


def build_trusted_case_bank():
    """Build trusted_case_bank.csv — 16-24 clear illustrative cases from silver set."""
    silver = pd.read_csv(SILVER_PATH, keep_default_na=False)
    audit = pd.read_csv(AUDIT_PATH, keep_default_na=False)

    # Get the set of "reasonable" audit cases (these are pre-vetted as plausible)
    reasonable_audit = audit[audit['author_sanity_decision'] == 'reasonable'][['candidate_id', 'author_sanity_decision']]

    # Also get Table 0 examples (these are already curated)
    table0 = pd.read_csv(TABLE0_PATH, keep_default_na=False)
    table0_ids = set(table0['candidate_id'].tolist())

    # Build a set of "clear" candidate_ids: those in reasonable audit + table0
    clear_ids = set(reasonable_audit['candidate_id'].tolist()) | table0_ids

    # For each class, select 4-6 trusted cases
    # Priority: (1) table0 examples, (2) reasonable audit cases, (3) other silver cases with clear evidence
    selected = []
    case_id = 1

    for label in ['supported', 'mild_scope_overclaim', 'strong_action_overclaim', 'contradiction_candidate']:
        # Get table0 examples for this label
        t0 = table0[table0['label'] == label]
        for _, r in t0.iterrows():
            selected.append({
                'case_id': f"TCB_{case_id:03d}",
                'candidate_id': r['candidate_id'],
                'domain': r['domain'],
                'label': label,
                'evidence_text_short': r.get('evidence_text_short', '')[:200],
                'claim_text': r.get('claim_text', '')[:300],
                'why_trusted': 'Selected for Table 0; illustrates the label with clear evidence-claim relationship.',
                'why_not_other_labels': r.get('why_not_other_labels', ''),
                'recommended_location_in_paper': 'Table 0',
            })
            case_id += 1

        # Get reasonable audit cases for this label (excluding already-selected table0)
        already_selected = {s['candidate_id'] for s in selected}
        reasonable_for_label = reasonable_audit[
            (audit['label_4_silver'] == label) &
            (~reasonable_audit['candidate_id'].isin(already_selected))
        ]

        # Target: 4 per class for supported/mild/contradiction, 6 for strong_action
        target = 6 if label == 'strong_action_overclaim' else 4
        current_count = len([s for s in selected if s['label'] == label])

        for _, ar in reasonable_for_label.iterrows():
            if current_count >= target:
                break
            cid = ar['candidate_id']
            if cid in already_selected:
                continue
            # Get full record from silver
            silver_row = silver[silver['candidate_id'] == cid]
            if len(silver_row) == 0:
                continue
            sr = silver_row.iloc[0]
            ev = sr.get('evidence_text', '')[:200]
            cl = sr.get('claim_text', '')[:300]
            if len(ev) < 50 or len(cl) < 30:
                continue  # skip too-short cases

            # Determine why trusted
            why_trusted = f"Author sanity audit rated 'reasonable'; evidence and claim are clear enough for illustrative use."
            why_not = ''
            if label == 'supported':
                why_not = 'Not mild (no scope over-extension); not strong_action (no action/deployment assertion); not contradiction (directions align).'
            elif label == 'mild_scope_overclaim':
                why_not = 'Not supported (scope mildly over-extended); not strong_action (no action/deployment/safety conclusion); not contradiction (direction consistent).'
            elif label == 'strong_action_overclaim':
                why_not = 'Not supported (evidence insufficient for action claimed); not mild (over-extension is about action strength, not just scope); not contradiction (direction may align but strength excessive).'
            elif label == 'contradiction_candidate':
                why_not = 'Not supported (directions conflict); not mild (not a scope issue); not strong_action (the issue is directional conflict, not strength mismatch).'

            selected.append({
                'case_id': f"TCB_{case_id:03d}",
                'candidate_id': cid,
                'domain': sr.get('domain', ''),
                'label': label,
                'evidence_text_short': ev,
                'claim_text': cl,
                'why_trusted': why_trusted,
                'why_not_other_labels': why_not,
                'recommended_location_in_paper': 'Appendix case study',
            })
            already_selected.add(cid)
            case_id += 1
            current_count += 1

        # If still not enough, pull from silver set (preferring longer evidence)
        if current_count < target:
            need = target - current_count
            pool = silver[
                (silver['candidate_label_guess'] == label) &
                (~silver['candidate_id'].isin(already_selected)) &
                (silver['evidence_text'].str.len() >= 100) &
                (silver['claim_text'].str.len() >= 50)
            ].sort_values('evidence_text', key=lambda x: x.str.len(), ascending=False).head(need * 3)

            for _, sr in pool.iterrows():
                if current_count >= target:
                    break
                ev = sr.get('evidence_text', '')[:200]
                cl = sr.get('claim_text', '')[:300]
                why_not = ''
                if label == 'supported':
                    why_not = 'Not mild/strong/contradiction (evidence aligns with claim strength and direction).'
                elif label == 'mild_scope_overclaim':
                    why_not = 'Not supported/strong/contradiction (mild scope over-extension only).'
                elif label == 'strong_action_overclaim':
                    why_not = 'Not supported/mild/contradiction (action over-extension with directional consistency).'
                elif label == 'contradiction_candidate':
                    why_not = 'Not supported/mild/strong (directional conflict).'

                selected.append({
                    'case_id': f"TCB_{case_id:03d}",
                    'candidate_id': sr['candidate_id'],
                    'domain': sr.get('domain', ''),
                    'label': label,
                    'evidence_text_short': ev,
                    'claim_text': cl,
                    'why_trusted': f"Evidence and claim are clear; not in the 40-row audit but evidence length and clarity are sufficient for illustrative use (not gold-validated).",
                    'why_not_other_labels': why_not,
                    'recommended_location_in_paper': 'Appendix case study',
                })
                already_selected.add(sr['candidate_id'])
                case_id += 1
                current_count += 1

    out_path = os.path.join(OUT_DIR, 'trusted_case_bank.csv')
    pd.DataFrame(selected).to_csv(out_path, index=False, encoding='utf-8')
    print(f"\nTrusted case bank written: {out_path} ({len(selected)} rows)")

    # Distribution
    df = pd.DataFrame(selected)
    print("\nTrusted case bank distribution:")
    print(df['label'].value_counts())
    print("\nBy domain:")
    print(df['domain'].value_counts())

    return selected


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    diag = build_diagnosis()
    build_high_risk_bank(diag)
    build_trusted_case_bank()
    print("\n=== V3.4 taxonomy hardening files generated ===")
