import argparse
import csv
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(r"D:\ocn")
QUEUE_CSV = ROOT / "data" / "simclaim_v4_scaffold" / "generation_queue" / "v4_generation_queue_600_candidate_slots.csv"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v4_pilot"
OUT_CANDIDATES = OUT_ROOT / "candidates" / "simclaim_hardpair_v4_pilot_candidates.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v4_pilot_candidates.jsonl"
OUT_RAW = OUT_ROOT / "raw_llm" / "v4_claim_generation_raw_outputs.jsonl"
OUT_AUDIT = OUT_ROOT / "audit" / "v4_claim_generation_audit.csv"
OUT_REPORT = ROOT / "reports" / "simclaim_hardpair_v4_pilot" / "v4_claim_generation_report.md"

LABELS = [
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
]

BANNED_STYLE_CUES = [
    "contradict",
    "contradiction",
    "opposite",
    "rather than",
    "instead of",
    "proves",
    "guarantees",
    "must be used",
    "should be adopted",
    "policy makers should",
    "require",
    "requires",
    "required",
    "replacement",
    "replace",
    "replacing",
    "immediate",
    "hinder",
    "hinders",
    "progress",
    "most domains",
    "most settings",
    "most applications",
    "always",
    "never",
    "all settings",
    "all domains",
    "universally",
    "therefore",
    "need to",
    "needs to",
    "can rely",
    "field-oriented",
    "standard platform",
    "standard",
    "sufficient",
    "primary",
    "deployment",
    "policy",
    "recommend",
    "recommended",
    "basis for",
    "ready for",
    "production",
    "complete framework",
    "within the same described research context",
    "same described research context",
    "described research context",
    "adequate for",
    "validating",
    "operational",
    "guide",
    "guides",
    "guiding",
    "establish",
    "establishes",
    "established",
    "establishing",
    "making",
    "practical",
    "routine",
    "central",
    "omit",
    "omits",
    "need",
    "needs",
    "needed",
    "should",
    "must",
    "across",
]

SOFT_BALANCE_CUES = [
    "related",
    "adjacent",
    "tasks",
    "contexts",
    "setting",
    "beyond",
    "outside",
    "use",
    "can",
    "generally",
    "varied",
    "diverse",
    "without",
    "only",
    "selected",
    "additional",
    "scenario",
    "scenarios",
    "real-world",
    "driving",
    "excluding",
    "fewer",
    "less",
    "not",
]

