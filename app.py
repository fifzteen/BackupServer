import time
from flask import Flask
app = Flask(__name__)

import os
from pathlib import PurePath
import logging
import logging.handlers
logger = logging.getLogger(__name__)

LOG_LEVEL = logging.INFO
LOG_FORMAT = '[%(levelname)s] %(asctime)s : %(name)s(%(lineno)s) %(message)s'
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logpath = PurePath(os.path.dirname(os.path.abspath(__file__)), 'log', 'backup_app.log')
handler = logging.handlers.TimedRotatingFileHandler(str(logpath), when='D', backupCount=7)
handler.setLevel(LOG_LEVEL)
handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
logging.getLogger().addHandler(handler)

from settings import Settings
from process import Process
from processpool import ProcessPool
import logutil

def generate_section(proc):
    """
    プロセスからセクション文字列を生成する

    Parameters
    ----------
    proc : process.Process
        プロセスインスタンス

    Returns
    -------
    str
        セクション文字列
    """
    return '_'.join([proc.cmd[proc.cmd.index('--user')+1], proc.cmd[proc.cmd.index('--target')+1]])

def get_status(pool):
    """
    バックアップ実行状況を取得する

    Parameters
    ----------
    pool : processpool.ProcessPool
        ProcessPoolインスタンス

    Returns
    -------
    message : str
        ステータスメッセージ
    """
    # セクションを取得
    procs_sections = pool.get_section(generate_section)

    # メッセージ作成
    message = 'error : ' + procs_sections[ProcessPool.ERROR] + '\n'+ \
              'finished : ' + procs_sections[ProcessPool.FINISHED] + '\n' + \
              'running : ' + procs_sections[ProcessPool.RUNNING] + '\n' + \
              'pending : ' + procs_sections[ProcessPool.PENDING] + '\n'

    # プロセス辞書をフラッシュ
    pool.clear_procs([ProcessPool.FINISHED])

    return message

def deco_exec_backup(func):
    def exec_backup_wrapper(*args, **kwargs):
        format_before = logging.getLogger().handlers[0].formatter._fmt
        try:
            logutil.set_logger_format(logging.getLogger().handlers, '%(message)s')
            res = func(*args, **kwargs)
        finally:
            logutil.set_logger_format(logging.getLogger().handlers, format_before)
        return res
    return exec_backup_wrapper

@deco_exec_backup
def exec_backup(cmd, pool):
    """
    バックアップを実行する

    Parameters
    ----------
    cmd : list
        実行するバックアップコマンド
    pool : processpool.ProcessPool
        プロセスプールインスタンス

    Returns
    -------
    int
        終了コード
    """
    # サブプロセス作成
    proc = Process(cmd=cmd, out_to_log=True)
    pool.register(proc, ProcessPool.PENDING)
    # 他のサブプロセスを待つ
    rcode = proc.wait_other_process()
    if rcode == 1:
        rcode = max([rcode, pool.move_proc(proc, ProcessPool.ERROR)])
        return rcode
    # 実行
    rcode = pool.move_proc(proc, ProcessPool.RUNNING)
    if rcode == 0:
        logger.info('')
        proc.execute(wait=True)
        target = ProcessPool.FINISHED if proc.returncode == 0 else ProcessPool.ERROR
        rcode = pool.move_proc(proc, target)
    return max([proc.returncode, rcode])

@app.route("/")
def index():
    return 'index page'

@app.route("/api/status", methods=["GET"])
def status():
    """
    ステータス取得
    """
    try:
        return get_status(ppool)
    except Exception as e:
        logger.warn('Exception raised. Return warning')
        return 'something occured. check pi3!\n%s' % e

@app.route("/api/clear_error", methods=["POST"])
def clear_error():
    """
    エラータスクをクリア
    """
    ppool.clear_procs([ProcessPool.ERROR])
    return 'cleared.\n'

@app.route("/api/<user>/<target>", methods=["POST"])
def backup(user, target):
    """
    バックアップ実行

    Parameters
    ----------
    user : str
        対象ユーザ
    target : str
        対象区分
    """
    exec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup.py')
    cmd = ['python3', exec_path, '--user', user, '--target', target]
    logger.info('execute backup (%s)', ' '.join(cmd))
    returncode = exec_backup(cmd, ppool)
    if returncode == 0:
        logger.info('Return success')
        return 'success!\n'
    else:
        logger.info('Return failed')
        return 'failed...\n'

if __name__ == '__main__':
    ppool = ProcessPool()
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)