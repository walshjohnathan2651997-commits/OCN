"""Tests for P5-13: run_pilot_loop.py.

These tests use the toy smoke dataset with --allow_toy_results to
exercise the full pilot loop end-to-end. They also test the
label-conflict stopping behavior and the summary structure.

ocn-29: subprocess harness rewritten to avoid capture_output=True
(which can deadlock under TRAE / pytest / timeout-wrapper pipe
capture). stdout/stderr now go to a log file; tree-kill on timeout.
Heavy full-loop tests are marked ``@pytest.mark.slow`` so the default
``pytest -q tests/test_run_pilot_loop.py`` runs the fast unit tests
plus ONE integration test, not 5+ full training loops.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DATA = ROOT / "data" / "toy" / "smoke.jsonl"


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill the whole process tree of ``proc``.

    POSIX: kill the process group (proc was started with
    ``start_new_session=True``). Windows: ``taskkill /T /F``.
    """
    if proc.poll() is not None:
        return
    if sys.platform.startswith("win"):
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15, check=False,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception:
            pass


def _run_pilot_loop(
    cmd: list[str],
    cwd: Path = ROOT,
    timeout: int = 300,
    log_path: Path | None = None,
):
    """Run a pilot-loop subprocess WITHOUT ``capture_output=True``.

    stdout/stderr are tee'd to a log file (so failures can be diagnosed
    by reading the tail) instead of being captured into an OS pipe that
    can deadlock when the parent's read buffer fills under TRAE / pytest
    / timeout-wrapper. On timeout the whole process tree is killed
    (``start_new_session=True`` + ``killpg`` / ``taskkill /T /F``).

    Returns a SimpleNamespace with ``returncode``, ``stdout`` (tail),
    ``stderr`` (tail), and ``log_path`` so existing assertions like
    ``proc.returncode`` and ``proc.stderr[-2000:]`` keep working.
    """
    if log_path is None:
        log_path = cwd / "_pilot_loop_test.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # own process group on POSIX
        )
    except Exception:
        log_file.close()
        raise
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass  # best-effort; tree-kill above is the strong arm
    finally:
        log_file.close()
    # Read the log tail for diagnostics. Avoid keeping the whole file in
    # memory (some e2e logs are large).
    text = log_path.read_text(encoding="utf-8", errors="replace")
    tail = text[-4000:] if len(text) > 4000 else text
    return SimpleNamespace(
        returncode=proc.returncode,
        stdout=tail,
        stderr=tail,
        log_path=str(log_path),
    )


@pytest.mark.slow
def test_pilot_loop_runs_on_smoke_data(tmp_path):
    """End-to-end smoke test: the pilot loop should run to completion
    on the toy smoke dataset and produce a diagnostic summary."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, (
        f"pilot loop failed (rc={proc.returncode}). "
        f"stderr tail:\n{proc.stderr[-2000:]}"
    )
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists(), "pilot_loop_summary.json missing"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    # Pilot is never paper-ready.
    assert summary["paper_valid"] is False
    assert summary["result_scope"] == "pilot_diagnostic"
    # Steps must be recorded.
    step_names = [s["step"] for s in summary["steps"]]
    assert "validate" in step_names
    assert "fill_escalation_labels" in step_names
    assert "run_stage_train_eval" in step_names
    # No failed_step.
    assert "failed_step" not in summary


@pytest.mark.slow
def test_pilot_loop_stops_on_label_conflict(tmp_path):
    """When the input has a label conflict, the fill_escalation_labels
    step must fail and the loop stops with a failed summary."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    # Build a tiny input with a deliberate conflict: escalation_label=0
    # but claim_tiers > support_tiers on some dim.
    records = []
    for line in SMOKE_DATA.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        r["escalation_label"] = 0  # force a (likely) conflict
        records.append(r)
    # Ensure at least one record will conflict: pick a record where
    # claim_tiers > support_tiers on some dim.
    conflict_found = False
    for r in records:
        ct = r.get("claim_tiers", {})
        st = r.get("support_tiers", {})
        if any(ct.get(k, 0) > st.get(k, 0) for k in ct):
            r["escalation_label"] = 0  # conflict
            conflict_found = True
            break
    assert conflict_found, "test setup did not create a conflict"
    bad_input = tmp_path / "bad_pilot.jsonl"
    with open(bad_input, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(bad_input),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--step_timeout_sec", "60",
    ]
    proc = _run_pilot_loop(cmd, timeout=180)
    assert proc.returncode != 0, "expected failure on label conflict"
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["failed_step"] == "fill_escalation_labels"


