import logging
import os
import sys
import time
from logging import LogRecord
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from audience_toolkits.settings import LOG_FILE_DIRECTORY, LOG_BACKUP_COUNT, LOGGING_FORMAT, LOGGING_ERROR_FORMAT


class LogLevelFilter(logging.Filter):

    def __init__(self, low, high) -> None:
        self._low = low
        self._high = high
        super().__init__()

    def filter(self, record: LogRecord) -> int:
        if self._low <= record.levelno <= self._high:
            return True
        else:
            return False


def _get_general_file_handler(context, log_level, formatter) -> logging.Handler:
    Path(LOG_FILE_DIRECTORY).mkdir(exist_ok=True)
    log_dir = os.path.join(LOG_FILE_DIRECTORY, context)
    Path(log_dir).mkdir(exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        os.path.join(
            log_dir,
            time.strftime("%Y-%m-%d", time.localtime()) + ".log"
        ),
        when='MIDNIGHT',
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.addFilter(
        LogLevelFilter(log_level, log_level)
    )
    file_handler.setFormatter(formatter)
    return file_handler


def _get_error_file_handler(formatter) -> logging.Handler:
    Path(LOG_FILE_DIRECTORY).mkdir(exist_ok=True)
    log_dir = os.path.join(LOG_FILE_DIRECTORY, "Exceptions")
    Path(log_dir).mkdir(exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        os.path.join(
            log_dir,
            time.strftime("%Y-%m-%d", time.localtime()) + ".log"
        ),
        when='MIDNIGHT',
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel("WARNING")
    file_handler.setFormatter(formatter)
    return file_handler


def _get_console_handler(log_level, formatter) -> logging.Handler:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    return console_handler


def get_logger(
        context: str, verbose: bool = False,
        write_to_file: bool = True
):
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger(context)
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        LOGGING_FORMAT.format(
            _context=context
        )
    )
    formatter_err = logging.Formatter(
        LOGGING_ERROR_FORMAT.format(
            _context=context
        )
    )

    logger.addHandler(
        _get_console_handler(log_level, formatter)
    )
    logger.addHandler(
        _get_error_file_handler(formatter_err)
    )

    if write_to_file:
        logger.addHandler(
            _get_general_file_handler(
                context, log_level, formatter
            )
        )

    return logger