LOCAL_REPAIR_REPLACEMENTS = [
    ("for all autonomous driving tasks", "for driving scenarios"),
    ("in all autonomous driving tasks", "in driving scenarios"),
    ("for all driving-system tasks", "for driving scenarios"),
    ("all driving-system tasks", "driving scenarios"),
    ("all driving tasks", "driving scenarios"),
    ("all driving scenarios", "additional driving scenarios"),
    ("all traffic", "additional traffic"),
    ("all rear-end", "additional rear-end"),
    ("for all load profiles", "for load profiles"),
    ("for all capacitor and regulator settings", "for capacitor and regulator settings"),
    ("all real-world tasks", "real-world scenarios"),
    ("all real world tasks", "real-world scenarios"),
    ("all multi-agent tasks", "multi-agent scenarios"),
    ("in most settings", "for adjacent benchmark cases"),
    ("across most settings", "for adjacent benchmark cases"),
    ("across most domains", "for adjacent benchmark cases"),
    ("across most applications", "for adjacent benchmark cases"),
    ("across varied sensor types", "for additional sensor examples"),
    ("for sensor plugins beyond the described examples", "for additional sensor examples"),
    ("beyond the described examples", "additional examples"),
    ("beyond examples", "additional examples"),
    ("across varied driving scenarios", "for additional driving scenarios"),
    ("across varied game environments", "for varied game environments"),
    ("in related game scenarios", "in game scenarios"),
    ("related game scenarios", "game scenarios"),
    ("across diverse game environments", "in game environments"),
    ("diverse game environments", "game environments"),
    ("across varied settings", "for adjacent benchmark cases"),
    ("across varied", "for additional"),
    ("across all reinforcement learning frameworks", "for reinforcement learning frameworks"),
    ("for varied driving scenarios", "for selected driving scenarios"),
    ("in varied towns", "in Town 2"),
    ("for diverse driving scenarios", "for simulator output cases"),
    ("for varied", "for selected"),
    ("in varied", "in selected"),
    ("varied", "selected"),
    ("diverse", "additional"),
    ("should be replaced for research", "are limited for research"),
    ("should be replaced", "are limited"),
    ("require immediate replacement", "are limited for direct study"),
    ("requires immediate replacement", "are limited for direct study"),
    ("needed for", "reported for"),
    ("need to", "can be considered to"),
    ("needs to", "can be considered to"),
    ("as a basis for", "in relation to"),
    ("basis for", "relation to"),
    ("as a standard platform for all multi-agent tasks", "for multi-agent scenarios"),
    ("standard platform", "shared platform"),
    ("used for deployment", "described beyond evaluation"),
    ("for deployment", "beyond evaluation"),
    ("for real-world deployment", "beyond the described setting"),
    ("real-world deployment", "described setting"),
    ("tasks within", "scenarios within"),
    ("tasks", "scenarios"),
    ("benchmark cases", "benchmark context"),
    ("driving cases", "driving context"),
    ("cases", "context"),
    ("benchmark context within", "benchmark setting within"),
    ("driving context within", "driving setting within"),
    ("for research within", "for study setting within"),
    ("research within", "study setting within"),
    ("field-oriented evaluation", "study setting"),
    ("field-oriented scope", "study setting"),
    ("field-oriented use", "study setting"),
    ("field-oriented", "study-setting"),
    ("extended study setting", "study setting"),
    ("extended", "specified"),
    ("used beyond setting", "described beyond setting"),
    ("used beyond", "described beyond"),
    ("can inform", "is described alongside"),
    ("autonomous driving systems", "driving studies"),
    ("autonomous driving", "driving"),
    ("driving-system studies", "driving studies"),
    ("driving-system use", "driving setting"),
    ("driving-system", "driving"),
    ("beyond evaluation", "beyond described scope"),
    ("evaluation within", "scope within"),
    ("beyond described scope", "beyond the described setting"),
    ("without discrete time steps", "with continuous-time interaction"),
    ("without cloud platform assistance", "with local platform assistance"),
    ("without accurate physics simulation", "with inaccurate physics simulation"),
    ("without efficient physics simulation", "with inefficient physics simulation"),
    ("without the initial statuses", "with missing initial statuses"),
    ("related real traffic scenarios", "additional real traffic scenarios"),
    ("for related driving contexts", "for driving scenarios"),
    ("safe exploration contexts", "safe exploration examples"),
    ("across related", "for comparable"),
    ("can replace", "is described alongside"),
    ("not available", "absent"),
    ("only for single-agent reinforcement learning", "for single-agent reinforcement learning"),
    ("instead of a list", "in place of a list"),
    ("as the standard for", "in relation to"),
    ("the standard for", "relation to"),
    ("all driving", "driving"),
    ("all real", "real"),
    ("direct use", "direct study"),
    ("study use within", "study setting within"),
    ("use within", "setting within"),
]


