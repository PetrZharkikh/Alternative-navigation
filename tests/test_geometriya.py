import time
from geometriya import dlin, uravnPryamoy, peresechPryamyh, peresechOtrezkov

def test_dlin_runtime():
    start = time.perf_counter()
    result = dlin((0, 0), (3, 4))
    duration = time.perf_counter() - start
    assert result == 5
    assert duration >= 0

def test_uravn_runtime():
    start = time.perf_counter()
    coeffs = uravnPryamoy((0, 0), (1, 1))
    duration = time.perf_counter() - start
    assert coeffs == (-1, 1, 0)
    assert duration >= 0

def test_peresech_functions():
    start = time.perf_counter()
    p = peresechPryamyh((1, -1, 0), (1, 0, -1))
    q = peresechOtrezkov(((0, 0), (3, 0)), ((1, -1), (1, 1)))
    duration = time.perf_counter() - start
    assert p == (1.0, -1.0)
    assert q == (1.0, 0.0)
    assert duration >= 0
