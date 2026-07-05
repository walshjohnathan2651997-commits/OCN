# LLM Baseline Cost Estimate

## Scope

- **Sample size**: 200 SimClaim pairs (50 per class × 4 classes)
- **Sample size alternative**: 100 pairs (25 per class) for pilot
- **API**: NOT called in Task Q. This is a pre-execution estimate.

## Estimated Token Usage (per call)

- System prompt: ~250 tokens
- User prompt (claim + evidence + rules): ~450 tokens average (varies by evidence length)
- LLM response (JSON): ~120 tokens
- **Total per call**: ~820 tokens (input + output)

## Cost Scenarios (illustrative, list prices, USD)

| Model | Input $/1M | Output $/1M | Cost per 200 calls | Cost per 100 calls |
|---|---|---|---|---|
| GPT-4o-mini | $0.15 | $0.60 | ~$0.10 | ~$0.05 |
| GPT-4o | $2.50 | $10.00 | ~$1.70 | ~$0.85 |
| Claude 3.5 Haiku | $0.80 | $4.00 | ~$0.70 | ~$0.35 |
| Claude 3.5 Sonnet | $3.00 | $15.00 | ~$2.10 | ~$1.05 |
| Local Qwen2.5-7B | $0 | $0 | $0 (compute only) | $0 (compute only) |

## Recommended Approach

1. **Pilot first**: Run 100 samples on a low-cost model (GPT-4o-mini or local Qwen2.5-7B).
2. **Quality check**: Inspect 20 random outputs for label quality.
3. **Scale only if useful**: If pilot shows LLM >= R4 on strong_positive_f1, scale to 200 + try a stronger model.
4. **Never run full 444 SimClaim**: Keep LLM baseline to <=200 for cost control.

## Constraints

- Task Q does NOT call any API.
- Task Q does NOT spend any budget.
- All costs are estimates for planning only.
- Actual execution requires separate approval.
