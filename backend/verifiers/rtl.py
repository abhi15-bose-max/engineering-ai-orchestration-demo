from __future__ import annotations
import re, subprocess, time
from pathlib import Path
from ..core.contracts import VerificationResult

def _run(cmd,cwd,timeout):
    try:
        p=subprocess.run(cmd,cwd=str(cwd),capture_output=True,text=True,timeout=timeout,check=False)
        return p.returncode,p.stdout,p.stderr,False
    except subprocess.TimeoutExpired as e:
        return None,e.stdout or "",f"Verifier timed out after {timeout}s.",True

class RTLVerifier:
    name="Verilator + Yosys"
    def verify(self,candidate,task,work_dir):
        work=Path(work_dir); work.mkdir(parents=True,exist_ok=True)
        rtl=work/"candidate.sv"; rtl.write_text(candidate,encoding="utf-8")
        rc,out,err,to=_run(["verilator","--lint-only","--language","1800-2012",str(rtl)],work,20)
        if to: return VerificationResult("FAIL","verifier_timeout",err,{"stage":"verilator"})
        if rc!=0:
            return VerificationResult("FAIL",self._classify_verilator(err),err,{"stage":"verilator","stdout":out})
        top=self._top(candidate)
        if not top: return VerificationResult("FAIL","invalid_module","No top module found.",{"stage":"verilator"})
        ys=work/"verify.ys"; net=work/"synthesized_netlist.v"
        # Fixed verifier-owned command script. The model cannot influence executable/arguments.
        ys.write_text("\n".join([
            f"read_verilog -sv {rtl}",f"hierarchy -check -top {top}","proc","opt","check",
            f"synth -top {top}","stat",f"write_verilog -noattr {net}"
        ]),encoding="utf-8")
        rc2,out2,err2,to2=_run(["yosys","-s",str(ys)],work,40)
        if to2: return VerificationResult("FAIL","verifier_timeout",err2,{"stage":"yosys","top_module":top})
        passed=rc2==0 and "found and reported 0 problems" in (out2+"\n"+err2)
        if not passed:
            return VerificationResult("FAIL","synthesis_error",err2 or out2,{"stage":"yosys","top_module":top,"netlist":str(net) if net.exists() else None})
        stats=self._stats(out2)
        return VerificationResult("PASS",None,"",{"stage":"yosys","top_module":top,"statistics":stats,"netlist":str(net)})
    @staticmethod
    def _top(s):
        m=re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)",s); return m.group(1) if m else None
    @staticmethod
    def _classify_verilator(e):
        if "syntax" in e.lower(): return "syntax_error"
        return "lint_error"
    @staticmethod
    def _stats(s):
        def n(p): 
            m=re.search(p,s); return int(m.group(1)) if m else None
        return {"wires":n(r"Number of wires:\s+(\d+)"),"wire_bits":n(r"Number of wire bits:\s+(\d+)"),
                "cells":n(r"Number of cells:\s+(\d+)"),"processes":n(r"Number of processes:\s+(\d+)")}
