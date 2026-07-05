"""Tests for the LLM-judge baseline (spec 6.4)."""

from __future__ import annotations

import json
import os
import tempfile

import numpy as np

from cese.baselines.llm_judge_baseline import (
    LlmJudgeBaseline,
    OfflineJsonlClient,
    _coerce_judge_output,
    _extract_json_object,
    build_judge_prompt,
)


class _StubClient:
    """In-memory client returning canned responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def judge(self, sample):
        resp = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return _coerce_judge_output(resp)


def test_coerce_judge_output_validates_fields():
    raw = {
        "contradiction": 1,
        "escalation": 1,
        "escalation_type": ["scope", "not_a_real_type"],
        "evidence_gap_labels": "coverage_missing",
        "rationale": "claim overstates scope",
    }
    out = _coerce_judge_output(raw)
    assert out["contradiction"] == 1
    assert out["escalation"] == 1
    assert out["escalation_type"] == ["scope"]  # invalid filtered
    assert out["evidence_gap_labels"] == ["coverage_missing"]
    assert "scope" in out["rationale"]


def test_coerce_judge_output_from_string():
    text = '{"escalation": 1, "rationale": "overclaim"}'
    out = _coerce_judge_output(text)
    assert out["escalation"] == 1
    assert out["rationale"] == "overclaim"


def test_extract_json_object_from_code_fence():
    text = '```json\n{"escalation": 1}\n```'
    obj = _extract_json_object(text)
    assert obj == {"escalation": 1}


def test_extract_json_object_with_surrounding_text():
    text = 'Here is the result: {"escalation": 0, "contradiction": 1} done.'
    obj = _extract_json_object(text)
    assert obj["contradiction"] == 1


def test_build_judge_prompt_includes_claim_and_evidence():
    prompt = build_judge_prompt(
        {"claim_text": "model is safe", "evidence_text": "no safety test"}
    )
    assert "model is safe" in prompt
    assert "no safety test" in prompt
    assert "escalation" in prompt


def test_disabled_baseline_returns_nan_probs():
    baseline = LlmJudgeBaseline()
    assert not baseline.enabled
    out = baseline.predict([{"claim_text": "x", "evidence_text": "y"}])
    assert np.isnan(out["escalation_prob"][0])
    assert out["escalation_pred"][0] == 0


def test_baseline_with_stub_client():
    responses = [
        {"escalation": 1, "contradiction": 0, "escalation_type": ["scope"]},
        {"escalation": 0, "contradiction": 1, "rationale": "ok"},
    ]
    baseline = LlmJudgeBaseline(client=_StubClient(responses))
    records = [
        {"claim_text": "c1", "evidence_text": "e1"},
        {"claim_text": "c2", "evidence_text": "e2"},
    ]
    out = baseline.predict(records)
    assert out["escalation_pred"][0] == 1
    assert out["escalation_pred"][1] == 0
    assert out["contradiction"][1] == 1
    assert out["escalation_type"][0] == ["scope"]


def test_offline_jsonl_client(tmp_path=None):
    # Write a temporary JSONL file.
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "sample_id": "s1",
                        "escalation": 1,
                        "escalation_type": ["causal"],
                        "evidence_gap_labels": ["traceability_missing"],
                        "rationale": "missing causal id",
                    }
                )
                + "\n"
            )
            fh.write(
                json.dumps({"sample_id": "s2", "escalation": 0, "rationale": "ok"})
                + "\n"
            )
        client = OfflineJsonlClient(path)
        out1 = client.judge({"sample_id": "s1"})
        out2 = client.judge({"sample_id": "s2"})
        out3 = client.judge({"sample_id": "missing"})
        assert out1["escalation"] == 1
        assert out1["escalation_type"] == ["causal"]
        assert out2["escalation"] == 0
        assert out3["escalation"] == 0  # default for missing
    finally:
        os.remove(path)


def test_offline_jsonl_baseline_predict():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                json.dumps({"sample_id": "a", "escalation": 1, "contradiction": 1})
                + "\n"
            )
        baseline = LlmJudgeBaseline(offline_jsonl=path)
        assert baseline.enabled
        out = baseline.predict([{"sample_id": "a"}, {"sample_id": "b"}])
        assert out["escalation_pred"][0] == 1
        assert out["contradiction"][0] == 1
        # Missing sample -> default 0.
        assert out["escalation_pred"][1] == 0
    finally:
        os.remove(path)
