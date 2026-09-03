from backend.verifiers.ode import ODEVerifier
def test_ode_pass(): assert ODEVerifier().verify("2*exp(-x)","Solve y'(x) + y(x) = 0 with y(0) = 2.").status=="PASS"
def test_ode_fail(): assert ODEVerifier().verify("exp(-x)","Solve y'(x) + y(x) = 0 with y(0) = 2.").failure_class=="initial_condition_mismatch"