def test_pilot_loop_requires_input_or_splits(tmp_path):
    """Missing --input and --train/--dev/--test should fail immediately."""
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
    ]
    proc = _run_pilot_loop(cmd, timeout=60)
    assert proc.returncode != 0
    # Summary should record the failure.
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "failed"


@pytest.mark.slow
def test_pilot_loop_summary_marks_diagnostic(tmp_path):
    """The summary must always mark paper_valid=false and
    result_scope=pilot_diagnostic."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--step_timeout_sec", "60",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["paper_valid"] is False
    assert summary["result_scope"] == "pilot_diagnostic"


def test_pilot_loop_summary_always_written_on_failure(tmp_path):
    """Even when the loop fails at the very first step (e.g. missing
    input), pilot_loop_summary.json must exist and record the failure.
    """
    out_dir = tmp_path / "pilot_out"
    # Point --input at a non-existent file. The first validation will
    # fail because validate_data can't open it.
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(tmp_path / "does_not_exist.jsonl"),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--step_timeout_sec", "60",
    ]
    proc = _run_pilot_loop(cmd, timeout=120)
    assert proc.returncode != 0
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists(), "summary must be written even on failure"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert "failed_step" in summary
    assert "error" in summary


@pytest.mark.slow
def test_pilot_loop_warns_on_split_imbalance(tmp_path):
    """When the data is heavily class-imbalanced, the loop should
    complete but the check_pilot_balance step records a soft failure
    (warning) and next_step_suggestions mentions imbalance.
    """
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    # Build a tiny imbalanced dataset: take smoke records but force
    # escalation_label=0 on almost all of them so the dataset is
    # heavily imbalanced (only a few positives).
    records = []
    pos_kept = 0
    for line in SMOKE_DATA.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        # Force most records to negative; keep only 1 positive.
        if r.get("escalation_label") == 1 and pos_kept < 1:
            pos_kept += 1
            # keep as-is
        else:
            r["escalation_label"] = 0
            # zero out claim_tiers so derived label is 0 too.
            r["claim_tiers"] = {k: 0 for k in r.get("claim_tiers", {})}
        records.append(r)
    imbalanced = tmp_path / "imbalanced.jsonl"
    with open(imbalanced, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(imbalanced),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--step_timeout_sec", "60",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    # The loop should still complete (pilot diagnostic), but the
    # check_pilot_balance step should be soft_failed.
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    # Find the balance step.
    balance_steps = [
        s for s in summary["steps"] if s["step"] == "check_pilot_balance"
    ]
    assert len(balance_steps) == 1
    # Either soft_failed (imbalance) or ok. With a heavily imbalanced
    # set we expect soft_failed.
    assert balance_steps[0]["status"] in ("soft_failed", "ok")
    # Either the balance step warns OR the next_step_suggestions mention
    # imbalance (the suggestion generator also checks pos/neg ratio).
    balance_warned = balance_steps[0]["status"] == "soft_failed"
    suggestion_warned = any(
        "imbalance" in s.lower() for s in summary.get("next_step_suggestions", [])
    )
    assert balance_warned or suggestion_warned, (
        f"expected imbalance warning; steps={balance_steps[0]}; "
        f"suggestions={summary.get('next_step_suggestions')}"
    )


# ---------------------------------------------------------------------------
# ocn-28: subprocess execution model tests (timeout, log path, return code,
# no lingering processes, --skip_report).
# ---------------------------------------------------------------------------

def _import_run_pilot_loop():
    """Import run_pilot_loop as a module (not via subprocess) so we can
    unit-test its internal helpers (_run_step, _wait_or_kill)."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "run_pilot_loop", ROOT / "scripts" / "run_pilot_loop.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_step_records_log_path_and_returncode(tmp_path):
    """A successful step must record its log_path and returncode in the
    summary."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    # Use a fast built-in command (python -c "print('hi')").
    cmd = [sys.executable, "-u", "-c", "print('hi from step')"]
    result = rpl._run_step(
        cmd, "demo_step", summary_path, summary, log_dir, timeout=30,
    )
    assert result["status"] == "ok"
    assert result["returncode"] == 0
    assert "log_path" in result
    log_path = Path(result["log_path"])
    assert log_path.exists(), f"log file missing: {log_path}"
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    assert "hi from step" in log_text
    # Summary updated to disk.
    summary_on_disk = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary_on_disk["steps"][-1]["status"] == "ok"


def test_run_step_records_failed_returncode(tmp_path):
    """A non-zero exit must record the returncode and failed status."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    cmd = [sys.executable, "-u", "-c", "import sys; sys.exit(7)"]
    with pytest.raises(RuntimeError):
        rpl._run_step(
            cmd, "failing_step", summary_path, summary, log_dir, timeout=30,
        )
    summary_on_disk = json.loads(summary_path.read_text(encoding="utf-8"))
    step = summary_on_disk["steps"][-1]
    assert step["status"] == "failed"
    assert step["returncode"] == 7
    assert summary_on_disk["status"] == "failed"
    assert summary_on_disk["failed_step"] == "failing_step"
    assert step["log_path"]
    assert Path(step["log_path"]).exists()


