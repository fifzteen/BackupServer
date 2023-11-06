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
    PENDING = 'penfing'

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
        self.map[key].append(proc)

    def get_section(self, func):
        """
        プロセスのセクション辞書を取得する

        Parameters
        ----------
        func : function
            セクション作成関数

        Returns
        -------
        dict of {str: str}
        """
        procs_sections = {key: [func(v) for v in value] if len(value) > 0 else [] for key, value in self.map.items()}
        procs_sections = {k: ','.join(v) if len(v) > 0 else '' for k, v in procs_sections.items()}
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
            if proc in v:
                current_key = k
                break
        else:
            logger.error('given process not exist in pool')
            return 1

        # targetのキー違反チェック
        if not self.is_in_keys(target):
            logger.error('given target key %s not exist', target)
            return 1

        # 処理
        self.map[current_key].remove(proc)
        self.map[target].append(proc)

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
