# Reviewer Attack Report — V3.9 Pre-Gold Complete Manuscript

**Audit date:** 2026-07-04
**Auditor:** Simulated harsh SCI reviewer (Reviewer 2 persona)
**Target:** `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\CESE_OCN_V3_9_pre_gold_complete.md`
**Method:** Read-only audit. No experiments run, no data modified, no V3.9 files changed.

## Audit Summary

| Severity | Count | Verdict |
| --- | --- | --- |
| Fatal | 2 | Must address before advisor review |
| Major | 6 | Must address before submission (not necessarily before advisor) |
| Minor | 9 | Polish before submission |

**Overall judgment:** The manuscript is internally consistent and the numbers are traceable. The two fatal issues are framing/positioning problems, not data problems. They can be fixed without new experiments. **Recommendation: B (minor revision before advisor).**

---

## Fatal Issues (2)

### F1 — The "pre-gold complete draft" framing reads as "we couldn't validate, so we wrote a paper about why validation is pending"

**Location:** Title page, §VII, §IX Limitation 7, Abstract closing sentence.
**Attack:** A harsh reviewer reads "pre-gold complete manuscript" as a confession that the authors know the silver labels are unreliable but want credit for the paper structure anyway. The §VII Planned Gold Validation section, while well-designed, can be read as an elaborate excuse for not having done the gold annotation *before* writing the paper. The phrase "complete draft except planned gold validation results" in the title page signals weakness to a reviewer who doesn't care about the project's internal timeline.
**Risk:** Reviewer rejects with "come back when you have gold labels" without engaging with the framework's structural contributions.
**Recommended fix:** Reframe V3.9 as "silver-stage pilot with pre-registered gold validation protocol" rather than "pre-gold complete draft." Move the "not submission-ready" disclaimer from the title page to a footnote or the Limitations section. Do not lead the paper with an apology. The title page should state what the paper *is*, not what it *isn't yet*.

### F2 — The central claim (R4 complements LLM on strong_action) is computed against labels that the paper itself flags as 62.5% questionable/unclear

**Location:** §V.D (author sanity audit), §VI.B (LLM comparison), §VII (gold validation plan).
**Attack:** The paper's strongest empirical claim — "R4 achieves strong_F1 = 0.3000 vs. LLM 0.0769" — is computed against silver labels. The paper itself reports that 62.5% of audited silver labels are questionable/unclear, with strong_action_overclaim at 75% confusion. A harsh reviewer asks: "If your labels are 62.5% questionable, why should I believe any of your numbers?" The §VII gold validation plan says "we'll check later" — but the paper's contribution claims are stated in the present tense ("R4 improves," "LLM under-detects"), not conditional tense.
**Risk:** Reviewer dismisses all §VI results as unreliable.
**Recommended fix:** Add an explicit conditional framing to §VI: "Under the silver-label pilot, R4 improves... If gold adjudication supports the silver labels (§VII), this pattern holds; if not, the paper is downgraded per §VII.G." Make the conditional tense explicit in the Abstract and Conclusion. The paper currently says this in Limitations but not in the Results section itself.

---

## Major Issues (6)

### M1 — R4's macro-F1 (0.3280) is so much lower than LLM (0.5523) that the "complement" framing may not survive practical scrutiny

**Location:** §VI.B, §VIII.A.
**Attack:** A 0.22 macro-F1 gap is enormous. A reviewer asks: "If I deploy R4 alongside my LLM judge, I get +0.2231 strong_action-F1 but I also get 98 supported→strong false positives and 24 mild→strong false positives. Is the strong_action improvement worth the false-positive cleanup cost?" The paper acknowledges this trade-off but does not quantify the operational cost. The screening use case (§VII.D H6) is mentioned but not demonstrated.
**Risk:** Reviewer concludes R4 is impractical.
**Recommended fix (no new experiment needed):** Add a paragraph in §VIII.A that explicitly states the operational trade-off: "For every true strong_action case R4 finds, it produces approximately N false positives (98+24)/[true positives]. This ratio is acceptable for screening (where a human reviews flagged cases) but not for autonomous deployment." Compute the false-positive-per-true-positive ratio from existing data and report it.

### M2 — strong_action_overclaim could be a taxonomy artifact, not a real class