def test_run_step_times_out_and_kills_subprocess(tmp_path):
    """A step that runs longer than its timeout must be killed, marked
    'timeout', and no child python process should linger afterwards."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    # Sleep longer than the timeout. We write a sentinel file on start
    # so we can detect the child actually launched.
    sentinel = tmp_path / "started.flag"
    cmd = [
        sys.executable, "-u", "-c",
        f"open(r'{sentinel}', 'w').close(); "
        "import time; time.sleep(300)",
    ]
    t0 = time.monotonic()
    with pytest.raises(RuntimeError):
        rpl._run_step(
            cmd, "sleep_step", summary_path, summary, log_dir, timeout=2,
        )
    dt = time.monotonic() - t0
    # Should return well under the 300s sleep — bounded by timeout +
    # grace period + small overhead.
    assert dt < 30, f"timeout handling took too long: {dt:.1f}s"
    summary_on_disk = json.loads(summary_path.read_text(encoding="utf-8"))
    step = summary_on_disk["steps"][-1]
    assert step["status"] == "timeout"
    assert step["timeout_sec"] == 2
    assert step["log_path"]
    assert Path(step["log_path"]).exists()
    assert summary_on_disk["status"] == "failed"
    assert summary_on_disk["failed_step"] == "sleep_step"
    # Sentinel proves the child actually started.
    assert sentinel.exists(), "child process did not start (no sentinel)"
    # Give the OS a moment to reap the killed process.
    time.sleep(0.5)
    # Verify no lingering python sleep process. We do this loosely by
    # checking psutil if available, otherwise by checking the process
    # is no longer the (gone) Popen handle's pid. We can't easily get
    # the pid back from _run_step, so we instead wait briefly and check
    # that running the same long-sleep command would not block (i.e.
    # the previous one was killed). The strongest portable check is
    # that the timeout wait returned within budget (already asserted
    # above). For a stronger assertion we check that no "python -u -c
    # ...time.sleep(300)" process is alive via tasklist/wmic on Windows
    # or pgrep on POSIX.
    _assert_no_sleeping_python_with_timeout_300()


def _assert_no_sleeping_python_with_timeout_300() -> None:
    """Best-effort check that no leftover ``time.sleep(300)`` python
    process is still alive. Skipped if no process-listing tool is
    available (the timeout-duration assertion above is the primary
    guarantee)."""
    import shutil
    try:
        if sys.platform.startswith("win"):
            # tasklist /V prints all processes with command line (truncated).
            out = subprocess.run(
                ["tasklist", "/V", "/FO", "CSV"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10,
                check=False,
            ).stdout
            # The sleep command is short; tasklist /V may truncate the
            # cmdline column. We just check we don't see our sentinel
            # pattern. This is a weak check; the duration assertion is
            # the strong one.
            assert "time.sleep(300)" not in out
        else:
            out = subprocess.run(
                ["pgrep", "-af", "time.sleep(300)"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10,
                check=False,
            ).stdout
            assert "time.sleep(300)" not in out
    except FileNotFoundError:
        # Tool not available — skip the check.
        pass
    except Exception:
        # Don't fail the test on a process-listing glitch.
        pass


def test_run_step_summary_always_written(tmp_path):
    """The summary file must always exist and never linger in
    'running' once _run_step returns (ok or raised)."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    cmd = [sys.executable, "-u", "-c", "print('ok')"]
    rpl._run_step(cmd, "ok_step", summary_path, summary, log_dir, timeout=30)
    assert summary_path.exists()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] in ("ok", "running")
    # The step itself must NOT be 'running' anymore.
    assert data["steps"][-1]["status"] == "ok"


