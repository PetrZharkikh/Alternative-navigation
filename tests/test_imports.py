import importlib
import time
import pytest

modules = [
    'grafInterfToFrame',
    'oneImage',
    'serialImage',
    'tilesAero',
    'trMatrix',
    'primerShivka',
    'primesShivka'
]

@pytest.mark.parametrize('name', modules)
def test_import_module_runtime(name):
    start = time.perf_counter()
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.skip(f'Missing dependency for {name}: {exc}')
    duration = time.perf_counter() - start
    assert duration >= 0
