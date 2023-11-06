import os
import sys
import glob
import logging
logger = logging.getLogger(__name__)

from process import Process
from settings import Settings

def exec_with_startend_log(additional):
    # 実行時に開始終了ログを付与するラッパー
    def _exec_with_startend_log(func):
        def wrapper(*args, **kwargs):
            logger.info('Start - '+additional)
            res = func(*args, **kwargs)
            logger.info('End - '+additional)
            return res
        return wrapper
    return _exec_with_startend_log

def forceexit_when_error(func):
    # シェルコマンドが異常終了だったら強制的に終了するラッパー
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if res != 0:
            logger.error('Command failed. Force exit.')
            sys.exit(1)
        return res
    return wrapper

@forceexit_when_error
def exec_mount_all():
    """
    sudo mount -a 実行

    Returns
    -------
    endcode : int
        終了コード
    """
    cmd = ['sudo', 'mount', '-a']
    proc = Process(cmd=cmd)
    proc.execute(wait=True)
    return proc.returncode

@exec_with_startend_log('Copy recent directory')
@forceexit_when_error
def exec_cp(setting):
    """
    cp実行

    Parameters
    ----------
    setting : Settings
        設定

    Returns
    -------
    endcode : int
        終了コード
    """
    # PASS_CPならコピーはしない
    if setting.PASS_CP:
        logger.info('passing cp is given. cp is not to execute.')
        return 0
    # KEEP_COUNTが0なら世代コピーを作らない
    if setting.KEEP_COUNT == 0:
        logger.info('keep count is 0. cp is not to execute.')
        return 0

    cmd = ['cp', '-avR', setting.DEST, setting.CPDEST]
    proc = Process(cmd=cmd, out_to_log=True)
    proc.execute(wait=True)
    return proc.returncode

@exec_with_startend_log('Backup by rsync')
@forceexit_when_error
def exec_rsync(setting):
    """
    rsync実行

    Parameters
    ----------
    setting : Settings
        設定

    Returns
    -------
    endcode : int
        終了コード
    """
    cmd = ['rsync', '-avE', '--delete-after', '--copy-unsafe-links', setting.SOURCE, setting.DEST]
    proc = Process(cmd=cmd, out_to_log=True)
    proc.execute(wait=True)
    return proc.returncode

def get_dates_to_remove(setting, is_log=False):
    """
    削除する実行日付を取得する

    Parameters
    ----------
    setting : Settings
        設定
    is_log : bool, default False
        ログファイルの検索かどうか

    Returns
    -------
    dates : list
        削除対象の日付リスト(YYYYmmdd)
    """
    # 種類取得
    backup_type = setting.TARGET
    # 対象ディレクトリ取得
    if is_log:
        dest_dir = os.path.dirname(setting.DEST[:-1]) + '/log/' + backup_type
    else:
        dest_dir = setting.DEST[:-1]
    dirs_sametype = glob.glob(dest_dir+'_*')
    # 日付つきのみに限定
    dirs_sametype = [os.path.splitext(dirname)[0] for dirname in dirs_sametype if os.path.splitext(dirname)[0][-8:].isdecimal()]
    # 日付抽出
    dates_sametype = [[idx,int(dirname[-8:])] for idx, dirname in enumerate(dirs_sametype)]
    # 日付部分でソート
    dates_sametype = sorted(dates_sametype, key=lambda x: x[1])
    # KEEP_COUNTで削る
    if len(dates_sametype) <= setting.KEEP_COUNT+int(is_log):
        return []
    else:
        remove_targets = dates_sametype[:len(dates_sametype)-(setting.KEEP_COUNT+int(is_log))]
        return [str(rt[1]) for rt in remove_targets]


@exec_with_startend_log('Remove past directory')
@forceexit_when_error
def exec_rm_dir(dates, setting):
    """
    rm実行(directory)

    Parameters
    ----------
    dates : list
        削除する日付リスト(YYYYmmdd)
    setting : Settings
        設定

    Returns
    -------
    endcode : int
        終了コード
    """
    # 日付を削除対象に変換
    rmdests = [Settings.create_dirpath_with_date(setting.DEST, date) for date in dates]
    # 削除
    if len(rmdests) == 0:
        logger.info('No directory is to remove.')
        return 0
    for rmdest in rmdests:
        cmd = ['rm', '-rfv', rmdest]
        proc = Process(cmd=cmd, out_to_log=True)
        proc.execute(wait=True)
        return proc.returncode

@exec_with_startend_log('Remove past log')
@forceexit_when_error
def exec_rm_log(dates, setting):
    """
    rm実行(log)

    Parameters
    ----------
    dates : list
        削除する日付リスト(YYYYmmdd)
    setting : Settings
        設定

    Returns
    -------
    endcode : int
        終了コード
    """
    # 日付を削除対象に変換
    rmdests = [setting.LOG[:setting.LOG.rfind('_')]+'_'+date+'.log' for date in dates]
    # 削除
    if len(rmdests) == 0:
        logger.info('No log is to remove.')
        return 0
    for rmdest in rmdests:
        cmd = ['rm', '-rfv', rmdest]
        proc = Process(cmd=cmd, out_to_log=True)
        proc.execute(wait=True)
        return proc.returncode

def main(setting):
    """
    エントリポイント

    Parameters
    ----------
    setting : Settings
        設定

    Returns
    -------
    returncode : int
        終了コード
    """
    # 予めマウント
    exec_mount_all()

    # 世代バックアップの作成
    exec_cp(setting)

    # rsyncによるバックアップ
    exec_rsync(setting)

    # 不要世代の洗い出し
    rm_dates = get_dates_to_remove(setting)
    # 不要世代の削除
    exec_rm_dir(rm_dates, setting)
    # 不要世代の洗い出し
    rm_log_dates = get_dates_to_remove(setting, is_log=True)
    # 不要世代ログの削除
    exec_rm_log(rm_log_dates, setting)

    # config.iniのエクスポート
    setting.export_config()

    return 0


if __name__ == "__main__":
    setting = Settings()
    main(setting)