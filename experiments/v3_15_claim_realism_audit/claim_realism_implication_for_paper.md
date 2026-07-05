# Claim Realism Audit: Implications for Paper Narrative

**Task:** V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring
**Date:** 2026-07-05
**Companion files:** `claim_realism_audit_summary.md`, `claim_realism_audit_queue.csv`, `claim_realism_group_audit.csv`, `claim_realism_audit_gate.json`

---

## Q1. Can SimClaim still serve as a controlled diagnostic set?

**Answer: YES — but with explicit realism caveats.** Based on this automatic audit, 0/444 (0.0%) claims are flagged high-risk and 0/111 (0.0%) groups are flagged high-risk. The high-risk rate is non-trivial but does NOT invalidate the diagnostic-set purpose, because:

1. **SimClaim was designed as a controlled counterfactual diagnostic set, not a naturalistic corpus.** The 1:1:1:1 balanced design and the same-evidence-four-variants construction are deliberate, intended to stress-test R4's boundary-recognition ability under controlled conditions. Realism is a quality dimension, not the design goal.
2. **The audit flags are heuristic, not validated.** A high heuristic risk flag does NOT mean the claim is unrealistic — it means the claim matches a pattern that *might* be unrealistic. Gold validation is required to confirm.
3. **Even high-risk claims retain diagnostic value.** A claim that is 'too_extreme' or 'strong_action_too_forced' is still a valid test of whether R4 can detect overclaim language — the test is whether R4 flags it, not whether the claim is naturalistic.

**Conditional continued use:** SimClaim remains usable as a controlled diagnostic set provided that:
- The paper explicitly labels it as 'controlled counterfactual diagnostic set, not naturalistic corpus.'
- The paper discloses the realism audit results (high-risk rate, per-label risk) in the Limitations section.
- High-risk claims are excluded from illustrative examples in the paper body.
- The gold pilot protocol (already frozen) includes realism_score_1_to_5 as Layer 2 to validate the audit.
- No claim is made about real-world prevalence based on SimClaim.

---

## Q2. Which claims are unsuitable as paper illustrative examples?

**Answer: 0 claims are flagged `exclude_from_paper_examples`** (high risk + extreme/templated wording). These should NOT appear as worked examples in the paper body, introduction, or discussion.

Additionally, all `prioritize_gold_realism` claims (high risk) should be avoided as paper examples until gold validation confirms their realism.

**Recommended pool for paper illustrative examples:**
- Use only `low` risk claims (289 available, per-label distribution above).
- Select examples across all 4 labels and multiple domains for balance.
- Even low-risk claims should pass a final human sanity check before being placed in the paper body.
- Avoid using the same evidence group's 4 claims as a 'quartet example' if the group is flagged `high` risk.

---

## Q3. Is realism_score mandatory in the paper?

**Answer: YES — realism_score_1_to_5 must be added to the gold pilot protocol.** This audit found 0.0% high-risk claims heuristically, but the audit is rule-based and cannot substitute for human judgment. Without realism gold, the paper cannot defend against the reviewer concern that 'AI-generated counterfactual claims are templated and unrealistic.'

**Required actions:**
1. **gold_pilot_protocol_freeze_v1 Layer 2 (already planned):** Annotators assign `claim_realism_score_1_to_5` for each pilot claim (1=very realistic, 5=very unrealistic).
2. **Pre-registered thresholds (already in protocol):** 25% class-level, 25% paper-level — if exceeded, paper claim must be downgraded.
3. **Audit-to-gold cross-check:** After gold pilot, compare heuristic risk_score to gold realism_score to calibrate the heuristic rules. If correlation is weak, the heuristic audit should be reported as exploratory, not definitive.
4. **Paper reporting:** Report both the automatic audit results (this file) and the gold realism results (after pilot) in the Limitations section.

---

## Q4. If realism risk is high, how should the paper be downgraded?

**Answer:** Downgrade is conditional on gold pilot outcomes. The pre-registered downgrade path is:

**Scenario A — gold pilot realism is acceptable** (class-level high-realism rate < 25% AND paper-level < 25%):
- No downgrade needed.
- Report audit + gold realism results in Limitations.
- SimClaim remains 'controlled counterfactual diagnostic set.'

