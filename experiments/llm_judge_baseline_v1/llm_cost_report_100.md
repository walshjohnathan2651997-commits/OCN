# LLM Baseline Cost Report (100 samples)

## Summary

- **Model**: deepseek-chat
- **N samples**: 100
- **N valid (parsed OK)**: 100
- **Valid rate**: 1.0000
- **Total API calls**: 0

## Token Usage

- **Total input tokens**: 52778
- **Total output tokens**: 7742
- **Mean input tokens/call**: 52778.0
- **Mean output tokens/call**: 7742.0

## Cost

- **Total cost estimate**: $0.000000
- **Mean cost/call**: $0.000000
- **Pricing used**: input cache hit $0.14/1M, cache miss $0.27/1M, output $0.28/1M

## Latency

- **Mean latency**: 1.78s
- **Max latency**: 2.24s
- **Min latency**: 1.24s

## LLM vs R4 Cost Comparison

- **LLM cost**: $0.000000 for 100 valid predictions
- **R4 cost**: $0 (deterministic local model, no API)
- **LLM latency**: 1.78s/call (amortized)
- **R4 latency**: <0.01s/call (local inference)

## Notes

- Cost is an estimate based on public DeepSeek pricing; actual billing may vary.
- R4 is a local deterministic model with zero marginal API cost.
- LLM provides natural-language rationales; R4 provides transparent routing thresholds.
