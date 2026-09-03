from __future__ import annotations
import re, multiprocessing as mp
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from ..core.contracts import VerificationResult

ALLOWED={"E":sp.E,"I":sp.I,"pi":sp.pi,"exp":sp.exp,"log":sp.log,"sqrt":sp.sqrt,"sin":sp.sin,"cos":sp.cos,"tan":sp.tan,"sinh":sp.sinh,"cosh":sp.cosh,"tanh":sp.tanh,"Abs":sp.Abs}
DANGEROUS=re.compile(r"(__|import|lambda|eval|exec|open\s*\(|globals|locals|builtins|os\.|sys\.)",re.I)

def parse_safe(text):
    if not isinstance(text,str) or len(text)>4000 or DANGEROUS.search(text): raise ValueError("Forbidden or oversized expression.")
    x=sp.Symbol("x",real=True); y=sp.Function("y")
    names=dict(ALLOWED); names.update({"x":x,"y":y,"Derivative":sp.Derivative,"Eq":sp.Eq})
    return parse_expr(text.replace("^","**"),local_dict=names,transformations=standard_transformations+(implicit_multiplication_application,),evaluate=True)

def _problem(task):
    # Small, explicit safe parser for the public demo's supported ODE family.
    s=task.lower().replace(" ","")
    if "y'(x)+y(x)=0" in s or "y'(x)+y(x)=0" in s:
        eq=sp.Derivative(sp.Function("y")(sp.Symbol("x",real=True)),sp.Symbol("x",real=True))+sp.Function("y")(sp.Symbol("x",real=True))
    else:
        raise ValueError("Demo ODE parser supports the first-order linear example: y'(x) + y(x) = 0.")
    m=re.search(r"y\(([-+]?\d+(?:\.\d+)?)\)=([-+]?\d+(?:\.\d+)?)",s)
    if not m: raise ValueError("Provide an initial condition such as y(0)=2.")
    x=sp.Symbol("x",real=True); y=sp.Function("y")
    return eq, x, y, sp.Eq(y(sp.Float(m.group(1)) if "." in m.group(1) else sp.Integer(m.group(1))), sp.Float(m.group(2)) if "." in m.group(2) else sp.Integer(m.group(2)))

class ODEVerifier:
    name="SymPy"
    def verify(self,candidate,task,work_dir=None):
        try:
            eq,x,y,cond=_problem(task)
            expr=parse_safe(candidate)
            residual=sp.simplify(eq.subs(y(x),expr).doit())
            val=sp.simplify(expr.subs(x,cond.lhs.args[0])-cond.rhs)
            if residual!=0: return VerificationResult("FAIL","nonzero_symbolic_residual",f"Equation residual is {residual}, not 0.",{"equation_residual":str(residual),"condition":"FAIL"})
            if val!=0: return VerificationResult("FAIL","initial_condition_mismatch",f"Initial condition residual is {val}, not 0.",{"equation_residual":"0","condition_residual":str(val)})
            return VerificationResult("PASS",evidence={"equation_residual":"0","condition":"PASS","overall":"PASS"})
        except ValueError as e: return VerificationResult("FAIL","malformed_candidate",str(e),{})
        except Exception as e: return VerificationResult("ERROR","verifier_error",str(e),{})
