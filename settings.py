import os
import sys
import argparse
import configparser
import datetime
from pathlib import Path
import logging
import logging.handlers
logger = logging.getLogger(__name__)

class Settings:
    """
    設定を保持するクラス

    Attributes
    ----------
    _INIDIR : str, default /mnt/backup/
        config.iniのあるディレクトリ
    _INIPATH : str, default ./config.ini
        config.iniの相対パス
    CONFIG : dict
        configのパース結果
    USER : str
        引数で指定されたユーザ
    TARGET : str
        引数で指定されたターゲット
    SOURCE : str
        バックアップ元パス
    DEST : str
        バックアップ先パス
    CPDEST : str
        世代コピー先パス
    KEEP_COUNT : int, default 0
        世代コピーを作成する数
    DATE_CURRENT : str, default datetime.date.today().strftime('%Y%m%d')
        実行日付(YYYYmmdd)
    DATE_LAST : str
        前回実行日付(YYYYmmdd)
    LOG : str
        ログファイルのパス
    LOG_LEVEL : int, default logging.INFO
        ログのレベル
    LOG_FORMATTER : str, default [%(levelname)s] %(asctime)s : %(name)s(%(lineno)s) %(message)s
        ログのフォーマット
    """

    def __init__(self, args=sys.argv[1:]):
        # 初期化
        self._INIDIR = '/mnt/backup'
        self._INIPATH = './config.ini'
        self.CONFIG = None
        self.USER = ''
        self.TARGET = ''
        self.PASS_CP = False
        self.SECTION = ''
        self.SOURCE = ''
        self.DEST = ''
        self.CPDEST = ''
        self.KEEP_COUNT = 0
        self.DATE_CURRENT = datetime.date.today().strftime('%Y%m%d')
        self.DATE_LAST = ''
        self.LOG = ''
        self.LOG_LEVEL = logging.INFO
        self.LOG_FORMAT = '[%(levelname)s] %(asctime)s : %(name)s(%(lineno)s) %(message)s'

        # log設定
        logging.basicConfig(level=logging.INFO, format=self.LOG_FORMAT)

        # コマンド引数をパース
        options = self._parse_args(args)
        self._INIDIR = options._INIDIR
        self._INIPATH = options._INIPATH
        self.USER = options.USER
        self.TARGET = options.TARGET
        self.PASS_CP = options.PASS_CP
        self.SECTION = self.USER + '_' + self.TARGET

        # config.ini読み込み
        self.CONFIG = self._load_config()

        # config.iniの内容をインスタンス変数に入れる
        self._set_config_values_to_instance()

        # CPDESTの値をセット
        self.CPDEST = Settings.create_dirpath_with_date(self.DEST, self.DATE_LAST)

        # LOGの値をセット
        self.LOG = self._generate_logpath()

        # ファイルハンドラを追加
        filehandler = logging.FileHandler(self.LOG, mode='a', encoding='UTF-8')
        filehandler.setLevel(self.LOG_LEVEL)
        filehandler.setFormatter(logging.Formatter(fmt=self.LOG_FORMAT))
        logging.getLogger().addHandler(filehandler)

        # ログに内容を吐き出し
        logger.info(vars(self))

    @property
    def INIPATH(self):
        return str(Path(self._INIDIR, self._INIPATH).resolve())

    @staticmethod
    def create_dirpath_with_date(dirpath, date):
        """
        日付つきディレクトリパスを作成

        Parameters
        ----------
        dirpath : str
            ベースとなるディレクトリパス
        date : str
            日付(YYYYmmdd)

        Returns
        -------
        path : str
            ディレクトリパス
        """
        dirpath_wo_thrash = dirpath[:-1] if dirpath[-1] == '/' else dirpath
        basename = os.path.basename(dirpath_wo_thrash)
        result = os.path.join(os.path.dirname(dirpath_wo_thrash),
                              basename+'_'+date)
        result = result + '/'
        return result

    def _parse_args(self, args):
        """
        コマンド引数をインスタンス変数にパース

        Parameters
        ----------
        args : list or tuple
            パースする引数リスト

        Returns
        -------
        options : argparse.Namespace
            パースした結果
        """
        parser = argparse.ArgumentParser(description='Backup Server')
        parser.add_argument('--inidir', dest='_INIDIR', type=str, default=self._INIDIR)
        parser.add_argument('--inipath', dest='_INIPATH', type=str, default=self._INIPATH)
        parser.add_argument('--user', dest='USER', type=str, required=True)
        parser.add_argument('--target', dest='TARGET', type=str, required=True)
        parser.add_argument('--pass_cp', dest='PASS_CP', action='store_true')
        options = parser.parse_args(args)
        return options

    def _load_config(self):
        """
        config.iniを読み込む
        """
        config = configparser.ConfigParser()
        config.read(self.INIPATH, 'UTF-8')
        if len(config) == 0:
            logger.error('Failed to load config.ini. Maybe cannot find config.ini.')
            sys.exit(1)
        return config

    def _set_config_values_to_instance(self):
        """
        config.iniの内容をインスタンス変数に入れる
        """
        config_filtered = self.CONFIG[self.SECTION]
        self.SOURCE = config_filtered['source']
        self.DEST = config_filtered['dest']
        self.KEEP_COUNT = int(config_filtered['keep_count'])
        self.DATE_LAST = config_filtered['date_last']

    def _generate_logpath(self):
        """
        LOGパスを作成
        """
        log_basename = self.TARGET + '_' + self.DATE_CURRENT + '.log'
        logpath = str(Path(Path(self.DEST).parent, 'log', log_basename))
        return logpath

    def export_config(self):
        """
        configを更新してiniファイルにエクスポートする
        """
        # 実行日付を前回日付に格納
        self.CONFIG.set(self.SECTION, 'date_last', self.DATE_CURRENT)
        logging.info('Section %s, date_last is %s', self.SECTION, self.DATE_CURRENT)
        # config.iniにエクスポート
        try:
            self.CONFIG.write(open(self.INIPATH, 'w'))
        except Exception as e:
            logger.error('Could not write to config.ini: %s', e)
            sys.exit(1)