import time
from ChislMetody import bisection

def test_bisection_runtime():
    start = time.perf_counter()
    root = bisection(0, 3, lambda x: x*x - 4)
    duration = time.perf_counter() - start
    assert abs(root - 2) < 0.001
    assert duration >= 0
