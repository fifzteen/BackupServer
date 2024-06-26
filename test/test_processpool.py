import pytest
import datetime

from process import Process
from processpool import ProcessPool

@pytest.fixture()
def pool():
    return ProcessPool()

@pytest.fixture()
def sleep_proc():
    return Process(['sleep', '5'])

@pytest.mark.parametrize('key, expected', [
    (ProcessPool.ERROR, True),
    ('foobar', False)
], ids=['exist', 'not exist'])
def test_is_in_keys(key, expected, pool):
    assert pool.is_in_keys(key) == expected

@pytest.mark.parametrize('key, testkey, expected', [
    (ProcessPool.ERROR, ProcessPool.ERROR, True),
    ('foobar', ProcessPool.ERROR, False)
], ids=['exist', 'not exist'])
def test_register(key, testkey, expected, pool, sleep_proc):
    pool.register(sleep_proc, key)
    assert (sleep_proc in [item['proc'] for item in pool.map[testkey]]) == expected

def to_section_name_stub(proc):
    return proc.cmd[0]

@pytest.fixture(params=[[], ['p'], ['r'], ['f'], ['e'],
                        ['p', 'r'], ['p', 'f'], ['p', 'e'],
                        ['r', 'f'], ['r', 'e'], ['f', 'e'],
                        ['p', 'r', 'f'], ['p', 'r', 'e'], ['p', 'f', 'e'],
                        ['r', 'f', 'e'], ['p', 'r', 'f', 'e']],
                ids=['init', 'pending', 'running', 'finished', 'error',
                     'pending_running', 'pending_finished', 'pending_error',
                     'running_finished', 'running_error', 'finished_error',
                     'pending_running_finished', 'pending_running_error', 'pending_finished_error',
                     'running_finished_error', 'all'])
def context_get_section(request, pool, sleep_proc):
    expected = {ProcessPool.ERROR: [], ProcessPool.FINISHED: [], ProcessPool.RUNNING: [], ProcessPool.PENDING: []}

    if len(request.param) > 0:
        now = datetime.datetime.now().isoformat()
        if 'e' in request.param:
            pool.map[ProcessPool.ERROR].append({'proc':sleep_proc, 'updated_at': now})
            expected[ProcessPool.ERROR].append({'name': 'sleep', 'updated_at': now})
        if 'f' in request.param:
            pool.map[ProcessPool.FINISHED].append({'proc':sleep_proc, 'updated_at': now})
            expected[ProcessPool.FINISHED].append({'name': 'sleep', 'updated_at': now})
        if 'r' in request.param:
            for _ in range(2):
                pool.map[ProcessPool.RUNNING].append({'proc':sleep_proc, 'updated_at': now})
                expected[ProcessPool.RUNNING].append({'name': 'sleep', 'updated_at': now})
        if 'p' in request.param:
            pool.map[ProcessPool.PENDING].append({'proc':sleep_proc, 'updated_at': now})
            expected[ProcessPool.PENDING].append({'name': 'sleep', 'updated_at': now})

    yield pool, expected

def test_get_section(context_get_section):
    pool, expected = context_get_section
    assert pool.get_section(to_section_name_stub) == expected

@pytest.fixture(params=[0, 1, 2], ids=['valid', 'invalid key', 'value not exists'])
def context_move_proc(request, pool, sleep_proc):
    now = datetime.datetime.now().isoformat()
    if request.param == 0:
        # 正常
        pool.map[ProcessPool.PENDING].append({'proc': sleep_proc, 'updated_at': now})
        return pool, sleep_proc, ProcessPool.PENDING, ProcessPool.RUNNING, 0
    elif request.param == 1:
        # キー違反
        pool.map[ProcessPool.PENDING].append({'proc': sleep_proc, 'updated_at': now})
        return pool, sleep_proc, ProcessPool.PENDING, 'foobar', 1
    else:
        # 値がない
        return pool, sleep_proc, ProcessPool.PENDING, ProcessPool.RUNNING, 1

def test_move_proc(context_move_proc):
    pool, proc, current, target, expected = context_move_proc
    assert pool.move_proc(proc, target) == expected
    if expected == 0:
        assert proc in [item['proc'] for item in pool.map[target]]
        assert proc not in [item['proc'] for item in pool.map[current]]

@pytest.fixture(params=[(ProcessPool.FINISHED,), (ProcessPool.ERROR, ProcessPool.RUNNING)],
                ids=['single target', 'multi target'])
def context_clear_procs(request, pool):
    for key in request.param:
        pool.map[key] = [1,2,3]

    yield pool, request.param

def test_clear_procs(context_clear_procs):
    pool, keys = context_clear_procs
    pool.clear_procs(keys)
    for key in keys:
        assert len(pool.map[key]) == 0
