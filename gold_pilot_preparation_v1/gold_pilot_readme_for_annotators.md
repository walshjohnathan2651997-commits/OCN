# README for Annotators — Gold Pilot

**Welcome.** Thank you for helping with this annotation task. This README explains what you need to do in plain language. Please read it once before starting.

---

## What is this task about?

You will see 50 pairs of text. Each pair has:
- **Evidence:** a short piece of text from a scientific paper.
- **Claim:** a sentence that someone wrote about that evidence.

Your job is to judge: **Is the evidence enough to support the strength of the claim?**

This is not about whether the claim is true or false in the real world. It is about whether the *evidence provided* is *enough* for the *strength* of the claim as written.

## The five labels

For each pair, pick one label:

| Label | Plain meaning |
|---|---|
| `supported` | The evidence is enough for the claim as written. The claim does not stretch the evidence. |
| `mild_scope_overclaim` | The claim slightly stretches the scope (e.g., "single dataset" becomes "multi-dataset"), but does not make an action/deployment/safety claim. |
| `strong_action_overclaim` | The claim makes an action/deployment/safety/guarantee/generalization claim that the evidence does not back up. The claim is not exactly false — it is just too strong. |
| `contradiction_candidate` | The evidence actually contradicts the claim. They point in opposite directions on the same number, name, or fact. |
| `unsure` | You genuinely cannot decide after reading both carefully. |

## How to decide

Use this simple order:

1. **First, check for contradiction.** Does the claim say the *opposite* of the evidence on the same number, name, or fact? If yes → `contradiction_candidate`.
2. **If no contradiction, check for action/deployment/safety language.** Does the claim use words like "deploy," "safety," "guarantee," "ready for," "outperforms," "operational"? If yes → check if the evidence really supports that strong claim. If the evidence is too thin (e.g., only a simulation, only one benchmark) → `strong_action_overclaim`.
3. **If no action language, check for scope stretching.** Does the claim stretch the scope (e.g., "single domain" becomes "multi-domain") without an action conclusion? If yes → `mild_scope_overclaim`.
4. **If none of the above** → `supported`.

## Rules you must follow

1. **Only look at the evidence and claim text given to you.** Do not look up the paper. Do not search online. Do not use your own knowledge of the topic.
2. **Do not try to guess what the author meant.** Judge the text as written.
3. **Do not talk to the other annotator.** You each work alone. Comparing notes is not allowed until both of you are done.
4. **Do not look for model predictions.** You will not be given any model outputs. Do not try to find them.
5. **Do not look for the "silver" labels.** You will not be given them. Do not try to find them.
6. **If you are really unsure, pick `unsure`.** Do not force a label. But if you can narrow it down to two options, pick the one you lean toward and note your confusion in the form.
7. **Write a one-sentence reason for every pair.** This is required. The reason should explain *why* you picked that label.

## How to fill the form

For each pair, you will fill these fields:

| Field | What to write |
|---|---|
| `annotator_label` | One of the five labels above. |
| `confidence_1_to_5` | How sure are you? 1 = very unsure, 5 = very sure. |
| `rationale_one_sentence` | One sentence explaining your choice. Example: "Evidence mentions numerical experiments only, but claim says 'physical plant trials' — that is an action escalation." |
| `confusion_if_any` | If you were torn between two labels, write which two. Options: `none`, `supported_vs_mild`, `mild_vs_strong`, `strong_vs_contradiction`, `evidence_insufficient_context`, `other`. If you were not confused, write `none`. |
| `needs_adjudication` | Write `yes` if you think this case needs a third person to decide. Otherwise `no`. |

## Tips

- **Read the evidence first, then the claim.** This order matters.
- **Look for numbers, names, and facts.** If the claim swaps a number or name from the evidence, that is likely `contradiction_candidate`.
- **Look for action words.** Words like "deploy," "safety," "guarantee," "ready for," "outperforms," "operational" suggest `strong_action_overclaim` if the evidence is thin.
- **Look for scope words.** Words like "multi-domain," "across datasets," "generalizes" suggest `mild_scope_overclaim` if there is no action conclusion.
- **When in doubt, do not force it.** Pick `unsure` or the label you lean toward, and explain in the rationale.
- **Take breaks.** Tired annotators produce low-quality labels. If you are tired, stop and come back later.

## How long will it take?

Most annotators take 6-10 hours for 50 pairs. There is no time limit. Work at your own pace.

## What happens after you finish?

After both annotators finish, a third person (the adjudicator) will:
- Compare your labels.
- For pairs where you both agree: confirm the label.
- For pairs where you disagree: read both reasons and pick a final label.

The final labels will be used to check whether the taxonomy is reliable. Your work is the foundation of that check.

## Questions?

If you have questions about the guideline, ask the project coordinator. Do not ask the other annotator.

---

**Thank you for your careful work. Your labels matter.**
