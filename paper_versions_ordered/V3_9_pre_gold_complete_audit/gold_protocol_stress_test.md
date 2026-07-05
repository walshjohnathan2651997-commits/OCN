# Gold Protocol Stress Test — V3.9

**Audit date:** 2026-07-04
**Target:** `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\gold_validation_protocol_section.md`
**Method:** Read-only audit of the frozen gold validation protocol. No modification of the protocol file.

## Summary

The gold validation protocol is **well-designed for a pilot** but has **four stress points** that an advisor or reviewer would likely question. None of these are fatal — they are thresholds and framings that need explicit defense. The protocol does NOT have a "if gold is bad, the whole paper collapses" risk because the downgrade criteria are pre-registered and graduated (not all-or-nothing).

| Stress Point | Severity | Fixable Without New Experiments? |
| --- | --- | --- |
| 50 samples is too small for confirmatory claims | Major | Yes — set expectations explicitly |
| mild_vs_strong κ threshold (0.40) may be too strict | Major | Yes — add exploratory band |
| Downgrade criterion 6 (≥5/50 taxonomy_revision_needed) is very sensitive | Medium | Yes — add nuance |
| Success criteria are all-or-nothing (ALL must hold) | Medium | Yes — add partial-success tier |

---

## Q1 — Are The Success Criteria Reasonable?

### Overall agreement ≥ 0.70
**Assessment:** Reasonable for a four-class task with boundary cases. FEVER-style datasets report 0.70-0.85 agreement. However, 0.70 on a 50-sample pilot with 25 high-risk cases is a high bar — the high-risk oversampling will depress agreement. A reviewer may argue: "You oversampled the hardest cases, then set a threshold that doesn't account for that."

**Recommendation:** Add a note: "The 0.70 threshold is computed on the full 50-sample pilot, which includes 25 high-risk boundary cases. Agreement on the 25 high-risk subset is expected to be lower; agreement on the 25 trusted+random subset is expected to be higher. Both sub-agreements are reported in Table G1."

### Cohen's kappa ≥ 0.45
**Assessment:** Reasonable. κ ≥ 0.45 is the lower bound of "moderate agreement" (Landis & Koch 1977). For a four-class task with inherently fuzzy boundaries, this is the right floor. Below 0.45 means annotators agree mostly by chance.

**Recommendation:** Keep as-is. Add the Landis & Koch reference.

### mild_vs_strong κ ≥ 0.40
**Assessment:** This is the most consequential threshold. The paper's central contribution depends on strong_action_overclaim being a reliably drawable class. κ ≥ 0.40 is the lower bound of "moderate agreement." But for the *hardest boundary in the taxonomy* (75% confusion rate in the author audit), 0.40 may be too strict — even good annotators might land at 0.35-0.45 on this boundary.

**Recommendation:** Add an exploratory band: "κ ≥ 0.40 = pass; κ = 0.30–0.40 = exploratory (taxonomy survives but with explicit 'mild_vs_strong boundary is fuzzy' caveat in the paper); κ < 0.30 = fail (taxonomy must be revised)." This three-tier framing is more defensible than a binary pass/fail at 0.40.

### strong_action retention ≥ 0.60
**Assessment:** Reasonable. If gold re-labels more than 40% of silver strong_action cases to something else, the silver-stage finding is about a different class. 0.60 is a sensible floor.

**Recommendation:** Keep as-is.

### LLM strong recall ≤ 0.20
**Assessment:** Reasonable. Pre-gold LLM strong recall is 0.04. If gold moves it to 0.20, the under-detection pattern is weaker but still present. Above 0.20, the claim is downgraded.

**Recommendation:** Keep as-is. Note that this threshold applies to ALL four LLM conditions (GPT standard, GPT decision-tree, GPT few-shot, DeepSeek). If any one exceeds 0.20, the claim is downgraded per criterion 3.

### R4 false positives per true positive ≤ 10
**Assessment:** This is a generous threshold. R4 currently produces 98+24 = 122 false positives. If gold confirms ~25 true strong_action cases in the 100-sample set, the FP/TP ratio is ~122/25 ≈ 4.9. The threshold of 10 gives substantial headroom. A reviewer may argue this is too lenient.

**Recommendation:** Tighten to ≤ 5 for the screening claim, or add: "≤ 5 = screening viable; 5-10 = screening viable with human-in-the-loop; > 10 = screening not viable." Three tiers are more informative than a single cutoff.

---

## Q2 — Are The Downgrade Criteria Too Easy To Self-Destruct?

### Downgrade criterion 1 (mild_vs_strong κ < 0.40 → taxonomy revision)
**Assessment:** This is the biggest self-destruct risk. The author audit shows 12/25 questionable/unclear cases are mild_vs_strong boundary cases. If annotators disagree on even a few of these, κ could easily land below 0.40. The criterion is honest but risky.

