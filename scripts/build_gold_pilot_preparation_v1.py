"""Build Gold Pilot Preparation Pack v1.

Generates 50 candidate samples for gold pilot annotation:
- 25 high-risk boundary cases (from high_risk_sample_bank.csv)
- 16 trusted illustrative cases (4 per class, from trusted_case_bank.csv)
- 9 random strict silver cases (from strict_silver_max_candidates_v1.csv, excluding above)

Does NOT fill gold_label, final_label, or human_audited.
Does NOT run models, APIs, or training.
"""
import csv
import os
import random
from collections import defaultdict

# Input paths
HIGH_RISK_CSV = r"D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\high_risk_sample_bank.csv"
TRUSTED_CSV = r"D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\trusted_case_bank.csv"
STRICT_SILVER_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"

# Output directory
OUT_DIR = r"D:\ocn\gold_pilot_preparation_v1"
os.makedirs(OUT_DIR, exist_ok=True)


def read_csv(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_strict_silver():
    """Read strict silver CSV with keep_default_na=False semantics."""
    rows = []
    with open(STRICT_SILVER_CSV, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_silver_lookup(strict_silver_rows):
    """Build candidate_id -> row lookup."""
    lookup = {}
    for row in strict_silver_rows:
        cid = row.get('candidate_id', '')
        if cid:
            lookup[cid] = row
    return lookup


def select_trusted_16(trusted_rows, audit_rows):
    """Select 16 trusted cases (4 per class), preferring clean cases."""
    # Build audit lookup: candidate_id -> problem_found
    audit_lookup = {}
    for a in audit_rows:
        cid = a.get('candidate_id', '')
        if cid:
            audit_lookup[cid] = a

    # Group trusted by label
    by_label = defaultdict(list)
    for t in trusted_rows:
        label = t.get('label', '')
        by_label[label].append(t)

    # Also include TCB_NEW_MILD_2 (G170-C02) which is in V3.6 table but may not be in trusted_case_bank
    # We'll handle G170-C02 separately if needed

    selected = []
    # Supported: TCB_001, TCB_002, TCB_003, TCB_004 (all clean)
    for t in by_label.get('supported', []):
        selected.append(t)
        if len([s for s in selected if s.get('label') == 'supported']) >= 4:
            break

    # Mild: prefer clean ones, include TCB_005 (with note) if needed
    mild_candidates = by_label.get('mild_scope_overclaim', [])
    # Sort: clean (no/ok) first
    mild_sorted = sorted(mild_candidates, key=lambda x: (
        audit_lookup.get(x.get('candidate_id', ''), {}).get('problem_found', 'yes') == 'yes',
        audit_lookup.get(x.get('candidate_id', ''), {}).get('severity', 'fatal') == 'fatal_for_example'
    ))
    for t in mild_sorted:
        selected.append(t)
        if len([s for s in selected if s.get('label') == 'mild_scope_overclaim']) >= 4:
            break

    # If we don't have 4 mild from trusted_case_bank, add G170-C02 manually
    mild_count = len([s for s in selected if s.get('label') == 'mild_scope_overclaim'])
    if mild_count < 4:
        # Add G170-C02 as a trusted mild case (it's the V3.6 replacement)
        g170 = {
            'case_id': 'TCB_NEW_MILD_2',
            'candidate_id': 'SBV2-ALL92-G170-C02',
            'domain': 'robotics',
            'label': 'mild_scope_overclaim',
            'evidence_text_short': 'In multi-task generalization experiments, our method achieves a success rate of 83% on trained tasks and 75% on unseen tasks in simulation.',
            'claim_text': 'In simulation, GRaD-Nav++ reports success rates of 83% on trained tasks and 75% on unseen multi-stage tasks during evaluation.',
            'why_trusted': 'V3.6 replacement for TCB_008; clean scope-expansion case (numbers match, only scope adjective added).',
        }
        selected.append(g170)

    # Strong: prefer clean ones
    strong_candidates = by_label.get('strong_action_overclaim', [])
    strong_sorted = sorted(strong_candidates, key=lambda x: (
        audit_lookup.get(x.get('candidate_id', ''), {}).get('problem_found', 'yes') == 'yes',
        'fatal' in audit_lookup.get(x.get('candidate_id', ''), {}).get('severity', 'fatal')
    ))
    for t in strong_sorted:
        # Skip TCB_013 (G214-C03) which had fatal issue
        cid = t.get('candidate_id', '')
        audit = audit_lookup.get(cid, {})
        if audit.get('severity') == 'fatal_for_example' or audit.get('final_decision') == 'exclude_from_V3_6':
            continue
        selected.append(t)
        if len([s for s in selected if s.get('label') == 'strong_action_overclaim']) >= 4:
            break

    # Contradiction: all 4
    for t in by_label.get('contradiction_candidate', []):
        selected.append(t)
        if len([s for s in selected if s.get('label') == 'contradiction_candidate']) >= 4:
            break

    return selected[:16]


def select_random_9(strict_silver_rows, exclude_ids):
    """Select 9 random cases from strict silver, excluding already-used IDs."""
    available = [r for r in strict_silver_rows if r.get('candidate_id', '') not in exclude_ids]
    # Ensure domain diversity
    by_domain = defaultdict(list)
    for r in available:
        domain = r.get('domain', 'unknown')
        by_domain[domain].append(r)

    # Try to pick from different domains
    random.seed(42)
    selected = []
    domains = list(by_domain.keys())
    random.shuffle(domains)

    # Round 1: pick one from each domain
    for d in domains:
        if len(selected) >= 9:
            break
        if by_domain[d]:
            pick = random.choice(by_domain[d])
            selected.append(pick)
            by_domain[d].remove(pick)

    # Round 2: fill remaining from any domain
    pool = []
    for d in domains:
        pool.extend(by_domain[d])
    random.shuffle(pool)
    for r in pool:
        if len(selected) >= 9:
            break
        selected.append(r)

    return selected[:9]


def get_full_text(silver_lookup, candidate_id):
    """Get full evidence_text and claim_text from strict silver lookup."""
    row = silver_lookup.get(candidate_id, {})
    return (
        row.get('evidence_text', ''),
        row.get('claim_text', ''),
        row.get('domain', ''),
        row.get('candidate_label_guess', ''),
    )


def build_candidate_50(high_risk_rows, trusted_16, random_9, silver_lookup):
    """Build the 50-row candidate CSV."""
    rows = []
    pilot_id = 1

    # 25 high-risk boundary cases
    for h in high_risk_rows:
        cid = h.get('candidate_id', '')
        evi, claim, domain, _ = get_full_text(silver_lookup, cid)
        silver_label = h.get('silver_label', '')
        risk_type = h.get('risk_type', '')
        why = h.get('why_risky', '')

        # Determine boundary_type
        boundary_map = {
            'claim_too_abstract': 'mild_vs_strong',
            'taxonomy_boundary_unclear': 'mild_vs_strong',
            'audit_conservative_plus_taxonomy_boundary': 'strong_vs_contradiction',
            'evidence_context_missing': 'supported_vs_mild',
        }
        boundary = boundary_map.get(risk_type, 'other_boundary')

        rows.append({
            'pilot_id': f'P{pilot_id:03d}',
            'candidate_id': cid,
            'domain': domain or h.get('domain', ''),
            'evidence_text': evi,
            'claim_text': claim,
            'silver_label_hidden_or_visible': 'visible_in_internal_version_only',
            'sample_source': 'high_risk_sample_bank',
            'boundary_type': boundary,
            'why_selected': f"High-risk boundary case ({risk_type}): {why}",
            'do_not_use_as_gold_yet': 'true',
        })
        pilot_id += 1

    # 16 trusted illustrative cases
    for t in trusted_16:
        cid = t.get('candidate_id', '')
        evi, claim, domain, _ = get_full_text(silver_lookup, cid)
        label = t.get('label', '')
        why = t.get('why_trusted', '')

        rows.append({
            'pilot_id': f'P{pilot_id:03d}',
            'candidate_id': cid,
            'domain': domain or t.get('domain', ''),
            'evidence_text': evi,
            'claim_text': claim,
            'silver_label_hidden_or_visible': 'visible_in_internal_version_only',
            'sample_source': 'trusted_case_bank',
            'boundary_type': 'clear_illustrative',
            'why_selected': f"Trusted illustrative case ({label}): {why}",
            'do_not_use_as_gold_yet': 'true',
        })
        pilot_id += 1

    # 9 random strict silver cases
    for r in random_9:
        cid = r.get('candidate_id', '')
        evi = r.get('evidence_text', '')
        claim = r.get('claim_text', '')
        domain = r.get('domain', '')
        label = r.get('candidate_label_guess', '')

        rows.append({
            'pilot_id': f'P{pilot_id:03d}',
            'candidate_id': cid,
            'domain': domain,
            'evidence_text': evi,
            'claim_text': claim,
            'silver_label_hidden_or_visible': 'visible_in_internal_version_only',
            'sample_source': 'random_strict_silver',
            'boundary_type': 'random_sample',
            'why_selected': f"Random strict silver sample ({label}) for representativeness check; not pre-screened as boundary.",
            'do_not_use_as_gold_yet': 'true',
        })
        pilot_id += 1

    return rows


def write_csv(path, rows, fieldnames):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    print("Reading input files...")
    high_risk_rows = read_csv(HIGH_RISK_CSV)
    trusted_rows = read_csv(TRUSTED_CSV)
    audit_rows = read_csv(r"D:\ocn\paper_versions_ordered\V3_6_case_figure_integrity_checked\case_integrity_audit.csv")
    strict_silver_rows = read_strict_silver()

    print(f"  high_risk: {len(high_risk_rows)} rows")
    print(f"  trusted: {len(trusted_rows)} rows")
    print(f"  audit: {len(audit_rows)} rows")
    print(f"  strict_silver: {len(strict_silver_rows)} rows")

    silver_lookup = build_silver_lookup(strict_silver_rows)
    print(f"  silver_lookup: {len(silver_lookup)} entries")

    # Select 16 trusted
    trusted_16 = select_trusted_16(trusted_rows, audit_rows)
    print(f"  trusted_16 selected: {len(trusted_16)}")

    # Collect exclude IDs
    exclude_ids = set()
    for h in high_risk_rows:
        exclude_ids.add(h.get('candidate_id', ''))
    for t in trusted_16:
        exclude_ids.add(t.get('candidate_id', ''))

    # Select 9 random
    random_9 = select_random_9(strict_silver_rows, exclude_ids)
    print(f"  random_9 selected: {len(random_9)}")

    # Build 50 candidates
    candidates = build_candidate_50(high_risk_rows, trusted_16, random_9, silver_lookup)
    print(f"  total candidates: {len(candidates)}")

    # Verify all candidate_ids have evidence/claim text
    missing_text = 0
    for c in candidates:
        if not c['evidence_text'] or not c['claim_text']:
            missing_text += 1
            print(f"  WARNING: missing text for {c['pilot_id']} / {c['candidate_id']}")
    print(f"  missing_text: {missing_text}")

    # Write gold_pilot_candidate_50.csv
    candidate_fields = [
        'pilot_id', 'candidate_id', 'domain', 'evidence_text', 'claim_text',
        'silver_label_hidden_or_visible', 'sample_source', 'boundary_type',
        'why_selected', 'do_not_use_as_gold_yet',
    ]
    write_csv(os.path.join(OUT_DIR, 'gold_pilot_candidate_50.csv'), candidates, candidate_fields)
    print(f"Wrote gold_pilot_candidate_50.csv ({len(candidates)} rows)")

    # Build annotator templates (without silver_label)
    annotator_fields = [
        'pilot_id', 'candidate_id', 'domain', 'evidence_text', 'claim_text',
        'annotator_label', 'confidence_1_to_5', 'rationale_one_sentence',
        'confusion_if_any', 'needs_adjudication',
    ]
    annotator_a_rows = []
    annotator_b_rows = []
    for c in candidates:
        base = {
            'pilot_id': c['pilot_id'],
            'candidate_id': c['candidate_id'],
            'domain': c['domain'],
            'evidence_text': c['evidence_text'],
            'claim_text': c['claim_text'],
            'annotator_label': '',
            'confidence_1_to_5': '',
            'rationale_one_sentence': '',
            'confusion_if_any': '',
            'needs_adjudication': '',
        }
        annotator_a_rows.append(base.copy())
        annotator_b_rows.append(base.copy())

    write_csv(os.path.join(OUT_DIR, 'annotator_A_template.csv'), annotator_a_rows, annotator_fields)
    write_csv(os.path.join(OUT_DIR, 'annotator_B_template.csv'), annotator_b_rows, annotator_fields)
    print(f"Wrote annotator_A_template.csv and annotator_B_template.csv ({len(annotator_a_rows)} rows each)")

    # Build adjudication template
    adj_fields = [
        'pilot_id', 'candidate_id', 'annotator_A_label', 'annotator_B_label',
        'agreement', 'adjudicated_label', 'adjudication_reason',
        'boundary_type', 'final_use_recommendation',
    ]
    adj_rows = []
    for c in candidates:
        adj_rows.append({
            'pilot_id': c['pilot_id'],
            'candidate_id': c['candidate_id'],
            'annotator_A_label': '',
            'annotator_B_label': '',
            'agreement': '',
            'adjudicated_label': '',
            'adjudication_reason': '',
            'boundary_type': c['boundary_type'],
            'final_use_recommendation': '',
        })
    write_csv(os.path.join(OUT_DIR, 'adjudication_template.csv'), adj_rows, adj_fields)
    print(f"Wrote adjudication_template.csv ({len(adj_rows)} rows)")

    # Print summary
    print("\n=== Summary ===")
    by_source = defaultdict(int)
    by_domain = defaultdict(int)
    by_boundary = defaultdict(int)
    for c in candidates:
        by_source[c['sample_source']] += 1
        by_domain[c['domain']] += 1
        by_boundary[c['boundary_type']] += 1

    print("By source:")
    for k, v in sorted(by_source.items()):
        print(f"  {k}: {v}")
    print("By domain:")
    for k, v in sorted(by_domain.items()):
        print(f"  {k}: {v}")
    print("By boundary_type:")
    for k, v in sorted(by_boundary.items()):
        print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
