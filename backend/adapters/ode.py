import json,re
class ODETask:
    domain="ode"; verifier_name="SymPy"
    def build_generation_prompt(self, task):
        return f"""You are an ODE solver. Return ONLY JSON: {{"solution":"<explicit SymPy expression>"}}. Do not return equations or prose. SymPy independently verifies correctness.
ODE PROBLEM:
{task}"""
    def build_repair_prompt(self,task,candidate,verification):
        return f"""Repair the ODE candidate. Return ONLY JSON {{\"solution\":\"<explicit SymPy expression>\"}}.
ORIGINAL ODE: {task}
CURRENT CANDIDATE: {candidate}
VERIFIER: {verification.diagnostics}
EVIDENCE: {verification.evidence}"""
    def normalize_candidate(self,raw):
        text=(raw or "").strip()
        m=re.search(r"\{.*\}",text,re.S)
        if not m: raise ValueError("Malformed ODE JSON candidate.")
        obj=json.loads(m.group(0))
        sol=obj.get("solution")
        if not isinstance(sol,str) or not sol.strip() or len(sol)>4000: raise ValueError("Invalid ODE solution.")
        return sol.strip()
