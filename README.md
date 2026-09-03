# Engineering AI Orchestration & Validation Infrastructure

**Public Technical Demonstrator**

> Bring your model. Bring your verifier. We run the engineering loop.

This MVP demonstrates a model-agnostic orchestration layer between AI generation and engineering ground truth:

**Generate → Verify → Diagnose → Repair → Re-verify → Verified result + evidence + trajectory + evaluation**

## What came from the supplied prototypes

The RTL prototype was audited first and its useful verifier/tooling patterns were retained: a model adapter, RTL extraction, a bounded repair loop, Verilator-first verification, controlled Yosys synthesis, diagnostics, and trajectory artifacts. The original RTL prototype executes a fixed Verilator lint command and only invokes Yosys after Verilator passes.

The DE-SLM prototype supplied the complementary SymPy ideas: structured ODE problems, restricted candidate parsing, equation-residual checking, initial/boundary-condition checks, deterministic failure classification, bounded repair, and JSON trajectory persistence.

The unified code intentionally does not carry forward the local Qwen inference requirement. GPT and Gemini are server-side hosted adapters; deterministic mock behavior exists only for offline tests/demo mode.

## Architecture

`frontend → FastAPI → orchestrator → model adapter + task adapter + verifier → trajectory/evaluation`

Core abstractions:
- `ModelAdapter`: GPT/Gemini behind one interface.
- `TaskAdapter`: domain-specific prompting and candidate normalization.
- `Verifier`: normalized `PASS/FAIL/ERROR`, failure class, diagnostics, evidence.
- `Orchestrator`: shared bounded generate/verify/repair loop.
- `Trajectory`: every attempt is structured data.
- `Evaluation`: first-pass success, final success, attempts, repair success, latency, failures.

Domains:
- RTL → Verilator + Yosys
- ODE → SymPy
- Logic → Z3 / SMT

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# export variables from .env using your preferred method
python -m backend
```

Open `http://localhost:8000`.

For a deterministic smoke demo without API keys:

```bash
DEMO_MODE=1 python -m backend
```

In public deployment, leave `DEMO_MODE=0` and configure the required server-side API keys. Missing keys are represented as unavailable models rather than exposed to the browser.

## API

- `GET /api/health`
- `GET /api/models`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/trajectory/{model}`
- `GET /api/runs/{run_id}/export/{model}`

Example run request:

```json
{"domain":"rtl","models":["gpt","gemini"],"task":"Create a synthesizable 4-bit counter with clk, reset and enable.","max_attempts":3}
```

## Security boundaries

- No model-generated shell commands are executed.
- RTL verifier commands are fixed by backend code.
- Verifier subprocesses have timeouts.
- Each run/model gets a separate temporary working directory under `data/runs`.
- Input sizes and repair iterations are bounded.
- API keys are server-side only.
- ODE parsing uses a restricted SymPy namespace and rejects dangerous tokens.
- Logic candidates are restricted to a small arithmetic grammar before solver construction.
- Raw model chain-of-thought is neither requested nor stored.

This is **not production enterprise infrastructure**. It has no authentication, billing, multi-tenancy, Kubernetes, queueing, or production-grade sandboxing. For a public deployment, run the verifier toolchains in an isolated container/runtime with appropriate OS-level resource limits.

## Deployment

The Docker image supplies the Python application dependencies. Verilator and Yosys are external system dependencies and should be installed in the deployment image or attached verification environment. No GPU is required.

## Prototype relationship

The supplied repositories are implementation assets rather than architectural constraints. Their working ideas were generalized rather than duplicated. The flagship RTL flow preserves the original Verilator → Yosys ordering; the ODE flow preserves independent SymPy verification and bounded repair; both now use the same orchestration and trajectory concepts.

## Supported demo examples

- RTL: `Create a synthesizable 4-bit counter with clk, reset and enable.`
- ODE: `Solve y'(x) + y(x) = 0 with y(0) = 2.`
- Logic: `Determine whether x >= 0, y >= 0, x + y <= 10 and x = 6, y = 5 are simultaneously satisfiable.`

The public ODE and Logic adapters intentionally support small, formalizable demo classes rather than pretending to be universal mathematical or legal reasoning systems.