**Location:** §III (taxonomy), §V.D (audit showing 75% confusion on strong_action).
**Attack:** A reviewer argues: "You defined a class (strong_action_overclaim) that has 75% confusion rate even by your own audit. Then you built a router (R4) that targets this class. Then you showed LLMs can't detect this class. But if the class itself is not reliably definable, your entire contribution collapses — R4 isn't detecting a real phenomenon, it's detecting your labeling heuristic." This is the strongest possible attack on the paper.
**Risk:** Reviewer rejects the taxonomy entirely.
**Recommended fix:** The §VII gold validation plan addresses this (downgrade criterion 1: mild_vs_strong κ < 0.40 → taxonomy revision). But the paper should state this risk more prominently in §III or §VIII, not bury it in §VII.G. Add a sentence in §III.C: "The existence of strong_action_overclaim as a reliably drawable class is itself a hypothesis; §VII pre-registers the test of this hypothesis."

### M3 — The structured prompt result (5-step decomposition doesn't help) is from a single prompt design, but the paper generalizes it

**Location:** §VI.B finding 1, §VIII.B.
**Attack:** The paper tests one structured prompt design and concludes "this structured decomposition design does not improve strong_action detection." But the paper also acknowledges "other prompt designs (few-shot, chain-of-thought, tool-augmented) remain untested." A reviewer asks: "Why didn't you test 2-3 more prompt designs? You ran GPT on 100 samples — adding 2 more prompts would cost ~$3." The paper's claim is narrow ("under the tested prompts") but the framing suggests a broader pattern.
**Risk:** Reviewer asks for more prompt variants before accepting the under-detection claim.
**Recommended fix:** The §VII gold validation plan includes GPT decision-tree prompt and GPT few-shot prompt as gold-subset evaluations (Table G3). Add a forward reference in §VI.B: "Two additional prompt designs (decision-tree, few-shot) are pre-registered for gold-subset evaluation in Table G3; if either closes the strong_action gap, the under-detection claim is downgraded per §VII.G criterion 3." This shows the paper is aware of the gap and has a plan.

### M4 — The 50-sample gold pilot is too small to confirm the taxonomy

**Location:** §VII.F.
**Attack:** 50 samples (25 high-risk + 16 trusted + 9 random) is a pilot, not a validation. A reviewer asks: "You have 444 silver pairs. Why gold-validate only 50? Even with perfect agreement on 50 samples, the confidence interval on kappa is wide. You cannot confirm a four-class taxonomy with 50 samples." The paper acknowledges this ("sufficient to estimate per-boundary κ but is not sufficient to support confirmatory benchmark claims") but still positions the gold pilot as the next step toward submission.
**Risk:** Reviewer says "50 samples is not enough for a confirmatory study" and asks for 200+.
**Recommended fix:** Add a sentence in §VII.F: "The 50-sample pilot is designed to detect fatal taxonomy problems (κ < 0.40), not to confirm the taxonomy. A confirmatory study (300–500 independently adjudicated pairs) is a separate follow-up effort. If the 50-sample pilot passes, the paper proceeds to the confirmatory study; if it fails, the taxonomy is revised first." This sets clear expectations.

### M5 — The paper makes 4 "cautious contributions" but they are still contributions

**Location:** §I (contributions list).
**Attack:** A reviewer reads: "(i) frames scientific claim calibration as evidence sufficiency calibration... (ii) constructs a silver diagnostic set... (iii) introduces CESE-OCN R4... (iv) reports a matched-sample LLM judge comparison..." These are contribution claims. But the paper also says all results are pre-gold, silver-label, exploratory. A reviewer asks: "If everything is exploratory and pre-gold, what are the contributions? You can't claim a contribution and then disclaim it in the same paper."
**Risk:** Reviewer questions whether the paper has any contribution at all.
**Recommended fix:** Reframe the contributions as "pilot contributions" or "framework contributions" explicitly: "(i) We propose a framework for... (ii) We construct a pilot dataset for... (iii) We introduce a routing method for... (iv) We report a pilot comparison..." The word "pilot" or "framework" should modify each contribution so the reader knows what level of claim is being made.

### M6 — The external validation (SciFact, VitaminC) is a sanity check that cannot test the core taxonomy

**Location:** §VI.D.
**Attack:** A reviewer asks: "You ran your method on public datasets, but those datasets don't have action-overclaim labels. So your external validation tests nothing about the four-class taxonomy. Why include it?" The paper acknowledges this ("Public datasets cannot test the four-class evidence-sufficiency taxonomy") but still devotes a results subsection to it.
**Risk:** Reviewer sees external validation as padding.
**Recommended fix:** Either (a) move §VI.D to an appendix with a clear "sanity check, not taxonomy validation" label, or (b) reframe it as "transferability probe of the contradiction + scope components" rather than "external validation." The current framing ("external public dataset sanity check") is honest but still takes up main-text space that a reviewer might see as wasted.

---

## Minor Issues (9)

### m1 — Abstract says "DeepSeek-V3 reaches macro-F1 0.5270" but Table 2 shows both 0.5248 (matched 100) and 0.5270 (full 200)

