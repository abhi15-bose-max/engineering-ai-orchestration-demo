import re
from ..core.contracts import VerificationResult

class RTLTask:
    domain="rtl"; verifier_name="Verilator + Yosys"
    def build_generation_prompt(self, task):
        return f"""You are an expert digital hardware designer. Convert the specification below into synthesizable SystemVerilog. Return ONLY the complete module source, no markdown or explanation.
SPECIFICATION:
{task}"""
    def build_repair_prompt(self, task, candidate, verification):
        return f"""Repair this SystemVerilog so it satisfies the original specification and the verifier feedback. Return ONLY complete SystemVerilog.
ORIGINAL:
{task}
CURRENT:
{candidate}
FAILED VERIFICATION:
{verification.diagnostics}
EVIDENCE:
{verification.evidence}"""
    def normalize_candidate(self, raw):
        text=(raw or "").strip()
        m=re.search(r"```(?:systemverilog|verilog|sv)?\s*(.*?)```",text,re.S|re.I)
        if m: text=m.group(1).strip()
        i=text.find("module ")
        if i>=0: text=text[i:]
        if len(text)>20000 or "module " not in text: raise ValueError("Malformed RTL candidate.")
        if re.search(r"\b(system|program|primitive|checker|import)\b",text): raise ValueError("Unsupported RTL construct.")
        return text