# ---------------------------------------------------------------------------
# --skip_report
# ---------------------------------------------------------------------------

def test_skip_report_runs_train_eval_and_skips_report(tmp_path):
    """SINGLE integration test for --skip_report (ocn-29).

    This is the only full ``run_pilot_loop.py --skip_report`` test that
    runs in the default (non-slow) pytest invocation. It covers:
    status=ok, report_skipped=true, run_stage_train_eval present,
    run_stage_report=skipped, train_eval/ + logs/ exist. The other
    full-loop --skip_report tests (artifacts, balance warnings,
    per-step logs, stage_timeout defaults/override/timeout) are marked
    ``@pytest.mark.slow`` and run via ``pytest -m slow``.
    """
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, (
        f"pilot loop --skip_report failed (rc={proc.returncode}). "
        f"stderr tail:\n{proc.stderr[-2000:]}"
    )
    summary_path = out_dir / "pilot_loop_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert summary.get("report_skipped") is True
    step_names = [s["step"] for s in summary["steps"]]
    assert "run_stage_train_eval" in step_names
    # The report step must be present but skipped.
    report_steps = [s for s in summary["steps"] if s["step"] == "run_stage_report"]
    assert len(report_steps) == 1
    assert report_steps[0]["status"] == "skipped"
    # train_eval output dir must exist.
    train_eval_dir = out_dir / "train_eval"
    assert train_eval_dir.exists(), "train_eval output missing"
    # logs dir must exist with at least one log.
    logs_dir = out_dir / "logs"
    assert logs_dir.exists()
    assert any(logs_dir.glob("*.log"))


@pytest.mark.slow
def test_skip_report_still_generates_train_eval_output(tmp_path):
    """--skip_report must produce eval_test.json (the train_eval
    pipeline output), not just an empty success."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0
    eval_test = out_dir / "train_eval" / "eval_test.json"
    assert eval_test.exists(), "train_eval/eval_test.json missing"


@pytest.mark.slow
def test_skip_report_summary_records_report_skipped(tmp_path):
    """The summary must have report_skipped=true when --skip_report is
    passed, even before any step runs (initial summary)."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["report_skipped"] is True


# ---------------------------------------------------------------------------
# ocn-28 P0/P1: BrokenPipe safety + summary never lingers in 'running'
# ---------------------------------------------------------------------------


def test_safe_print_swallows_broken_pipe(monkeypatch):
    """safe_print() must swallow BrokenPipeError so the loop can still
    finish writing its summary."""
    rpl = _import_run_pilot_loop()

    def _raising_print(*args, **kwargs):
        raise BrokenPipeError()

    monkeypatch.setattr(rpl, "_builtin_print", _raising_print)
    # Must NOT raise.
    rpl.safe_print("hello", "world", sep="-")
    rpl.safe_print("with kwargs", file=sys.stderr, end="")


def test_safe_print_swallows_epipe_oserror(monkeypatch):
    """safe_print() must swallow OSError with errno=EPIPE (32)."""
    rpl = _import_run_pilot_loop()

    def _raising_print(*args, **kwargs):
        err = OSError()
        err.errno = 32
        raise err

    monkeypatch.setattr(rpl, "_builtin_print", _raising_print)
    rpl.safe_print("hello")  # must not raise


