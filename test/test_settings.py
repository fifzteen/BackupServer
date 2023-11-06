import pytest
import os
import shutil
import configparser
import datetime
from pathlib import Path

from settings import Settings

# テスト用設定
PRJDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = 'srcdir'
TESTDIR = 'testdir'
USERNAME = 'foobar'
TYPENAME = 'hogehoge'
CONFIG_PATH = '../config.example.ini'
CONFIG_EXAMPLE_PATH = '../config.example2.ini'

@pytest.mark.parametrize('dirpath, date, expected', [
    ('/home/pi3/foo/bar/', '20180903', '/home/pi3/foo/bar_20180903/'),
    ('/home/pi3/foo/bar', '20180903', '/home/pi3/foo/bar_20180903/')
], ids=['thrash added', 'thrash not added'])
def test_create_dirpath_with_date(dirpath, date, expected):
    assert Settings.create_dirpath_with_date(dirpath, date) == expected

@pytest.fixture()
def fixture_testconfig():
    # 現在のconfig.iniを退避
    shutil.copy2(str(Path(PRJDIR, CONFIG_PATH).resolve()),
                 str(Path(PRJDIR, CONFIG_EXAMPLE_PATH).resolve()))

    # ソースディレクトリ作成
    os.mkdir(os.path.join(PRJDIR, SRCDIR))
    # テストディレクトリ作成
    os.mkdir(os.path.join(PRJDIR, TESTDIR))
    # ログ作成
    os.mkdir(os.path.join(PRJDIR, TESTDIR, 'log'))
    f = open(os.path.join(PRJDIR,
                          TESTDIR,
                          'log',
                          TYPENAME + '_' + datetime.date.today().strftime('%Y%m%d') + '.log'),
                          'w')
    f.close()

    # テスト実行
    yield

    # 掃除
    shutil.rmtree(os.path.join(PRJDIR, SRCDIR))
    shutil.rmtree(os.path.join(PRJDIR, TESTDIR))
    # config戻し
    shutil.copy2(str(Path(PRJDIR, CONFIG_EXAMPLE_PATH).resolve()),
                 str(Path(PRJDIR, CONFIG_PATH).resolve()))
    # config_example.ini削除
    os.remove(str(Path(PRJDIR, CONFIG_EXAMPLE_PATH).resolve()))

@pytest.fixture()
def cmd_args():
    return ('--inidir', PRJDIR,
            '--inipath', CONFIG_PATH,
            '--user', USERNAME,
            '--target', TYPENAME)

def test_export_config(cmd_args, fixture_testconfig):
    setting = Settings(args=cmd_args)
    # setting._INIDIR = PRJDIR
    setting.export_config()

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, 'UTF-8')
    assert config[USERNAME+'_'+TYPENAME]['date_last'] == '20180903'
