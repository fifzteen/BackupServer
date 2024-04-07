import pytest
import logging
import psutil
from subprocess import Popen, STDOUT, PIPE

from process import Process

# ログ設定
logger = logging.getLogger(__name__)
LOG_FORMATTER = '[%(levelname)s] %(asctime)s : %(name)s %(lineno)s(%(funcName)s) %(message)s'
LOG_FORMATTER_SH = '%(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMATTER)

@pytest.fixture()
def proc():
    return Process(cmd=['sleep', '5'])

@pytest.fixture(params=[True, False], ids=['wait', 'not wait'])
def context(request):
    if request.param:
        return (request.getfixturevalue('proc'), True)
    else:
        return (request.getfixturevalue('proc'), False)

def test_execute(context):
    proc, wait = context
    proc.execute(wait=wait)
    assert proc.returncode == 0

@pytest.fixture(params=[0, 5], ids=['no timeout', 'set timeout'])
def context_other_procs(request):
    cmd = request.getfixturevalue('proc').cmd
    if request.param == 0:
        return (request.getfixturevalue('proc'), [cmd, cmd], None)
    else:
        return (request.getfixturevalue('proc'), [cmd, cmd], 3)
def test_wait_other_process(context_other_procs):
    proc, other_cmds, timeout = context_other_procs
    for ocmd in other_cmds:
        Popen(ocmd, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
    rcode = proc.wait_other_process(timeout)
    proc.wait_other_process()
    if timeout is None:
        assert rcode == 0
    else:
        assert rcode == 1

@pytest.fixture(params=[0, 1, 2], ids=['no other proc', 'one other proc', 'some other proc'])
def context_pids(request):
    if request.param == 0:
        return (request.getfixturevalue('proc'), [])
    else:
        cmd = request.getfixturevalue('proc').cmd
        return (request.getfixturevalue('proc'), [cmd for _ in range(request.param)])

@pytest.mark.parametrize('func, expected', [
    (lambda: True, True),
    (lambda: False, False),
    (lambda: (_ for _ in ()).throw(psutil.NoSuchProcess(0)), False)
], ids=['True', 'False', 'Exception'])
def test__process_if(proc, func, expected):
    assert proc._process_if(func) == expected

def test_get_other_process_pids(context_pids):
    proc, other_cmds = context_pids
    if len(other_cmds) == 0:
        pids = proc.get_other_process_pids()
        assert pids == []
    else:
        other_procs = [Popen(ocmd, stdout=PIPE, stderr=STDOUT, universal_newlines=True) for ocmd in other_cmds]
        pids = proc.get_other_process_pids()

        for oproc in other_procs:
            oproc.wait()

        assert pids == [oproc.pid for oproc in other_procs]

if __name__ == '__main__':
    test_wait_other_process(Process(cmd=['sleep', '5']))