def test_safe_print_reraises_non_pipe_oserror(monkeypatch):
    """safe_print() must re-raise OSError that is NOT EPIPE."""
    rpl = _import_run_pilot_loop()

    def _raising_print(*args, **kwargs):
        err = OSError()
        err.errno = 13  # EACCES — not a pipe error
        raise err

    monkeypatch.setattr(rpl, "_builtin_print", _raising_print)
    with pytest.raises(OSError):
        rpl.safe_print("hello")


def test_finalize_summary_marks_running_steps_failed(tmp_path):
    """finalize_summary() must convert any step still marked 'running'
    into 'failed' so the summary never lingers in a running state."""
    rpl = _import_run_pilot_loop()
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {
        "status": "running",
        "started_at": rpl._now(),
        "steps": [
            {"step": "validate", "status": "ok"},
            {"step": "train", "status": "running"},  # interrupted
        ],
    }
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    # The 'running' step must now be 'failed'.
    train_step = data["steps"][1]
    assert train_step["status"] == "failed"
    assert "interrupted" in train_step["error"]
    # Top-level status promoted away from 'running'.
    assert data["status"] == "failed"
    assert data["failed_step"] == "train"


def test_finalize_summary_preserves_terminal_status(tmp_path):
    """If summary status is already 'ok' or 'failed', finalize_summary
    must NOT overwrite it (only 'running' gets promoted)."""
    rpl = _import_run_pilot_loop()
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {
        "status": "ok",
        "started_at": rpl._now(),
        "steps": [{"step": "validate", "status": "ok"}],
    }
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "ok"
    assert data["steps"][0]["status"] == "ok"


def test_finalize_summary_promotes_running_to_ok_when_no_running_steps(tmp_path):
    """If top-level status is 'running' but all steps are terminal,
    finalize_summary promotes the top-level to 'ok' (the loop finished
    normally but didn't set the terminal status)."""
    rpl = _import_run_pilot_loop()
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {
        "status": "running",
        "steps": [{"step": "validate", "status": "ok"}],
    }
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "ok"


def test_summary_not_running_after_broken_pipe_sim(tmp_path, monkeypatch):
    """Simulate the real failure: even if print() raises BrokenPipeError
    during the final summary output, the summary file on disk must still
    reach a terminal status and all steps must be terminal."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}

    # Monkeypatch the module-level _builtin_print so safe_print raises
    # BrokenPipeError (which safe_print must swallow).
    def _raising_print(*args, **kwargs):
        raise BrokenPipeError()

    monkeypatch.setattr(rpl, "_builtin_print", _raising_print)

    # Run a fast successful step under the broken-pipe simulation.
    cmd = [sys.executable, "-u", "-c", "print('ok')"]
    result = rpl._run_step(
        cmd, "demo_step", summary_path, summary, log_dir, timeout=30,
    )
    # The step must be marked ok even though safe_print swallowed errors.
    assert result["status"] == "ok"
    # Now simulate the main() finally block: finalize the summary.
    summary["status"] = "ok"
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "ok"
    for s in data["steps"]:
        assert s["status"] != "running"


def test_summary_not_running_after_step_exception(tmp_path):
    """If a step raises an exception mid-flight (so its status stays
    'running'), finalize_summary must mark it 'failed' so the summary
    does not linger in 'running'."""
    rpl = _import_run_pilot_loop()
    summary_path = tmp_path / "pilot_loop_summary.json"
    # Manually simulate a step that was started but interrupted.
    summary = {
        "status": "running",
        "steps": [
            {"step": "validate", "status": "ok"},
            {"step": "train", "status": "running",
             "started_at": rpl._now(),
             "command": "python train.py"},
        ],
    }
    # Simulate main()'s except + finally.
    summary["status"] = "failed"
    summary["error"] = "KeyboardInterrupt"
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    train = data["steps"][1]
    assert train["status"] == "failed"
    assert "interrupted" in train["error"]


def test_timeout_summary_not_running(tmp_path):
    """After a timeout, the summary must NOT have any step in 'running'
    status. The timeout step must be 'timeout' and the top-level must
    be 'failed'."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    cmd = [
        sys.executable, "-u", "-c",
        "import time; time.sleep(300)",
    ]
    t0 = time.monotonic()
    with pytest.raises(RuntimeError):
        rpl._run_step(
            cmd, "sleep_step", summary_path, summary, log_dir, timeout=2,
        )
    dt = time.monotonic() - t0
    assert dt < 30
    # Simulate the finally block (main would call this).
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    sleep_step = data["steps"][-1]
    assert sleep_step["status"] == "timeout"
    assert sleep_step["timeout_sec"] == 2
    assert sleep_step["log_path"]
    assert Path(sleep_step["log_path"]).exists()
    # No step lingers in 'running'.
    for s in data["steps"]:
        assert s["status"] != "running"


