from __future__ import annotations
import time
from datetime import datetime, timezone
from .contracts import Trajectory, Attempt, VerificationResult
from .evaluation import evaluate
from .storage import JsonStore

class Orchestrator:
    def __init__(self, store: JsonStore):
        self.store = store

    def run(self, run_id, task_adapter, verifier, model, task, max_attempts, work_dir, emit=None):
        started_total = time.perf_counter()
        t = Trajectory(
            run_id=run_id, timestamp=datetime.now(timezone.utc).isoformat(),
            task=task, domain=task_adapter.domain, model=model.name, verifier=verifier.name
        )
        candidate = None
        previous_verification = None

        for n in range(1, max_attempts + 1):
            try:
                if n == 1:
                    if emit: emit({"type":"stage","stage":"generate","status":"running","attempt":n})
                    raw = model.generate(task_adapter.build_generation_prompt(task))
                else:
                    if emit: emit({"type":"stage","stage":"repair","status":"running","attempt":n})
                    raw = model.repair(task_adapter.build_repair_prompt(task, candidate, previous_verification))
                call_start = time.perf_counter()
                # call_start is intentionally local to keep the metric focused on normalization/API time.
                candidate = task_adapter.normalize_candidate(raw)
                call_ms = int((time.perf_counter()-call_start)*1000)
            except Exception as exc:
                verification = VerificationResult("ERROR","model_error",str(exc),{})
                t.attempts.append(Attempt(n, candidate or "", verification, latency_ms=int((time.perf_counter()-started_total)*1000)))
                t.error = str(exc)
                if emit: emit({"type":"attempt","attempt":n,"candidate":candidate or "","verification":verification.__dict__})
                break

            if emit: emit({"type":"stage","stage":"verify","status":"running","attempt":n})
            verify_start=time.perf_counter()
            verification = verifier.verify(candidate, task, work_dir)
            verification.duration_ms = int((time.perf_counter()-verify_start)*1000)
            attempt = Attempt(n, candidate, verification, latency_ms=call_ms)
            t.attempts.append(attempt)
            if emit: emit({"type":"attempt","attempt":n,"candidate":candidate,"verification":verification.__dict__})

            if verification.status == "PASS":
                t.final_status="VERIFIED"
                t.final_artifact=candidate
                if emit: emit({"type":"stage","stage":"verified","status":"complete","attempt":n})
                break
            previous_verification = verification
            if emit: emit({"type":"stage","stage":"diagnose","status":"complete","attempt":n})
            if n < max_attempts:
                attempt.repair_feedback = verification.diagnostics or str(verification.evidence)

        latency=int((time.perf_counter()-started_total)*1000)
        t.evaluation=evaluate(t, model.name, latency)
        self.store.save(t)
        if emit: emit({"type":"complete","status":t.final_status,"trajectory":t.evaluation,"final_artifact":t.final_artifact})
        return t