**Recommendation:** Add the three-tier band (see Q1 recommendation). The current binary criterion forces a taxonomy revision if κ = 0.39, which is too sensitive. A κ of 0.35-0.40 should trigger a "taxonomy revision review" not an automatic revision.

### Downgrade criterion 2 (strong_action retention < 0.50 → paper claim downgraded)
**Assessment:** Reasonable. If gold moves half the strong_action cases to mild, the paper's central class is not stable.

**Recommendation:** Keep as-is.

### Downgrade criterion 3 (GPT few-shot or decision-tree strong_F1 ≥ 0.20 → under-detection downgraded)
**Assessment:** This is a **trap for the authors**. The pre-gold strong_F1 is 0.0769. If a different prompt design achieves 0.20, that's still quite low (recall ~0.15-0.20). But the criterion triggers a downgrade at 0.20, which is a low bar for "fixing" the problem. A reviewer might argue: "You set the downgrade threshold so low that any prompt improvement triggers it, which means you're committed to the under-detection claim regardless of evidence."

**Recommendation:** Raise the threshold to ≥ 0.30 (closer to R4's 0.3000) or add: "≥ 0.30 = under-detection claim downgraded; 0.20-0.30 = under-detection claim weakened but retained; < 0.20 = under-detection claim supported." The current 0.20 threshold is too easy to trigger.

### Downgrade criterion 4 (R4 FP/TP > 10 → screening downgraded)
**Assessment:** See Q1 — 10 is generous. But as a downgrade trigger, it's fine because it only downgrades the screening use case, not the whole paper.

**Recommendation:** Keep as-is, but tighten the threshold to > 5 per the Q1 recommendation.

### Downgrade criterion 5 (hybrid gives no screening gain → complementarity downgraded)
**Assessment:** Reasonable. If LLM+R4 hybrid doesn't improve over R4 alone, the complementarity claim is weakened.

**Recommendation:** Keep as-is. Note that this criterion depends on the hybrid design (how LLM and R4 are combined), which is not specified in the protocol. Add: "The hybrid design is: LLM judge for supported/mild/contradiction (where LLM is strong), R4 for strong_action (where R4 is strong). If a different hybrid design is used, the criterion must be re-specified."

### Downgrade criterion 6 (≥5/50 taxonomy_revision_needed → taxonomy revision required)
**Assessment:** This is **too sensitive**. 5/50 = 10%. In a 50-sample pilot with 25 high-risk boundary cases, getting 5 taxonomy_revision_needed flags is quite likely. This criterion could trigger even if the overall kappa is fine.

**Recommendation:** Change to: "≥ 10/50 taxonomy_revision_needed → taxonomy revision required. 5-9/50 → taxonomy revision review (case-by-case examination, not automatic revision)." The current 5/50 threshold is too easy to trigger.

---

## Q3 — Is 50 Samples Enough For The Paper's Positioning?

**Assessment:** No, 50 samples is **not enough for confirmatory claims**, but it **is enough for pilot diagnostic claims**. The paper currently positions itself as a "pilot diagnostic study" — 50 samples is appropriate for that positioning.

**Risk:** If the advisor/reviewer expects confirmatory validation, 50 samples will be rejected as insufficient. The paper must be explicit that 50 samples is a pilot to detect fatal problems, not a confirmatory study.

**Recommendation:** Add to §VII.F: "The 50-sample pilot is designed to detect fatal taxonomy problems (κ < 0.30, retention < 0.40), not to confirm the taxonomy. A confirmatory study (300–500 independently adjudicated pairs) is a separate follow-up effort. If the 50-sample pilot passes the success criteria, the paper proceeds to the confirmatory study; if it fails, the taxonomy is revised first. The 50-sample pilot cannot support claims like 'the four-class taxonomy is validated' — it can only support 'the four-class taxonomy survived a 50-sample pilot stress test.'"

---

## Q4 — Which Thresholds Would An Advisor Question?

| Threshold | Advisor Likely Question | Recommended Response |
| --- | --- | --- |
| mild_vs_strong κ ≥ 0.40 | "Why 0.40 and not 0.30? The boundary is the hardest one." | "0.40 is the Landis & Koch lower bound for 'moderate agreement.' Below that, the boundary is not reliably drawable. We add an exploratory band 0.30-0.40." |
| strong_action retention ≥ 0.60 | "Why 0.60? If gold moves 35% of cases, the class is still mostly intact." | "0.60 means at least 60% of silver strong_action cases remain strong_action under gold. Below 0.50, the majority of cases shift, meaning the silver-stage finding is about a different class." |
| LLM strong recall ≤ 0.20 | "Why 0.20? Pre-gold is 0.04. That's a 5x headroom." | "0.20 is the threshold above which the under-detection pattern is no longer the dominant behavior. 0.04 → 0.20 is a 5x improvement, which would indicate the problem is prompt-fixable." |
| FP/TP ≤ 10 | "Why 10? That's a lot of false positives." | "Agreed. We tighten to ≤ 5 for the screening claim, with 5-10 as 'human-in-the-loop required.'" |
| 5/50 taxonomy_revision_needed | "5 out of 50 is 10%. That's very sensitive." | "Agreed. We change to 10/50 for automatic revision, with 5-9 as a review trigger." |
| 50 samples total | "Why not 100 or 200?" | "50 is a pilot to detect fatal problems. 200+ is a confirmatory study, which is the next step if the pilot passes." |

---

## Q5 — Which Conditions Should Be Exploratory Rather Than Confirmatory?

The following should be framed as **exploratory** (informative but not pass/fail):

1. **supported_vs_mild κ.** This is the weakest boundary (silver-stage mild-F1 = 0.1266). Low κ here is expected and does not invalidate the taxonomy. Already marked "informational" in the CSV — good.

2. **Krippendorff's α.** Already marked "optional" — good.

3. **mild_to_strong shift and strong_to_mild shift.** These are directional indicators, not pass/fail criteria. Already marked "informational" — good.

4. **GPT decision-tree prompt and GPT few-shot prompt results.** These are new prompt designs tested only on the gold subset. They should be framed as "exploratory prompt variants" not as "confirmatory test of the under-detection claim." Currently Table G3 lists them as methods with success_or_downgrade status — this is fine, but the paper should note these are exploratory.

5. **LLM+R4 hybrid.** The hybrid design is not specified in the protocol. The hybrid result should be exploratory (informative for the complementarity claim) rather than confirmatory.

**Recommendation:** Add a column to Table G3 or a note in §VII.E: "Methods marked 'exploratory' (GPT decision-tree, GPT few-shot, LLM+R4 hybrid) are reported for information; they do not trigger pass/fail criteria on their own but may inform downgrade decisions per §VII.G."

---

## Q6 — Is There A "If Gold Is Bad, The Whole Paper Collapses" Risk?

**Assessment:** **No, but close.** The paper has a graduated downgrade ladder, not a single collapse point:

| Gold Outcome | Paper Impact |
| --- | --- |
| All success criteria pass | Paper proceeds to confirmatory study with gold-validated numbers |
| mild_vs_strong κ < 0.30 | Taxonomy revised to 3 classes; paper re-framed (major but not fatal) |
| strong_action retention < 0.40 | Paper claim downgraded from "action overclaim" to "scope overclaim" (major but not fatal) |
| GPT few-shot fixes strong_action (≥ 0.30) | Under-detection claim downgraded to "prompt-specific" (major but not fatal) |
| All three happen at once | Paper collapses — the four-class taxonomy, the strong_action finding, and the LLM under-detection pattern all fail simultaneously |

**The collapse risk is the simultaneous failure of multiple criteria.** If only one criterion fails, the paper can be downgraded and resubmitted. If all three fail, the paper's core contribution is gone.

**Recommendation:** Add to §VII.G: "If multiple downgrade criteria trigger simultaneously (e.g., mild_vs_strong κ < 0.30 AND strong_action retention < 0.40 AND GPT few-shot fixes strong_action), the paper's core contribution is not viable. In this case, the silver-stage findings are reported as a negative result: the four-class evidence-sufficiency taxonomy was proposed and tested, but gold adjudication did not support it. This is a valid scientific outcome, not a paper failure."

This framing pre-empts the "collapse" risk by treating it as a pre-registered negative result, not a disaster.

---

## Summary Of Recommended Protocol Revisions (For Advisor Review, Not For Implementation)

1. Add three-tier band for mild_vs_strong κ: ≥0.40 pass / 0.30-0.40 exploratory / <0.30 fail.
2. Tighten FP/TP threshold from ≤10 to ≤5 (with 5-10 as "human-in-the-loop").
3. Raise downgrade criterion 3 threshold from 0.20 to 0.30 (with 0.20-0.30 as "weakened but retained").
4. Change downgrade criterion 6 from 5/50 to 10/50 (with 5-9 as "review trigger").
5. Add explicit "exploratory" labeling for GPT decision-tree, GPT few-shot, LLM+R4 hybrid in Table G3.
6. Add "collapse risk" paragraph in §VII.G for simultaneous multi-criterion failure.
7. Add Landis & Koch (1977) reference for κ thresholds.
8. Add sub-agreement reporting (high-risk subset vs. trusted+random subset) for Table G1.

**None of these revisions require new experiments.** They are threshold and framing adjustments to a protocol that is already well-designed.
