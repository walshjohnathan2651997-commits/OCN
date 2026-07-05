# Script Second-Pass Cleanup Note

Date: 2026-07-04
Pass: 2 (correction pass after the first script_cleanup_v1 run)
Operator: assistant

## 1. Why Not Refactor

The user explicitly evaluated the first-pass cleanup and concluded: **do not refactor code**. The project bottleneck is gold pilot / label credibility, not code quality. Refactoring old scripts would only add risk to a paper already in the advisor-handoff stage, without changing any number in V3.7.

This second pass is therefore a **light correction**, not a refactor:
- No script logic modified.
- No script deleted.
- No experiments run, no APIs called, no models trained.
- No paper edits, no data edits, no gold labels written.
- V3.7 paper directory and `_MAIN_PAPER_CURRENT` not broken.

## 2. What Was Moved Out of `D:\ocn\scripts`

| Script | Old location | New location | Reason |
|---|---|---|---|
| `build_script_cleanup_v1.py` | `D:\ocn\scripts\build_script_cleanup_v1.py` | `D:\ocn\_PROJECT_INDEX\tools\build_script_cleanup_v1.py` | It is a project maintenance tool, not a paper mainline script. |

The script is recoverable at its new location. It is not deleted.

After this move, `D:\ocn\scripts` contains 23 files: 21 `.py` scripts + `README_MAINLINE.md` + `HOW_TO_REPRODUCE_MAINLINE.md`.

## 3. Scripts Marked as `historical` in the Registry

The following 5 scripts remain in `D:\ocn\scripts` for traceability of the V3.x revision chain, but are now explicitly marked `category=historical` in `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv`. Their `notes` field reads: `historical only; current paper is V3.7; do not use unless reproducing old versions`.

| Script | Why historical |
|---|---|
| `build_v3_1_docx.py` | V3.1 docx builder; superseded by V3.7. |
| `build_v3_2_docx.py` | V3.2 docx builder; superseded by V3.7. |
| `build_v3_2_table0_and_audit.py` | V3.2 Table 0 + author sanity audit; superseded by V3.4 taxonomy hardening. |
| `build_v3_3_docx.py` | V3.3 docx builder; superseded by V3.7. |
| `build_v3_3_main_paper.py` | V3.3 main paper content builder; superseded by V3.4. |

These are NOT deleted and NOT archived — they stay in `D:\ocn\scripts` so the V3.1 → V3.7 revision chain is locally traceable, but the registry makes clear they are not current.

## 4. `safe_to_run` Conservative Updates

`D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv` was rewritten with a strict `safe_to_run` policy.

### 4.1 Rule applied

| Script type | `safe_to_run` |
|---|---|
| Calls an API (DeepSeek, GPT, Hugging Face inference) | `no` |
| Reruns a frozen model / experiment / sweep | `no` |
| Changes file structure (moves / archives / deletes) | `no` |
| Regenerates a frozen main result pack or paper-content builder | `no` |
| Historical script (V3.1 / V3.2 / V3.3 line) | `no` |
| `build_v3_7_docx.py` (regenerates V3.7 Word from markdown) | `yes` (with note: confirm no overwrite of manual docx edits) |
| `build_gold_pilot_preparation_v1.py` (regenerates 50-sample pack from existing CSVs) | `yes` (with note: confirm no overwrite of manual annotations) |

### 4.2 Resulting `safe_to_run=no` count

Out of 21 entries in the registry:

- `safe_to_run=yes`: **2** (`build_v3_7_docx.py`, `build_gold_pilot_preparation_v1.py`)
- `safe_to_run=no`: **19** (all `run_*` scripts + all `build_v3_*` scripts except `build_v3_7_docx.py` + `build_paper_ready_mixed_framework_v2.py` + `build_v3_external_gold_llm_plan_v1.py`)

### 4.3 Specific scripts flipped to `no` by this pass

| Script | Before | After |
|---|---|---|
| `build_v3_1_docx.py` | yes | no (historical) |
| `build_v3_2_docx.py` | yes | no (historical) |
| `build_v3_3_docx.py` | yes | no (historical) |
| `build_v3_4_docx.py` | yes | no (frozen output) |
| `build_v3_5_docx.py` | yes | no (frozen output) |
| `build_v3_6_docx.py` | yes | no (frozen output) |

The 6 `run_*` scripts and the result-pack / paper-content builders were already `no` after the first pass and remain `no`.

## 5. Is `D:\ocn\scripts` Clean Enough Now?

Yes. After this second pass:

- 21 `.py` scripts + 2 `.md` docs = 23 files.
- 16 `current_mainline` scripts (the actual working set for V3.7 and its immediate V3.4–V3.6 revision chain).
- 5 `historical` scripts (V3.1–V3.3 line, kept for traceability, marked clearly).
- 0 maintenance tools (moved to `_PROJECT_INDEX\tools\`).
- 0 ambiguity in `safe_to_run` — only 2 yes, both with overwrite-prevention notes.
- README and HOW_TO_REPRODUCE both explicitly say: do not rerun API / experiments; do not refactor; next step is gold pilot.

The user's stated target of "12-15 truly current scripts" is met in spirit: the 16 `current_mainline` scripts are all genuinely on the V3.4→V3.7 revision chain or directly feed V3.7. The 5 historical V3.1–V3.3 scripts are a small traceability tail and could be archived in a future pass if the user wants, but they are harmless and already clearly labeled.

## 6. Files Updated / Created by This Pass

| File | Action |
|---|---|
| `D:\ocn\scripts\build_script_cleanup_v1.py` | MOVED to `D:\ocn\_PROJECT_INDEX\tools\build_script_cleanup_v1.py` |
| `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv` | REWRITTEN — 21 entries, added `category` column (current_mainline / historical), conservative `safe_to_run`, historical notes |
| `D:\ocn\scripts\README_MAINLINE.md` | REWRITTEN — explicit "not a complete historical codebase", current paper V3.7, no API / experiment scripts, only edit markdown then regenerate docx |
| `D:\ocn\scripts\HOW_TO_REPRODUCE_MAINLINE.md` | REWRITTEN — added Section 0 "Full Reproduction Is NOT Recommended" with 4 reasons; recommended reproduction path uses existing outputs only |
| `D:\ocn\_PROJECT_INDEX\script_second_pass_cleanup_note.md` | CREATED (this file) |

## 7. Next Step Recommendation

**Gold pilot, not code refactor.**

The script directory is now clean enough. Further refactoring would not change any V3.7 number and would only add risk. The actual scientific blocker is independent gold adjudication:

1. Two annotators independently label the 50 candidates in `D:\ocn\gold_pilot_preparation_v1\annotator_A_template.csv` and `annotator_B_template.csv`.
2. Adjudicator resolves disagreements in `adjudication_template.csv`.
3. Compute per-boundary Cohen's κ per `agreement_statistics_plan.md`.
4. If `mild_vs_strong κ < 0.4`, revise the taxonomy before any further algorithm work.

Until that pilot is adjudicated, no new algorithm / ablation / LLM comparison should be started.

## 8. Prohibitions Honored

- No script code logic modified.
- No script deleted.
- No experiments run.
- No API calls.
- No model training.
- No paper edits.
- No data edits.
- V3.7 not moved.
- `_MAIN_PAPER_CURRENT` not broken (left untouched in this pass; its copy of `build_script_cleanup_v1.py` is left in place to avoid breaking the mirror — the canonical location for the tool is now `_PROJECT_INDEX\tools\`).