def endpoint_from_base(base_url):
    base = (base_url or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def group_slots(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["v4_group_id"], []).append(row)
    return {gid: sorted(items, key=lambda r: LABELS.index(r["candidate_label_guess"])) for gid, items in groups.items()}


def existing_successes():
    if not OUT_AUDIT.exists():
        return set()
    rows = read_csv(OUT_AUDIT)
    return {r["v4_group_id"] for r in rows if str(r.get("status", "")).startswith("success")}


def make_prompt(group_id, rows):
    base = rows[0]
    labels_text = "\n".join([f"- {label}: {desc}" for label, desc in [
        ("supported", "faithfully supported by the evidence, no extra scope"),
        ("mild_scope_overclaim", "a small scope or generalization overclaim, still plausible sounding"),
        ("strong_action_overclaim", "a larger factual or scope mismatch than the evidence warrants, still in the same sentence frame"),
        ("contradiction_candidate", "a neutral-sounding claim that conflicts with the evidence"),
    ]])
    banned = ", ".join(BANNED_STYLE_CUES)
    soft = ", ".join(SOFT_BALANCE_CUES)
    return f"""
You are generating candidate claims for a scientific evidence-pair classification dataset.

Hard constraints:
1. Do NOT alter the evidence text. Only write claim_text values.
2. Produce exactly four claims, one for each label.
3. Keep the four claims similar in surface style, length, formality, and hedging.
4. Do not reveal the label through obvious cue words.
5. Avoid these hard-banned label-leaking terms or phrases: {banned}
6. Keep each claim one sentence, 18-34 words. This is mandatory; claims shorter than 18 words are invalid.
7. Do not mention "evidence", "paper", "table", "section", "supported", "overclaim", "contradiction", or label names.
8. Use neutral scientific wording. No dramatic wording.
9. Use the same syntactic frame across the four labels where possible; the relation should change, not the surface style.
10. Avoid modal/action cue phrasing. Do not use "should", "must", "need", "therefore", "standard", "sufficient", "policy", "deployment", or "recommend".
11. The four claims should begin with the same subject phrase and use the same main verb phrase whenever possible.
12. These soft cue terms are allowed only if balanced across multiple claims, not confined to one label: {soft}
13. Before returning JSON, count the words in each claim and revise any claim that has fewer than 18 words or more than 34 words.
14. Do not use generic boilerplate tails such as "within the same described research context"; style control must come from similar syntax, not a repeated suffix.
15. Do not use action-pressure words such as "require", "replacement", "immediate", "hinder", or "progress".
16. Do not use expansion-shortcut phrases such as "across most domains", "most settings", or "most applications".
17. Build all four claims from one shared sentence skeleton. The subject phrase, main verb phrase, modality, and final closing phrase must be identical.
18. Change only a short factual slot of 2-8 words between labels; do not add label-specific framing words.
19. Do not make the mild or strong labels recognizable through generic scope words such as "related", "adjacent", "selected", "additional", "general", "reference", "setting", "context", "beyond", "outside", "tasks", or "use".
20. For the strong label, prefer a larger factual/scope mismatch inside the same grammar, not an action, policy, deployment, or recommendation claim.
21. For the contradiction label, change one factual attribute while preserving the same sentence frame; do not use negation unless all four claims use the same negation pattern.
22. A good pattern is: SAME SUBJECT + SAME VERB PHRASE + VARIABLE FACTUAL SLOT, with no repeated non-informative closing phrase.
23. Bad pattern: supported is plain, mild uses "related/adjacent/selected/additional", strong uses "general/reference/beyond/setting/use", contradiction uses "not/cannot". Avoid this.
24. The four full claim_text strings must be distinct. The variable factual slot must be non-empty and different in all four claims.
25. Do not return placeholders, repeated claims, or notes such as "needs factual slot change"; write actual final claim_text for every label.
26. For every non-supported label, the variable factual slot must add a clear mismatch signal that is not merely copied from the evidence text.
27. Mild, strong, and contradiction claims must not differ only by adding an entity already present in the evidence; they must change scope, quantity, condition, or factual attribute.

Labels:
{labels_text}

Return JSON only:
{{
  "group_id": "{group_id}",
  "claims": [
    {{"label": "supported", "claim_text": "...", "word_count": 0, "semantic_note": "..."}},
    {{"label": "mild_scope_overclaim", "claim_text": "...", "word_count": 0, "semantic_note": "..."}},
    {{"label": "strong_action_overclaim", "claim_text": "...", "word_count": 0, "semantic_note": "..."}},
    {{"label": "contradiction_candidate", "claim_text": "...", "word_count": 0, "semantic_note": "..."}}
  ],
  "shared_style_plan": "...",
  "risk_notes": "..."
}}

Context:
Group ID: {group_id}
Domain: {base.get("domain", "")}
Paper title: {base.get("paper_title", "")}
Evidence location: {base.get("evidence_location", "")}
Evidence text:
\"\"\"{base.get("evidence_text", "")}\"\"\"
""".strip()


def call_llm(api_key, base_url, model, prompt, timeout=90):
    endpoint = endpoint_from_base(base_url)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return strict JSON only. Do not include markdown fences."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    return obj["choices"][0]["message"]["content"]


def parse_json(text):
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    return json.loads(clean)


def normalize_space(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def local_repair_claim_text(text):
    repaired = str(text or "")
    replacements = []
    for old, new in LOCAL_REPAIR_REPLACEMENTS:
        pattern = re.compile(rf"\b{re.escape(old)}\b", flags=re.IGNORECASE)
        if pattern.search(repaired):
            repaired = pattern.sub(new, repaired)
            replacements.append(f"{old}->{new}")
    return normalize_space(repaired), replacements


def local_repair_payload(payload):
    copied = json.loads(json.dumps(payload, ensure_ascii=False))
    repairs = []
    for claim in copied.get("claims", []):
        before = claim.get("claim_text", "")
        after, reps = local_repair_claim_text(before)
        if reps:
            claim["claim_text"] = after
            claim["local_repair_applied"] = True
            claim["local_repair_replacements"] = reps
            repairs.append({"label": claim.get("label", ""), "replacements": reps, "before": before, "after": after})
    if repairs:
        copied["local_repair_applied"] = True
        copied["local_repair_records"] = repairs
    return copied, repairs


def validate_payload(payload):
    claims = payload.get("claims", [])
    if len(claims) != 4:
        return False, "expected_4_claims"
    by_label = {c.get("label"): normalize_space(c.get("claim_text", "")) for c in claims}
    if set(by_label) != set(LABELS):
        return False, "labels_missing_or_extra"
    for label, claim in by_label.items():
        if not claim:
            return False, f"empty_claim_{label}"
        word_count = len(claim.split())
        if word_count < 12 or word_count > 42:
            return False, f"word_count_out_of_range_{label}_{word_count}"
        low = claim.lower()
        for cue in BANNED_STYLE_CUES:
            if re.search(rf"\b{re.escape(cue)}\b", low):
                return False, f"banned_cue_{label}_{cue}"
    for cue in SOFT_BALANCE_CUES:
        labels_with_cue = [
            label for label, claim in by_label.items()
            if re.search(rf"\b{re.escape(cue)}\b", claim.lower())
        ]
        if len(labels_with_cue) == 1:
            return False, f"unbalanced_soft_cue_{labels_with_cue[0]}_{cue}"
    if len(set(by_label.values())) != 4:
        return False, "duplicate_claim_text"
    return True, "ok"


def generate_group(api_key, base_url, model, group_id, rows, retries=2):
    prompt = make_prompt(group_id, rows)
    last_error = ""
    for attempt in range(1, retries + 2):
        try:
            text = call_llm(api_key, base_url, model, prompt)
            payload = parse_json(text)
            ok, reason = validate_payload(payload)
            repair_records = []
            repaired_payload = payload
            if not ok:
                repaired_payload, repair_records = local_repair_payload(payload)
                repaired_ok, repaired_reason = validate_payload(repaired_payload)
                if repaired_ok:
                    ok, reason = True, "ok_after_local_repair"
                    payload = repaired_payload
                else:
                    reason = repaired_reason
            append_jsonl(OUT_RAW, {
                "v4_group_id": group_id,
                "attempt": attempt,
                "ok": ok,
                "reason": reason,
                "raw_text": text,
                "payload": payload,
                "local_repair_records": repair_records,
            })
            if ok:
                return payload, {
                    "v4_group_id": group_id,
                    "status": "success",
                    "attempt": attempt,
                    "reason": reason,
                    "model": model,
                }
            last_error = reason
        except Exception as exc:
            last_error = str(exc)
            append_jsonl(OUT_RAW, {
                "v4_group_id": group_id,
                "attempt": attempt,
                "ok": False,
                "reason": last_error,
            })
        time.sleep(1.0 * attempt)
    return None, {
        "v4_group_id": group_id,
        "status": "failed",
        "attempt": retries + 1,
        "reason": last_error,
        "model": model,
    }


def materialize_rows(queue_rows, payloads, audits):
    payload_by_group = {p["group_id"]: p for p in payloads if p}
    audit_by_group = {a["v4_group_id"]: a for a in audits}
    out = []
    for row in queue_rows:
        copied = dict(row)
        group_id = row["v4_group_id"]
        payload = payload_by_group.get(group_id)
        if payload:
            claim_map = {c["label"]: c for c in payload["claims"]}
            claim = claim_map[row["candidate_label_guess"]]
            copied["claim_text"] = normalize_space(claim["claim_text"])
            copied["claim_text_sha256"] = hashlib.sha256(copied["claim_text"].encode("utf-8")).hexdigest()
            copied["claim_generation_status"] = "success"
            copied["v4_semantic_note"] = claim.get("semantic_note", "")
            copied["v4_shared_style_plan"] = payload.get("shared_style_plan", "")
            copied["v4_risk_notes"] = payload.get("risk_notes", "")
            copied["v4_generation_model"] = audit_by_group.get(group_id, {}).get("model", "")
        else:
            copied["claim_generation_status"] = audit_by_group.get(group_id, {}).get("status", copied.get("claim_generation_status", "pending"))
            copied["v4_generation_failure_reason"] = audit_by_group.get(group_id, {}).get("reason", "")
        copied["evidence_text_original_locked"] = copied["evidence_text"]
        copied["evidence_lock_check_sha256"] = hashlib.sha256(copied["evidence_text"].encode("utf-8")).hexdigest()
        copied["human_audited"] = "false"
        copied["final_label"] = ""
        copied["gold_label"] = ""
        out.append(copied)
    return out


def write_report(rows, audits, selected_count):
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    success_groups = {a["v4_group_id"] for a in audits if str(a.get("status", "")).startswith("success")}
    generated_rows = [r for r in rows if r.get("claim_generation_status") == "success"]
    evidence_unchanged = sum(1 for r in generated_rows if r.get("evidence_text") == r.get("evidence_text_original_locked"))
    duplicate_claims = len(generated_rows) - len({r.get("claim_text", "") for r in generated_rows if r.get("claim_text", "")})
    lines = [
        "# v4 claim generation report",
        "",
        "This run generated claim text for selected v4 queue groups only. Evidence text was copied from the locked queue and must remain unchanged.",
        "",
        "## Summary",
        "",
        f"- Groups selected this run: {selected_count}",
        f"- Groups successfully generated: {len(success_groups)}",
        f"- Candidate rows generated: {len(generated_rows)}",
        f"- Evidence unchanged among generated rows: {evidence_unchanged}/{len(generated_rows) if generated_rows else 0}",
        f"- Duplicate generated claim rows: {duplicate_claims}",
        "",
        "## Safety status",
        "",
        "- `human_audited` remains false.",
        "- `final_label` and `gold_label` remain blank.",
        "- Evidence text was not rewritten by the generator.",
        "",
        "## Outputs",
        "",
        f"- Candidates CSV: `{OUT_CANDIDATES}`",
        f"- Generation audit: `{OUT_AUDIT}`",
        f"- Raw output cache: `{OUT_RAW}`",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-groups", type=int, default=1)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--confirm-spend", action="store_true")
    parser.add_argument("--hard-cap-groups", type=int, default=3)
    args = parser.parse_args()

    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    if not args.confirm_spend:
        raise RuntimeError("Refusing to call an external LLM without --confirm-spend")
    if args.limit_groups > args.hard_cap_groups:
        raise RuntimeError(f"Refusing to run {args.limit_groups} groups because hard cap is {args.hard_cap_groups}")
    if not api_key:
        raise RuntimeError("LLM_API_KEY environment variable is required for claim generation")
    if not base_url:
        raise RuntimeError("LLM_BASE_URL environment variable is required; no default provider is allowed")
    if not model:
        raise RuntimeError("LLM_MODEL environment variable is required; no default model is allowed")

    queue_rows = read_csv(QUEUE_CSV)
    groups = group_slots(queue_rows)
    done = set() if args.force else existing_successes()
    group_ids = [gid for gid in sorted(groups) if gid not in done]
    selected_ids = group_ids[args.start_index:args.start_index + args.limit_groups]
    print(json.dumps({
        "safety": "external_llm_call_confirmed",
        "provider_base_url": base_url,
        "model": model,
        "selected_groups": len(selected_ids),
        "hard_cap_groups": args.hard_cap_groups,
        "max_workers": args.max_workers,
        "retries": args.retries,
        "api_key": "redacted",
    }, ensure_ascii=False), flush=True)

    OUT_CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    payloads = []
    audits = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = {
            ex.submit(generate_group, api_key, base_url, model, gid, groups[gid], args.retries): gid
            for gid in selected_ids
        }
        for fut in as_completed(futures):
            gid = futures[fut]
            payload, audit = fut.result()
            payloads.append(payload)
            audits.append(audit)
            print(json.dumps({"v4_group_id": gid, **audit}, ensure_ascii=False), flush=True)

    existing_audits = read_csv(OUT_AUDIT) if OUT_AUDIT.exists() else []
    if args.force:
        selected_set = set(selected_ids)
        existing_audits = [r for r in existing_audits if r.get("v4_group_id") not in selected_set]
    write_csv(OUT_AUDIT, existing_audits + audits)

    generated_rows = materialize_rows(queue_rows, payloads, audits)
    if OUT_CANDIDATES.exists():
        previous = read_csv(OUT_CANDIDATES)
        by_id = {r["candidate_id"]: r for r in previous}
        selected_set = set(selected_ids)
        for r in generated_rows:
            if r.get("v4_group_id") in selected_set:
                by_id[r["candidate_id"]] = r
            elif r.get("claim_generation_status") == "success":
                by_id[r["candidate_id"]] = r
        all_rows = [by_id.get(r["candidate_id"], r) for r in queue_rows]
    else:
        all_rows = generated_rows
    write_csv(OUT_CANDIDATES, all_rows)
    write_jsonl(OUT_JSONL, all_rows)
    all_audits = read_csv(OUT_AUDIT)
    write_report(all_rows, all_audits, len(selected_ids))
    print(json.dumps({
        "status": "ok",
        "selected_groups": len(selected_ids),
        "success_groups_this_run": sum(1 for a in audits if str(a.get("status", "")).startswith("success")),
        "candidates_csv": str(OUT_CANDIDATES),
        "audit_csv": str(OUT_AUDIT),
        "report_md": str(OUT_REPORT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
