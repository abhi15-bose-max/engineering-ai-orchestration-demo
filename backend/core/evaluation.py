from collections import Counter
from typing import Iterable
from .contracts import Trajectory

def evaluate(t: Trajectory, model_name: str, latency_ms: int) -> dict:
    first_pass = bool(t.attempts and t.attempts[0].verification.status == "PASS")
    final_success = t.final_status == "VERIFIED"
    repair_success = final_success and len(t.attempts) > 1
    failures = Counter(
        a.verification.failure_class for a in t.attempts
        if a.verification.failure_class
    )
    return {
        "first_pass_success": first_pass,
        "final_success": final_success,
        "attempts": len(t.attempts),
        "repair_success": repair_success,
        "total_latency_ms": latency_ms,
        "model": model_name,
        "domain": t.domain,
        "failure_classes": dict(failures),
    }
