import pytest
import logging
logger = logging.getLogger(__name__)

from logutil import set_logger_format

@pytest.mark.parametrize('handlers, fmt', [
    (logging.getLogger().handlers, '[%(levelname)s] %(asctime)s : %(name)s(%(lineno)s) %(message)s'),
    (logger.handlers, '[%(levelname)s] %(asctime)s : %(name)s(%(lineno)s) %(message)s')
], ids=['root', 'this logger'])
def test_set_logger_format(handlers, fmt):
    set_logger_format(handlers, fmt)
    for handler in handlers:
        assert handler.formatter._fmt == fmt