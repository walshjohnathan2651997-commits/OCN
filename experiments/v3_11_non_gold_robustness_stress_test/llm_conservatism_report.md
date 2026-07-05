# LLM Conservatism Audit

**Method:** For samples where silver = strong_action_overclaim, compute the distribution of each judge's predictions. Conservatism = tendency to predict supported/mild instead of strong.

## Matched-100: Prediction Distribution on silver=strong_action

| Judge | n_strong | →supported | →mild | →strong (correct) | →contradiction | Conservative collapse (sup+mild) |
|---|---|---|---|---|---|---|
| gpt_standard | 25 | 0 (0.0%) | 10 (40.0%) | 1 (4.0%) | 14 (56.0%) | 40.0% |
| gpt_structured | 25 | 0 (0.0%) | 10 (40.0%) | 1 (4.0%) | 14 (56.0%) | 40.0% |
| deepseek | 25 | 9 (36.0%) | 10 (40.0%) | 1 (4.0%) | 5 (20.0%) | 76.0% |
| r4 | 25 | 2 (8.0%) | 8 (32.0%) | 9 (36.0%) | 6 (24.0%) | 40.0% |

## Matched-200: DeepSeek

| deepseek | 50 | 19 (38.0%) | 21 (42.0%) | 2 (4.0%) | 8 (16.0%) | 80.0% |
| r4 | 50 | 2 (4.0%) | 20 (40.0%) | 18 (36.0%) | 10 (20.0%) | 44.0% |

## Key Findings

1. **LLM conservatism CONFIRMED:** All three LLM judges (GPT-standard, GPT-structured, DeepSeek) predict strong_action correctly only 4% of the time on silver-strong samples (vs R4 36%).
2. **Two distinct error patterns:**
   - **GPT-5.5** collapses to **contradiction** (56%) — treats strong_action as factual contradiction rather than strength mismatch.
   - **DeepSeek** collapses to **supported/mild** (76%) — treats strong_action as charitably supported or mildly over-scoped.
   - Both patterns are systematic non-detection, not random errors.
3. **Structured prompt does NOT fix this:** GPT-structured makes 1 strong predictions vs GPT-standard 1 — identical, no improvement.
4. **R4 contrast:** R4 correctly identifies 9/25 strong_action cases, vs LLMs' 1-1.
5. **DeepSeek pattern stable at 200:** conservative collapse (80%) and strong recall (4%) are consistent between 100 and 200 samples.
