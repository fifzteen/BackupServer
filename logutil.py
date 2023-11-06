import logging
import logging.handlers
logger = logging.getLogger(__name__)

def set_logger_format(handlers, fmt):
    """
    ロギングハンドラのフォーマットを変更する

    Parameters
    ----------
    handlers : array-like of logging.handler
        対象となるハンドラ
    fmt : str
        変更後フォーマット
    """
    for handler in handlers:
        handler.setFormatter(logging.Formatter(fmt=fmt))