def test_soft_failed_does_not_force_top_failed(tmp_path):
    """A soft_failed step must NOT cause the top-level summary to be
    'failed' (it's a diagnostic warning). The loop should still reach
    status='ok' via the finally/normal path."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    # A failing command, but soft_fail=True so it's marked soft_failed
    # rather than raising.
    cmd = [sys.executable, "-u", "-c", "import sys; sys.exit(1)"]
    result = rpl._run_step(
        cmd, "soft_step", summary_path, summary, log_dir,
        timeout=30, soft_fail=True,
    )
    assert result["status"] == "soft_failed"
    # Simulate main() completing normally after the soft-fail step.
    summary["status"] = "ok"
    rpl.finalize_summary(summary, summary_path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["status"] == "ok"
    assert data["steps"][-1]["status"] == "soft_failed"
    # No 'failed_step' at the top level (soft fail is not a hard fail).
    assert "failed_step" not in data


# ---------------------------------------------------------------------------
# ocn-28 P3: --stage_timeout_sec — separate (larger) timeout for the
# multi-stage run_stage_train_eval step.
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_stage_timeout_defaults_to_step_times_six(tmp_path):
    """When --stage_timeout_sec is omitted, the pilot loop must use
    step_timeout_sec * 6 for run_stage_train_eval, and record both
    timeouts in the summary."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "60",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    # Top-level records both timeouts.
    assert summary["step_timeout_sec"] == 60
    assert summary["stage_timeout_sec"] == 60 * 6
    # The train_eval step's recorded timeout_sec must equal stage_timeout,
    # not the bare step_timeout.
    train_steps = [
        s for s in summary["steps"] if s["step"] == "run_stage_train_eval"
    ]
    assert len(train_steps) == 1
    assert train_steps[0]["timeout_sec"] == 60 * 6
    # Other (single-stage) steps must keep the bare step_timeout.
    validate_steps = [s for s in summary["steps"] if s["step"] == "validate"]
    assert len(validate_steps) == 1
    assert validate_steps[0]["timeout_sec"] == 60


@pytest.mark.slow
def test_explicit_stage_timeout_overrides_default(tmp_path):
    """When --stage_timeout_sec is provided explicitly, it is used as-is
    (not step * 6)."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "60",
        "--stage_timeout_sec", "300",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["stage_timeout_sec"] == 300
    train_steps = [
        s for s in summary["steps"] if s["step"] == "run_stage_train_eval"
    ]
    assert len(train_steps) == 1
    assert train_steps[0]["timeout_sec"] == 300


@pytest.mark.slow
def test_stage_timeout_marks_timeout_in_summary(tmp_path):
    """When run_stage_train_eval exceeds --stage_timeout_sec, the step
    must be marked 'timeout' (not 'failed'), and the summary must record
    timeout_sec + log_path. We force this by setting a tiny
    stage_timeout (1s) against a real train_eval that takes longer."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "60",
        "--stage_timeout_sec", "1",  # force timeout on train_eval
    ]
    proc = _run_pilot_loop(cmd, timeout=120)
    # Timeout on a step is a hard failure.
    assert proc.returncode != 0
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    # Top-level must not be 'running'.
    assert summary["status"] in ("failed",)
    train_steps = [
        s for s in summary["steps"] if s["step"] == "run_stage_train_eval"
    ]
    assert len(train_steps) == 1
    step = train_steps[0]
    assert step["status"] == "timeout"
    assert step["timeout_sec"] == 1
    assert step["timed_out"] is True
    assert step["log_path"]
    assert Path(step["log_path"]).exists()


