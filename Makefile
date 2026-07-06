# V3.17 Confidential Lightweight Pipeline — Makefile
#
# Unified entry points for toy validation, schema checks, red-team scanning,
# and paper asset collection. All targets are safe to run in CI.
#
# Hard boundaries (enforced by underlying scripts):
#   - no network, no API, no training, no original data modification
#   - full mode requires explicit authorization (see runbook)
#
# NEVER delete private data via Makefile. clean-toy only removes toy outputs.

PYTHON ?= python
PIPELINE_SCRIPT := scripts/run_v3_17_confidential_pipeline.py
VALIDATE_SCRIPT := scripts/validate_experiment_outputs_v1.py
REDTEAM_SCRIPT := scripts/run_confidentiality_redteam_scan_v1.py

# ---------------------------------------------------------------------------
# Default target
# ---------------------------------------------------------------------------

.PHONY: help
help:
	@echo "V3.17 Confidential Pipeline — Makefile targets:"
	@echo ""
	@echo "  make toy           Run the full toy pipeline (7 stages, ~3s)"
	@echo "  make validate      Validate experiment outputs against schema registry"
	@echo "  make redteam       Run confidentiality red-team scanner on repo"
	@echo "  make schemas       Check schema registry health (9 schemas load)"
	@echo "  make clean-toy     Remove toy experiment outputs (NOT private data)"
	@echo "  make paper-assets   Collect paper-ready artifacts from latest run"
	@echo "  make test          Run V3.17 smoke test suite (183 tests)"
	@echo "  make compile       Compile-check all scripts and tests"
	@echo ""
	@echo "For full private data runs, see docs/runbook_v3_17_confidential.md"

# ---------------------------------------------------------------------------
# Toy pipeline
# ---------------------------------------------------------------------------

.PHONY: toy
toy:
	$(PYTHON) $(PIPELINE_SCRIPT) --mode toy

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

.PHONY: validate
validate:
	$(PYTHON) $(VALIDATE_SCRIPT) --toy_mode

.PHONY: schemas
schemas:
	$(PYTHON) -m pytest -q tests/test_schema_registry.py

.PHONY: redteam
redteam:
	$(PYTHON) $(REDTEAM_SCRIPT) --toy_mode

# ---------------------------------------------------------------------------
# Paper assets
# ---------------------------------------------------------------------------

.PHONY: paper-assets
paper-assets:
	$(PYTHON) $(PIPELINE_SCRIPT) --mode toy --stages paper_assets --output_dir experiments/paper_assets_latest

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
		tests/test_pipeline_runner.py

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
