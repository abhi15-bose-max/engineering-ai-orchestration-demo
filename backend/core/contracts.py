from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass
class VerificationResult:
    status: str  # PASS | FAIL | ERROR
    failure_class: str | None = None
    diagnostics: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

@dataclass
class Attempt:
    attempt_id: int
    generated_artifact: str
    verification: VerificationResult
    repair_feedback: str | None = None
    repaired_artifact: str | None = None
    latency_ms: int = 0

@dataclass
class Trajectory:
    run_id: str
    timestamp: str
    task: str
    domain: str
    model: str
    verifier: str
    attempts: list[Attempt] = field(default_factory=list)
    final_status: str = "NOT_VERIFIED"
    final_artifact: str | None = None
    evaluation: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

class ModelAdapter(Protocol):
    name: str
    model_name: str
    def generate(self, prompt: str) -> str: ...
    def repair(self, prompt: str) -> str: ...

class TaskAdapter(Protocol):
    domain: str
    verifier_name: str
    def build_generation_prompt(self, task: str) -> str: ...
    def build_repair_prompt(self, task: str, candidate: str, verification: VerificationResult) -> str: ...
    def normalize_candidate(self, raw: str) -> str: ...

class Verifier(Protocol):
    name: str
    def verify(self, candidate: str, task: str, work_dir: Any = None) -> VerificationResult: ...
