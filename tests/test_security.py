from backend.verifiers.ode import ODEVerifier
def test_unsafe_rejected():
 r=ODEVerifier().verify("__import__('os').system('echo bad')","Solve y'(x) + y(x) = 0 with y(0) = 2.")
 assert r.status=="FAIL"
