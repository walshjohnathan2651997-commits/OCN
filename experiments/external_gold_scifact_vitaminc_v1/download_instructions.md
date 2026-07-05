# External Gold Data Download Instructions

This file documents how the SciFact and VitaminC data used in this experiment was acquired.

## SciFact

- **Source URL**: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
- **License**: CC BY-NC 2.0
- **Local path**: `D:\ocn\data\external_gold\scifact\`
- **Files used**:
  - `data/claims_train.jsonl` (809 claims, labeled)
  - `data/claims_dev.jsonl` (300 claims, labeled)
  - `data/corpus.jsonl` (5183 abstracts)
- **Note**: `claims_test.jsonl` exists but is unlabeled (no labels released); not used.
- **Download method**: direct HTTPS GET via Python `requests` with `trust_env=False` (bypassing system proxy).

## VitaminC

- **Original source**: https://github.com/TalSchuster/talschuster.github.io/raw/master/static/vitaminc.zip
- **Mirror used**: `https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/` (because `huggingface.co` and `raw.githubusercontent.com` were blocked by the local network)
- **License**: CC BY-SA 3.0
- **Local path**: `D:\ocn\data\external_gold\vitaminc\`
- **Files used**:
  - `dev.jsonl` (63054 records, used as training proxy)
  - `test.jsonl` (55197 records, used for evaluation sampling)
- **Files NOT downloaded**:
  - `train.jsonl` (194MB) - skipped to save bandwidth; dev.jsonl used as training proxy instead
- **Download method**: Python `requests` with `trust_env=False`, streamed to disk.
- **Network failures encountered**:
  - `huggingface.co` connection timeout (blocked by network)
  - `raw.githubusercontent.com` connection reset on large files (vitaminc.zip)
  - Workaround: used `hf-mirror.com` Chinese mirror which worked reliably

## NLI Model (Method C)

- **Model**: `cross-encoder/nli-deberta-base`
- **Cache location**: `~/.cache/huggingface/hub/models--cross-encoder--nli-deberta-base`
- **Loaded offline** with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`
- **No new model download required**

## Reproducibility

To re-download the data on a clean machine:

```bash
# SciFact
mkdir -p data/external_gold/scifact
curl -L -o data/external_gold/scifact_data.tar.gz \
  https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
tar -xzf data/external_gold/scifact_data.tar.gz -C data/external_gold/scifact

# VitaminC (use hf-mirror.com if huggingface.co is blocked)
mkdir -p data/external_gold/vitaminc
curl -L -o data/external_gold/vitaminc/dev.jsonl \
  https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/dev.jsonl
curl -L -o data/external_gold/vitaminc/test.jsonl \
  https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/test.jsonl
```
