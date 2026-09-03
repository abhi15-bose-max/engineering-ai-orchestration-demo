from pathlib import Path
from backend.core.orchestrator import Orchestrator
from backend.core.storage import JsonStore
from backend.adapters.ode import ODETask
from backend.verifiers.ode import ODEVerifier
from backend.core.models import MockGPT
def test_bounded_repair(tmp_path):
 t=Orchestrator(JsonStore(tmp_path)).run("r",ODETask(),ODEVerifier(),MockGPT(),"Solve y'(x) + y(x) = 0 with y(0) = 2.",3,tmp_path/"run")
 assert t.final_status=="VERIFIED"
 assert len(t.attempts)==2