**Scenario B — gold pilot realism is borderline** (class-level 25-40% OR paper-level 25-40%):
- Downgrade paper claim from 'SimClaim is a controlled diagnostic set' to 'SimClaim is a controlled diagnostic set with realism caveats; X% of claims were judged unrealistic by human annotators.'
- Restrict quantitative claims to per-class metrics on gold-validated subset.
- Add explicit Limitations paragraph on realism threats to external validity.

**Scenario C — gold pilot realism is poor** (class-level > 40% OR paper-level > 40%):
- Major downgrade: SimClaim is 'a synthetic counterfactual probe, not a diagnostic set.'
- All R4/LLM metrics on SimClaim are reported as 'probe-stage results pending naturalistic corpus validation.'
- Add a 'Threats to Validity' section.
- Consider delaying submission until a naturalistic corpus study is completed.

**Current state:** Gold pilot annotation has NOT begun (protocol frozen 2026-07-04). The paper cannot commit to Scenario A/B/C until gold realism data exists. V3.14 paper should report the audit results and pre-register the downgrade path.

---

## Q5. How to explain the legitimacy of synthetic counterfactual claims?

**Answer:** The paper should explicitly justify the counterfactual construction in the Data section. Recommended framing:

### Paste-ready paragraph for paper §V (Data)

> SimClaim is a controlled counterfactual diagnostic set constructed by generating four claim variants per evidence span: a faithful *supported* claim, a *mild_scope_overclaim* that slightly over-extends the evidence scope, a *strong_action_overclaim* that aggressively extrapolates to deployment/safety/policy implications, and a *contradiction_candidate* that reverses a key evidence assertion. The four-variant design is deliberate: it provides balanced 1:1:1:1 coverage of the four evidence-sufficiency relations, enabling per-class boundary-recognition evaluation that would be impossible on a naturalistic corpus where `strong_action_overclaim` and `contradiction_candidate` are rare. The construction is *not* intended to represent the natural prevalence of these relations in real scientific writing; a complementary low-prevalence screening simulation (§VIII.D.E) evaluates deployment-stage screening behavior under realistic class imbalance. SimClaim's evidence spans are sourced from real peer-reviewed papers across six domains (autonomous driving, policy simulation, digital twin, cyber defense, multi-agent reinforcement learning, robotics), ensuring that the *evidence* side of each claim-evidence pair is realistic; only the *claims* are synthetic counterfactuals. An automatic author-side realism audit (§IX Limitations) flagged X% of claims as high-realism-risk heuristically; a two-layer gold pilot protocol (§VII.J) is pre-registered to validate both relation labels (Layer 1) and claim realism (Layer 2, `claim_realism_score_1_to_5`) against human judgment, with pre-registered downgrade thresholds (25% class-level, 25% paper-level).

### Key points the paper must make

1. **Counterfactual by design, not by accident.** The four-variant construction is a deliberate diagnostic tool, not a data-quality failure.
2. **Evidence is real, claims are synthetic.** This is the inverse of many NLP datasets where claims are real but evidence is retrieved; here we hold evidence fixed and vary claims to isolate claim-side reasoning.
3. **Diagnostic ≠ naturalistic.** SimClaim answers 'can R4 recognize the boundary?' not 'what is the prevalence of strong_action overclaim in real scientific writing?'
4. **Realism is audited and will be gold-validated.** The audit is reported transparently; the gold pilot will quantify realism empirically.
5. **Low-prevalence simulation complements SimClaim.** Together they answer both boundary-recognition and deployment-screening questions.

---

## Q6. Summary of paper-edit recommendations

| Section | Edit | Status |
| --- | --- | --- |
| §V (Data) | Add paste-ready counterfactual-construction paragraph above | Pending V3.16 |
| §VII.J (Gold protocol) | Confirm Layer 2 realism_score is included (already in gold_pilot_protocol_freeze_v1) | Already in V3.13/V3.14 |
| §VIII.D.E (Low-prev sim) | Cross-reference realism audit | Already in V3.15 |
| §IX (Limitations) | Add realism audit summary + downgrade path (Scenarios A/B/C) | Pending V3.16 |
| §VI.B/C (Results) | Use only low-risk claims as illustrative examples | Pending V3.16 |

**Note:** The current V3.14 paper is NOT modified by this audit. All recommendations are pending V3.16 integration after gold pilot begins.
