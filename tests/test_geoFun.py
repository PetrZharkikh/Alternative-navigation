import time
from geoFun import dlinaDugiNachAzimut

def test_dlinaDugiNachAzimut_runtime():
    start = time.perf_counter()
    dist, az = dlinaDugiNachAzimut((0, 0), (0, 1))
    duration = time.perf_counter() - start
    assert 111000 < dist < 111300
    assert abs(az) < 1
    assert duration >= 0
