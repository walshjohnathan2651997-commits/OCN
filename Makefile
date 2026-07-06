# V3.17 Confidential Lightweight Pipeline — Makefile
#
# Unified entry points for toy validation, schema checks, red-team scanning,
# and paper asset collection. All targets are safe to run in CI unless
# explicitly marked as requiring private data.
#
# Hard boundaries (enforced by underlying scripts):
#   - no network, no API, no training, no original data modification
#   - real mode requires explicit --allow_private_data true
#   - CI never runs real PDF extraction or private release
#
# NEVER delete private data via Makefile. clean-toy only removes toy outputs.

PYTHON ?= python
PIPELINE_SCRIPT := scripts/run_v3_17_confidential_pipeline.py
VALIDATE_SCRIPT := scripts/validate_experiment_outputs_v1.py
REDTEAM_SCRIPT := scripts/run_confidentiality_redteam_scan_v1.py
PAPER_SCRIPT := scripts/generate_paper_assets_v3_17.py
RELEASE_SCRIPT := scripts/build_public_sanitized_release_v1.py
STATUS_SCRIPT := scripts/generate_project_status_report_v1.py

# ---------------------------------------------------------------------------
# Default target
# ---------------------------------------------------------------------------

.PHONY: help
help:
	@echo "V3.17 Confidential Pipeline — Makefile targets:"
	@echo ""
	@echo "  make status         Generate project status report"
	@echo "  make toy            Run toy pipeline (toy_demo, schema, redteam)"
	@echo "  make p0-real        Run P0 real experiments (REQUIRES private data)"
	@echo "  make paper-assets   Generate paper tables/figures/checklist"
	@echo "  make redteam        Run confidentiality red-team scanner"
	@echo "  make schema         Validate experiment outputs against schemas"
	@echo "  make release        Build public sanitized release bundle"
	@echo "  make final-check    Run full readiness gate (status + redteam + schema + tests)"
	@echo "  make test           Run V3.17 smoke test suite"
	@echo "  make compile        Compile-check all scripts and tests"
	@echo "  make clean-toy      Remove toy experiment outputs (NOT private data)"
	@echo ""
	@echo "CI-safe targets: status, toy, paper-assets, redteam, schema, test, compile"
	@echo "Private targets: p0-real, release (release is safe but slow)"
	@echo ""
	@echo "For full private data runs, see docs/runbook_v3_17_confidential.md"

# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

.PHONY: status
status:
	$(PYTHON) $(STATUS_SCRIPT)

# ---------------------------------------------------------------------------
# Toy pipeline (CI-safe)
# ---------------------------------------------------------------------------

.PHONY: toy
toy:
	$(PYTHON) $(PIPELINE_SCRIPT) --mode toy

# ---------------------------------------------------------------------------
# P0 real experiments (REQUIRES private data — never run in CI)
# ---------------------------------------------------------------------------

.PHONY: p0-real
p0-real:
	@echo "============================================================"
	@echo "WARNING: p0-real requires private data authorization."
	@echo "This target runs real PDF extraction, BM25, canonicalizer,"
	@echo "format shift, and leakage audit on real data."
	@echo "It will FAIL without --allow_private_data true."
	@echo "============================================================"
	$(PYTHON) $(PIPELINE_SCRIPT) --mode real \
		--stages pdf_corpus,bm25_real,canonicalizer_real,format_shift_real,leakage_real \
		--allow_private_data true

# ---------------------------------------------------------------------------
# Paper assets
# ---------------------------------------------------------------------------

.PHONY: paper-assets
paper-assets:
	$(PYTHON) $(PAPER_SCRIPT)

# ---------------------------------------------------------------------------
# Redteam scan
# ---------------------------------------------------------------------------

.PHONY: redteam
redteam:
	$(PYTHON) $(REDTEAM_SCRIPT) \
		--private_allowlist experiments/confidentiality_redteam_scan_v1/private_intermediate_allowlist.json

# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

.PHONY: schema
schema:
	$(PYTHON) $(VALIDATE_SCRIPT)

# ---------------------------------------------------------------------------
# Release bundle
# ---------------------------------------------------------------------------

