import json,re
class LogicTask:
    domain="logic"; verifier_name="Z3 / SMT"
    def build_generation_prompt(self,task):
        return f"""Formalize the constraint problem below. Return ONLY JSON with keys constraints (array of arithmetic constraints) and claim (arithmetic equalities). Use only variables x,y and operators >=,<=,>,<,==,+, -, *, integers.
TASK:
{task}"""
    def build_repair_prompt(self,task,candidate,verification):
        return f"""Repair the formal constraint candidate. Return ONLY JSON with keys constraints and claim. Keep the original constraints unchanged.
TASK: {task}
CURRENT: {candidate}
VERIFIER: {verification.diagnostics}
EVIDENCE: {verification.evidence}"""
    def normalize_candidate(self,raw):
        m=re.search(r"\{.*\}",(raw or "").strip(),re.S)
        if not m: raise ValueError("Malformed logic JSON candidate.")
        o=json.loads(m.group(0))
        if not isinstance(o.get("constraints"),list) or not isinstance(o.get("claim"),str): raise ValueError("Invalid logic candidate.")
        return json.dumps({"constraints":o["constraints"],"claim":o["claim"]})
