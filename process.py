from subprocess import PIPE, STDOUT, Popen
import psutil
import time
import logging
logger = logging.getLogger(__name__)

import logutil

class Process:
    """
    プロセスに関するクラス

    Attributes
    ----------
    cmd : list
        実行するコマンド
    out_to_log : bool, default False
        実行出力をログに出すか？
    _proc : subprocess.Popen
        実行したプロセスのPopenオブジェクト
    _returncode : int, default -1
        実行したプロセスの終了コード
    """

    def __init__(self, cmd, out_to_log=False):
        self.cmd = cmd
        self.out_to_log = out_to_log
        self._proc = None
        self._returncode = -1

    @property
    def returncode(self):
        # 実行してなかったらそのまま返す
        if self._proc == None:
            return self._returncode
        # 要求されたのに終了してなかったら待つ
        if self._proc.returncode is None:
            self._returncode = self._proc.wait()
        return self._returncode

    @property
    def pid(self):
        return self._proc.pid

    def _print_stuout_to_logger(self):
        """
        コマンド実行の標準出力をログに出力する
        """
        format_before = logging.getLogger().handlers[0].formatter._fmt
        try:
            logutil.set_logger_format(logging.getLogger().handlers, '%(message)s')
            for line in self._proc.stdout:
                logger.info(line.strip())
        finally:
            logutil.set_logger_format(logging.getLogger().handlers, format_before)

    def _process_if(self, func, *args, **kwargs):
        """
        プロセスに関する条件判定
        """
        try:
            return func(*args, **kwargs)
        except psutil.NoSuchProcess:
            return False

    def get_other_process_pids(self):
        """
        実行時に動いている他のプロセスのPIDを取得する

        Returns
        -------
        pids : list
            プロセスIDのリスト
        """
        procs = []
        append = procs.append
        for proc in psutil.process_iter(attrs=['pid', 'name', 'status']):
            try:
                append(proc)
            except psutil.NoSuchProcess:
                pass
        procs_running = [proc for proc in procs
                         if self._process_if(lambda: proc.status() == 'running')]
        procs_samename = [proc for proc in procs_running
                          if self._process_if(lambda: proc.name() == self.cmd[0])]
        pids_other = [proc.pid for proc in procs_samename
                      if self._process_if(lambda: proc.cmdline()[:2] == self.cmd[:2])]
        return pids_other

    def wait_other_process(self, timeout=None):
        """
        実行時に動いている他の指定プロセスの終了を待つ

        Parameters
        ----------
        timeout : int, default 60
            1回のプロセス待ちをチェックする間隔(s)

        Returns
        -------
        returncode : int
            終了コード
        """
        other_procs = [psutil.Process(pid) for pid in self.get_other_process_pids()
                      if self._process_if(lambda: psutil.pid_exists(pid))]
        if len(other_procs) > 0:
            gone, alive = psutil.wait_procs(other_procs, timeout=timeout)
            if len(alive) > 0:
                logger.error('process wait failed. pid : %s',
                             ','.join([str(proc.pid) for proc in alive]))
                return 1
        return 0

    def execute(self, wait=False):
        """
        シェルコマンド実行

        Parameters
        ----------
        wait : bool, default False
            プロセスの終了を待つか？
        """
        joined_cmd = ' '.join(self.cmd)
        logger.info('execute command (%s)', ' '.join(self.cmd))
        proc = Popen(joined_cmd, shell=True, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        self._proc = proc
        # ログを出す
        if self.out_to_log:
            self._print_stuout_to_logger()
        # 終了を待つ
        if wait:
            self._returncode = self._proc.wait()