.PHONY: release
release:
	$(PYTHON) $(RELEASE_SCRIPT)

# ---------------------------------------------------------------------------
# Final readiness gate
# ---------------------------------------------------------------------------

.PHONY: final-check
final-check:
	@echo "============================================================"
	@echo "V3.17 Final Readiness Gate"
	@echo "============================================================"
	@echo ""
	@echo "[1/5] Generating status report..."
	@$(PYTHON) $(STATUS_SCRIPT)
	@echo ""
	@echo "[2/5] Running redteam scan..."
	@$(PYTHON) $(REDTEAM_SCRIPT) \
		--private_allowlist experiments/confidentiality_redteam_scan_v1/private_intermediate_allowlist.json
	@echo ""
	@echo "[3/5] Running schema validation..."
	@$(PYTHON) $(VALIDATE_SCRIPT)
	@echo ""
	@echo "[4/5] Running smoke tests..."
	@$(PYTHON) -m pytest -q \
		tests/test_current_mainline_docs.py \
		tests/test_no_private_text_in_public_outputs.py \
		tests/test_pipeline_runner_toy.py \
		tests/test_release_bundle_safety.py \
		tests/test_redteam_scan_toy_passes.py \
		tests/test_paper_assets_no_private_text.py
	@echo ""
	@echo "[5/5] Final readiness gate complete."
	@echo "============================================================"
	@echo "Review reports/current_project_status_v3_17.md for P0 status."
	@echo "Review experiments/confidentiality_redteam_scan_v1/redteam_summary.md for high-risk count."
	@echo "Review experiments/schema_validation_summary.md for schema pass/fail."
	@echo "============================================================"

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

.PHONY: test
test:
	$(PYTHON) -m pytest -q \
		tests/test_no_leakage_fields.py \
		tests/test_smart_queue_outputs.py \
		tests/test_sentence_corpus_schema.py \
		tests/test_toy_demo_runs.py \
		tests/test_config_guards.py \
		tests/test_schema_registry.py \
		tests/test_redacted_outputs_no_text.py \
		tests/test_redteam_scan_toy_passes.py \
		tests/test_pipeline_runner.py \
		tests/test_paper_assets_no_private_text.py

.PHONY: compile
compile:
	$(PYTHON) -m compileall -q scripts tests

# ---------------------------------------------------------------------------
# Cleanup (toy only — NEVER deletes private data)
# ---------------------------------------------------------------------------

.PHONY: clean-toy
clean-toy:
	@echo "Removing toy experiment outputs (NOT private data)..."
	@-rm -rf experiments/bm25_sentence_retrieval_v1_toy
	@-rm -rf experiments/canonicalizer_ablation_v1_toy
	@-rm -rf experiments/format_shift_ablation_v1_toy
	@-rm -rf experiments/r4_eval_v1_toy
	@-rm -rf experiments/lightweight_smart_queue_v1_toy
	@-rm -rf experiments/leakage_audit_v1_toy
	@-rm -rf experiments/canonicalized_review_queue_v1_toy
	@-rm -rf experiments/canonicalized_risk_ranking_v1_toy
	@-rm -rf experiments/confidentiality_redteam_scan_v1_toy
	@-rm -rf experiments/toy_end_to_end_demo_v1
	@-rm -rf experiments/v3_17_confidential_pipeline_runs
	@-rm -rf experiments/paper_assets_latest
	@-rm -rf data/pdf_corpus_toy_v1
	@echo "Done. Private data (pdfs/, data/private/) is NOT touched."

# ---------------------------------------------------------------------------
# Safety check — verify private data is not deleted by any target
# ---------------------------------------------------------------------------

.PHONY: check-no-private-delete
check-no-private-delete:
	@echo "Verifying no Makefile target deletes private data..."
	@grep -E 'rm[[:space:]]+-rf[[:space:]]+(pdfs|private_pdfs|data/private|experiments/private)' Makefile && \
		(echo "ERROR: Makefile contains a target that deletes private data!" && exit 1) || \
		echo "OK: No private data deletion found in Makefile."
