import pytest
import os
import shutil
import time
import datetime
import copy
import logging
logger = logging.getLogger(__name__)

from backup import get_dates_to_remove, exec_cp, exec_rsync, exec_rm_dir, exec_rm_log
from settings import Settings

# テスト用設定
PRJDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = 'srcdir'
TESTDIR = 'testdir'
TESTDATES = ['20181220', '20190101', '20190110', '20190201']
USERNAME = 'foobar'
TYPENAME = 'hogehoge'

# 初期設定
@pytest.fixture(autouse=True, scope='module')
def fixture_testdir(tmpdir_factory):
    # ソースディレクトリ作成
    # srcdir = tmpdir_factory.mktemp(SRCDIR)
    os.mkdir(os.path.join(PRJDIR, SRCDIR))
    # 中身作成
    f = open(os.path.join(PRJDIR, SRCDIR, TYPENAME+'.txt'), 'w')
    # f = open(os.path.join(srcdir, TYPENAME+'.txt'), 'w')
    f.write('this is src')
    f.close()

    # テストディレクトリ作成
    # testdir = tmpdir_factory.mktemp(TESTDIR)
    os.mkdir(os.path.join(PRJDIR, TESTDIR))
    # 個別ディレクトリ作成
    dirnames = [''] + ['_'+date for date in TESTDATES[:-1]]
    for dirname in dirnames:
        dirpath = os.path.join(PRJDIR, TESTDIR, TYPENAME+dirname)
        # dirpath = os.path.join(testdir, TYPENAME+dirname)
        os.mkdir(dirpath)
        # 中身作成
        f = open(os.path.join(dirpath, 'hoge'+dirname+'.txt'), 'w')
        f.write(dirname)
        f.close()
        # 日付操作
        if dirname == '':
            cudate = time.strptime(TESTDATES[-1], '%Y%m%d')
        else:
            cudate = time.strptime(dirname[1:], '%Y%m%d')
        times = (time.mktime(cudate), time.mktime(cudate))
        os.utime(dirpath, times)

    # ログ作成
    os.mkdir(os.path.join(PRJDIR, TESTDIR, 'log'))
    # os.mkdir(os.path.join(testdir, 'log'))
    for date in TESTDATES:
        f = open(os.path.join(PRJDIR, TESTDIR, 'log', TYPENAME+'_'+date+'.log'), 'w')
        # f = open(os.path.join(testdir, 'log', TYPENAME+'_'+date+'.log'), 'w')
        f.write(date)
        f.close()

    # テスト実行
    yield

    # 掃除
    shutil.rmtree(os.path.join(PRJDIR, SRCDIR))
    shutil.rmtree(os.path.join(PRJDIR, TESTDIR))

@pytest.fixture(scope='module')
def stub_setting():
    setting = Settings(args=('--user', USERNAME,
                             '--target', TYPENAME,
                             '--inidir', PRJDIR,
                             '--inipath', '../config.example.ini'))
    return setting

# remove判定のtest
@pytest.mark.parametrize('keep_count, is_log, rmdates', [
    (1, False, ['20181220', '20190101']),
    (3, False, []),
    (1, True, ['20181220', '20190101', '20190110']),
    (3, True, ['20181220'])
])
def test_get_dates_to_remove(keep_count, is_log, rmdates, stub_setting):
    setting = copy.deepcopy(stub_setting)
    setting.KEEP_COUNT = keep_count
    assert get_dates_to_remove(setting, is_log) == rmdates

# cpのtest
def test_exec_cp(stub_setting):
    assert exec_cp(stub_setting) ==  0

# rsyncのtest
def test_exec_rsync(stub_setting):
    assert exec_rsync(stub_setting) == 0

# rm(dir)のtest
@pytest.mark.parametrize('keep_count', [1, 3])
def test_exec_rm_dir(keep_count, stub_setting):
    setting = copy.deepcopy(stub_setting)
    setting.KEEP_COUNT = keep_count
    assert exec_rm_dir(get_dates_to_remove(setting), setting) == 0

# rm(log)のtest
@pytest.mark.parametrize('keep_count', [1, 3])
def test_exec_rm_log(keep_count, stub_setting):
    setting = copy.deepcopy(stub_setting)
    setting.KEEP_COUNT = keep_count
    assert exec_rm_log(get_dates_to_remove(setting), setting) == 0