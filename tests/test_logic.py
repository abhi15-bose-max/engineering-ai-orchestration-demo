import pytest
z3=pytest.importorskip("z3")
from backend.verifiers.logic import LogicVerifier
def test_logic_pass():
 r=LogicVerifier().verify('{"constraints":["x >= 0","y >= 0","x + y <= 10"],"claim":"x = 5 and y = 5"}',"demo")
 assert r.status=="PASS"
def test_logic_fail():
 r=LogicVerifier().verify('{"constraints":["x >= 0","y >= 0","x + y <= 10"],"claim":"x = 6 and y = 5"}',"demo")
 assert r.status=="FAIL"
