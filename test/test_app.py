import pytest
from subprocess import Popen, PIPE, STDOUT
import os
from pathlib import Path

from app import *
from process import Process
from processpool import ProcessPool

@pytest.fixture(autouse=True, scope='module')
def clear_log():
    yield
    logpath = Path(os.path.dirname(os.path.abspath(__file__)), '..', 'backup_app.log').resolve()
    if os.path.exists(logpath):
        os.remove(logpath)

@pytest.fixture()
def pool():
    return ProcessPool()

@pytest.fixture()
def proc():
    return Process(['python3', 'backup.py', '--user', 'foo', '--target', 'bar'])

@pytest.mark.parametrize('cmd, expected', [
    (['python3', 'backup.py', '--user', 'foo', '--target', 'bar'], 'foo_bar'),
    (['sleep', '5'], ValueError)
], ids=['valid backup command', 'invalid backup command'])
def test_to_section_name(cmd, expected):
    proc = Process(cmd)
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            to_section_name(proc)
    else:
        assert to_section_name(proc) == expected

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
def context_get_status(request, pool, proc):
    sections = {ProcessPool.ERROR: [], ProcessPool.FINISHED: [], ProcessPool.RUNNING: [], ProcessPool.PENDING: []}
    if len(request.param) > 0:
        if 'e' in request.param:
            pool.map[ProcessPool.ERROR].append(proc)
            sections[ProcessPool.ERROR].append({'name': 'foo_bar'})
        if 'f' in request.param:
            pool.map[ProcessPool.FINISHED].append(proc)
            sections[ProcessPool.FINISHED].append({'name': 'foo_bar'})
        if 'r' in request.param:
            pool.map[ProcessPool.RUNNING].append(proc)
            sections[ProcessPool.RUNNING].append({'name': 'foo_bar'})
        if 'p' in request.param:
            pool.map[ProcessPool.PENDING].append(proc)
            sections[ProcessPool.PENDING].append({'name': 'foo_bar'})

    yield (pool, sections)

def test_get_status(context_get_status, monkeypatch):
    pool, sections = context_get_status
    monkeypatch.setattr(ProcessPool, 'get_section', lambda x,y: sections)
    assert get_status(pool) == sections

@pytest.mark.parametrize('cmd, result', [
    (['true'], 0),
    (['false'], 1)
], ids=['True - 0', 'False - 1'])
def test_exec_backup(cmd, result, pool):
    assert exec_backup(cmd, pool) == result