from __future__ import annotations
import ast, json, re
from ..core.contracts import VerificationResult

class LogicVerifier:
    name="Z3 / SMT"
    def verify(self,candidate,task,work_dir=None):
        try:
            from z3 import Int, Solver, sat, unsat
            o=json.loads(candidate); cs=o["constraints"]; claim=o["claim"]
            if len(cs)>12 or len(claim)>200: raise ValueError("Constraint limits exceeded.")
            x,y=Int("x"),Int("y"); env={"x":x,"y":y}
            def convert(node):
                if isinstance(node,ast.Expression): return convert(node.body)
                if isinstance(node,ast.Name) and node.id in env: return env[node.id]
                if isinstance(node,ast.Constant) and isinstance(node.value,int): return node.value
                if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)): return -convert(node.operand) if isinstance(node.op,ast.USub) else convert(node.operand)
                if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
                    a,b=convert(node.left),convert(node.right)
                    return {ast.Add:a+b,ast.Sub:a-b,ast.Mult:a*b,ast.Div:a/b}[type(node.op)]
                if isinstance(node,ast.Compare) and len(node.ops)==1:
                    a,b=convert(node.left),convert(node.comparators[0]); op=node.ops[0]
                    return {ast.GtE:a>=b,ast.LtE:a<=b,ast.Gt:a>b,ast.Lt:a<b,ast.Eq:a==b,ast.NotEq:a!=b}[type(op)]
                raise ValueError("Unsupported constraint syntax.")
            def expr(s):
                if not isinstance(s,str) or len(s)>200 or not re.fullmatch(r"[0-9xy+\-*/<>=() \t]+",s): raise ValueError("Unsupported constraint syntax.")
                return convert(ast.parse(s,mode="eval"))
            constraints=[expr(c) for c in cs]
            s=Solver(); s.add(*constraints)
            parts=[p.strip() for p in re.split(r"\band\b|,",claim,flags=re.I) if p.strip()]
            s.add(*(expr(p) for p in parts))
            r=s.check()
            if r==sat:
                return VerificationResult("PASS",evidence={"solver":"sat","constraints":cs,"claim":claim,"model":str(s.model())})
            if r==unsat:
                return VerificationResult("FAIL","unsatisfied_constraint","Claim cannot satisfy all constraints.",{"solver":"unsat"})
            return VerificationResult("ERROR","solver_error",str(r),{})
        except ValueError as e: return VerificationResult("FAIL","malformed_constraint",str(e),{})
        except Exception as e: return VerificationResult("ERROR","verifier_error",str(e),{})
