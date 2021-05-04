from contextlib import contextmanager

import pymysql
from retry import retry

from audience_toolkits import settings
from core.helpers.log_helper import get_logger

_logger = get_logger("DBOperator", verbose=True)

DEFAULT_MARIA_COUNT_QUERY = "SELECT count(*) as row_count FROM %s %s;"


@contextmanager
def get_mysql_connection(host: str, port: int, user: str, password: str, schema: str, connect_timeout=60,
                         cursor_class=pymysql.cursors.SSDictCursor):
    """
    取得mysql連線，建議使用 'with'
    :param host:
    :param port:
    :param user:
    :param password:
    :param schema:
    :param connect_timeout:
    :param cursor_class:
    :return:
    """
    conn = None
    try:
        conn = pymysql.connect(
            host=host, port=port, user=user,
            passwd=password, db=schema,
            cursorclass=cursor_class,
            connect_timeout=connect_timeout
        )
        # _logger.debug(f"{conn_info.host}:{conn_info.schema} connect ok!")
        yield conn
    finally:
        if conn is not None:
            # conn.close()
            pass


@retry(tries=settings.CONNECT_RETRIES, delay=3, backoff=1.5, logger=_logger)
def select_rows(conn: pymysql.Connection, sql_query: str, fetch_size=1000):
    c = conn.cursor()
    c.execute(sql_query)
    chunk_rows = c.fetchmany(size=fetch_size)
    while chunk_rows:
        yield chunk_rows
        chunk_rows = c.fetchmany(size=fetch_size)


@retry(tries=settings.CONNECT_RETRIES, delay=3, backoff=1.5, logger=_logger)
def get_row_count(conn: pymysql.Connection, schema, table, condition: str = None, row_count_col="row_count"):
    sql_query = DEFAULT_MARIA_COUNT_QUERY % (f"{schema}.{table}", f"{condition if condition is not None else ''}")
    cursor = conn.cursor()
    _logger.debug(sql_query)
    cursor.execute(sql_query)

    row = cursor.fetchone()
    cursor.close()
    return row[row_count_col]
