from .adapters.rtl import RTLTask
from .adapters.ode import ODETask
from .adapters.logic import LogicTask
from .verifiers.rtl import RTLVerifier
from .verifiers.ode import ODEVerifier
from .verifiers.logic import LogicVerifier

TASKS={"rtl":(RTLTask,RTLVerifier),"ode":(ODETask,ODEVerifier),"logic":(LogicTask,LogicVerifier)}
def resolve(domain): 
    if domain not in TASKS: raise KeyError(domain)
    a,v=TASKS[domain]; return a(),v()
