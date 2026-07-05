# LLM Baseline Cost Report (200 samples)

## Summary

- **Model**: deepseek-chat
- **N samples**: 200
- **N valid (parsed OK)**: 200
- **Valid rate**: 1.0000
- **Total API calls**: 200

## Token Usage

- **Total input tokens**: 105657
- **Total output tokens**: 15563
- **Mean input tokens/call**: 528.3
- **Mean output tokens/call**: 77.8

## Cost

- **Total cost estimate**: $0.032430
- **Mean cost/call**: $0.000162
- **Pricing used**: input cache hit $0.14/1M, cache miss $0.27/1M, output $0.28/1M

## Latency

- **Mean latency**: 1.76s
- **Max latency**: 2.77s
- **Min latency**: 1.22s

## LLM vs R4 Cost Comparison

- **LLM cost**: $0.032430 for 200 valid predictions
- **R4 cost**: $0 (deterministic local model, no API)
- **LLM latency**: 1.76s/call (amortized)
- **R4 latency**: <0.01s/call (local inference)

## Notes

- Cost is an estimate based on public DeepSeek pricing; actual billing may vary.
- R4 is a local deterministic model with zero marginal API cost.
- LLM provides natural-language rationales; R4 provides transparent routing thresholds.