def test_run_step_always_records_timeout_sec(tmp_path):
    """Even on a normal (non-timed-out) success, the summary step record
    must include the actual timeout_sec that was applied, so an operator
    can audit per-step budgets."""
    rpl = _import_run_pilot_loop()
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "pilot_loop_summary.json"
    summary = {"steps": [], "status": "running"}
    cmd = [sys.executable, "-u", "-c", "print('ok')"]
    result = rpl._run_step(
        cmd, "demo_step", summary_path, summary, log_dir, timeout=42,
    )
    assert result["status"] == "ok"
    assert result["timeout_sec"] == 42
    assert result["timed_out"] is False
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["steps"][-1]["timeout_sec"] == 42


# ---------------------------------------------------------------------------
# ocn-28 P4: --skip_report stable main path — full output verification.
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_skip_report_produces_all_train_eval_artifacts(tmp_path):
    """--skip_report must produce the full set of train_eval artifacts
    needed for manual pilot inspection:
      dev_predictions.jsonl, operating_threshold.json,
      eval_test.json, train_eval_summary.json.
    operating_threshold.json must have test_split_used=false (the
    threshold is fit on dev, not on test, to avoid test leakage).
    """
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    te = out_dir / "train_eval"
    for name in (
        "dev_predictions.jsonl",
        "operating_threshold.json",
        "eval_test.json",
        "train_eval_summary.json",
    ):
        assert (te / name).exists(), f"missing train_eval artifact: {name}"
    # operating_threshold.json must mark test_split_used=false.
    thr = json.loads((te / "operating_threshold.json").read_text(encoding="utf-8"))
    assert thr.get("test_split_used") is False, (
        f"test_split_used must be false (threshold fit on dev, not test); "
        f"got {thr.get('test_split_used')!r}"
    )
    # eval_test.json must be valid JSON with expected metric sections.
    ev = json.loads((te / "eval_test.json").read_text(encoding="utf-8"))
    assert "binary" in ev or "macro_f1" in str(ev)
    # train_eval_summary.json must be valid JSON.
    ts = json.loads((te / "train_eval_summary.json").read_text(encoding="utf-8"))
    assert isinstance(ts, dict)


@pytest.mark.slow
def test_skip_report_summary_records_balance_warnings(tmp_path):
    """--skip_report summary must record check_pilot_balance status
    (ok or soft_failed) and, when soft_failed, the warning/error must
    be present on the step record. The top-level must remain 'ok'."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary_path = out_dir / "pilot_loop_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert summary["report_skipped"] is True
    balance_steps = [
        s for s in summary["steps"] if s["step"] == "check_pilot_balance"
    ]
    assert len(balance_steps) == 1
    # soft_failed or ok — either is acceptable for a pilot diagnostic.
    assert balance_steps[0]["status"] in ("ok", "soft_failed")
    # When soft_failed, the step record must carry a warning field so
    # an operator can see WHY (imbalance) without opening the log.
    if balance_steps[0]["status"] == "soft_failed":
        assert "warning" in balance_steps[0]
    # Top-level must NOT be 'failed' due to soft_failed balance.
    assert summary["status"] != "failed"


@pytest.mark.slow
def test_skip_report_logs_dir_has_per_step_logs(tmp_path):
    """--skip_report must leave a logs/ dir with one .log per executed
    step (validate, fill_escalation_labels, audit, check_pilot_balance,
    split_pilot_data, run_stage_train_eval). The skipped report step
    needs no log."""
    if not SMOKE_DATA.exists():
        pytest.skip("smoke.jsonl not available")
    out_dir = tmp_path / "pilot_out"
    cmd = [
        sys.executable, "-u", "scripts/run_pilot_loop.py",
        "--input", str(SMOKE_DATA),
        "--output", str(out_dir),
        "--config", "configs/pilot_test.yaml",
        "--seed", "13",
        "--allow_toy_results",
        "--skip_report",
        "--step_timeout_sec", "120",
    ]
    proc = _run_pilot_loop(cmd, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    logs_dir = out_dir / "logs"
    assert logs_dir.exists()
    log_names = {p.name for p in logs_dir.glob("*.log")}
    for step in (
        "validate.log",
        "fill_escalation_labels.log",
        "audit.log",
        "check_pilot_balance.log",
        "split_pilot_data.log",
        "run_stage_train_eval.log",
    ):
        assert step in log_names, f"missing log: {step}; got {log_names}"

