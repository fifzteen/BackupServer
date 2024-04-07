import datetime
import logging
logger = logging.getLogger(__name__)

class ProcessPool:
    """
    プロセスをプールするクラス

    Attributes
    ----------
    error : list
        エラープロセスプール
    finished : list
        終了プロセスプール
    running : list
        実行中プロセスプール
    pending : list
        実行持ちプロセスプール
    """
    ERROR = 'error'
    FINISHED = 'finished'
    RUNNING = 'running'
    PENDING = 'pending'

    def __init__(self):
        self.error = []
        self.finished = []
        self.running = []
        self.pending = []
        self.map = {self.ERROR: self.error,
                    self.FINISHED: self.finished,
                    self.RUNNING: self.running,
                    self.PENDING: self.pending}

    def is_in_keys(self, key):
        """
        キーは存在するか？

        Parameters
        ----------
        key : str
            検査するキー

        Returns
        -------
        bool
        """
        return key in self.map.keys()

    def register(self, proc, key):
        """
        プロセスを登録する

        Parameters
        ----------
        proc : process.Process
            プロセスインスタンス
        key : str
            登録先キー
        """
        # キー違反チェック
        if not self.is_in_keys(key):
            logger.error('given target key %s not exist', key)
            return

        # 登録
        self.map[key].append({'proc': proc, 'updated_at': datetime.datetime.now().isoformat()})

    def get_section(self, to_section_name):
        """
        プロセスのセクション辞書を取得する

        Parameters
        ----------
        to_section_name : function
            セクション作成関数

        Returns
        -------
        dict of {str: list of {name: str}}
        """
        procs_sections = {key: [{'name': to_section_name(v['proc']), 'updated_at': v['updated_at']} for v in value] if len(value) > 0 else [] for key, value in self.map.items()}
        return procs_sections

    def move_proc(self, proc, target):
        """
        プロセス辞書のキー間を移動させる

        Parameters
        ----------
        proc : Process
            対象のプロセス
        target : str
            移動先

        Returns
        -------
        int
            終了コード
        """
        # プロセスのある場所を探す
        for k, v in self.map.items():
            for i, item in enumerate(v):
                if proc == item['proc']:
                    key = k
                    index = i
                    break
            else:
                continue
            break
        else:
            logger.error('given process not exist in pool')
            return 1

        # targetのキー違反チェック
        if not self.is_in_keys(target):
            logger.error('given target key %s not exist', target)
            return 1

        # 処理
        self.map[key].pop(index)
        self.register(proc, target)

        return 0

    def clear_procs(self, targets):
        """
        プロセス辞書の特定キーをクリアする

        Paramters
        ---------
        targets : list of str
            クリアするキーのリスト
        """
        for target in targets:
            # targetのキー違反チェック
            if not self.is_in_keys(target):
                logger.warning('given target key %s not exist', target)
                continue

            self.map[target].clear()