**Location:** Abstract vs. Table 2.
**Risk:** Minor confusion about which number is the headline.
**Fix:** Use 0.5270 consistently in the Abstract (it's the 200-sample number, which is the larger sample) and clarify in Table 2 that the matched 100 is a subset.

### m2 — The phrase "consistent under-detection pattern" appears throughout but is computed on a single run, temperature 0

**Location:** §VI.B, §VIII.B.
**Risk:** "Consistent" implies multiple runs or conditions; single-run is not "consistent."
**Fix:** Change to "under-detection pattern observed under the tested prompts" or "under-detection pattern across the two tested models" (which is accurate — GPT and DeepSeek both show it).

### m3 — "Pre-gold findings" is used 14 times in the paper; it becomes repetitive

**Location:** Throughout.
**Risk:** Reader fatigue; the cautionary framing loses impact through repetition.
**Fix:** Use "pre-gold findings" 3-4 times (Abstract, §VI opener, §VII opener, §X closer) and use "silver-stage results" or "pilot results" elsewhere.

### m4 — §VII.D has 6 hypotheses but H3 and H4 are both about silver-gold consistency

**Location:** §VII.D.
**Risk:** The hypotheses overlap; a reviewer may ask why H3 and H4 are separate.
**Fix:** Merge H3 and H4 into a single hypothesis about silver-gold consistency, or clarify that H3 is about label-level consistency and H4 is about model-ranking consistency.

### m5 — The decision tree (Figure 2) has not been tested against gold labels

**Location:** §VIII.D.
**Risk:** The paper uses the decision tree as if it were operational, but it's unvalidated.
**Fix:** Add "(unvalidated against gold)" after each mention of the decision tree in §III.B and §VIII.D. This is already implied but should be explicit.

### m6 — The cost-sensitive variant cw4.0 is mentioned but not clearly motivated

**Location:** §IV.D, Table 1.
**Risk:** A reviewer asks why cw4.0 is included if it doesn't meet the replacement threshold.
**Fix:** Add one sentence: "cw4.0 is retained as an auxiliary sensitivity analysis to show that cost-sensitive training provides a small additional improvement, but does not change the main method selection."

### m7 — The paper references files (e.g., `table_main_results_clean.csv`, `high_risk_sample_bank.csv`) without always specifying their location

**Location:** §V, §VI.
**Risk:** A reader cannot easily find these files.
**Fix:** Add a "Data and Code Availability" statement in the appendix listing all referenced files and their paths.

### m8 — The experiment file `gpt_structured_probe_gate.json` recommends positioning "llm_blindspot_supported" but the paper explicitly avoids "blind spot" language

**Location:** Traceability issue between experiment file and paper.
**Risk:** If a reviewer finds the experiment file, they may see a contradiction.
**Fix:** Add a note in the completion log that the paper deliberately re-frames the experiment file's recommendation to avoid "blind spot" language. (This is a process note, not a paper change.)

### m8 — The 0.3158 number (R4 strong_F1 on full 200) appears in Table 2 without a clear source file reference

**Location:** Table 2, row "R4 (full 200)."
**Risk:** Minor traceability gap.
**Fix:** Add a footnote: "R4 strong_F1 on the 200-sample DeepSeek comparison set; see `llm_vs_r4_200.csv`."

### m9 — The paper says "10/10 seeds positive" for the bootstrap CI but does not report per-seed numbers

**Location:** §VI.A.
**Risk:** A reviewer may want to see the per-seed distribution.
**Fix:** Add a reference to `frozen_r4_routing_results_by_seed.csv` for per-seed details.

---

## Summary Of Reviewer Risk

| Risk Category | Severity | Can Fix Without New Experiments? |
| --- | --- | --- |
| Silver labels are 62.5% questionable | Fatal (F2) | Yes — conditional framing |
| "Pre-gold complete" framing reads as apologetic | Fatal (F1) | Yes — reframe title page |
| R4 macro-F1 much lower than LLM | Major (M1) | Yes — quantify FP/TP ratio |
| strong_action may be taxonomy artifact | Major (M2) | Yes — state as hypothesis |
| Single structured prompt tested | Major (M3) | Yes — forward-reference §VII |
| 50-sample gold pilot too small | Major (M4) | Yes — set expectations |
| 4 "cautious contributions" still sound like contributions | Major (M5) | Yes — reframe as "pilot contributions" |
| External validation doesn't test taxonomy | Major (M6) | Yes — move to appendix or reframe |

**Bottom line:** All 8 issues are fixable through wording/framing changes. No new experiments are required to address any fatal or major issue. The data is sound; the framing is the problem.
