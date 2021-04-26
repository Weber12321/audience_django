from dataclasses import dataclass, astuple, field
from datetime import datetime
from enum import Enum
from typing import Optional

from core.helpers.log_helper import get_logger

_logger = get_logger("DBOperator", verbose=True)

DEFAULT_SELECT_QUERY: str = "SELECT id, s_area_id, author, title, content, post_time FROM {} {};"
DEFAULT_SELECT_ID_QUERY: str = "SELECT id FROM {} {};"
DEFAULT_SQLITE_COUNT_QUERY: str = "SELECT count(*) as rows FROM {} {};"
DEFAULT_EXPLAIN_COUNT: str = "EXPLAIN SELECT count(*) FROM {} {};"
ID_CONDITION: str = " AND id > {} "


class Features(Enum):
    """
    可用特徵，會使用value去操作'getattr(example, feature.value)'
    """
    S_AREA_ID = 's_area_id'
    AUTHOR = 'author'
    TITLE = 'title'
    CONTENT = 'content'
    POST_TIME = 'post_time'


@dataclass
class InputExample:
    id_: Optional[str]
    s_area_id: Optional[str]
    author: Optional[str]
    title: Optional[str]
    content: Optional[str]
    post_time: Optional[datetime]
    label: Optional[str] = field(default=None)

    def __iter__(self):
        return iter(astuple(self))

    def to_prob_model_dict(self):
        return {
            "_id": self.id_,
            "label": self.label,
            "content": self.content
        }


def _fix_null_str(x):
    if x is None or x == "(Null title)" or x == "(Null content)":
        return ""
    else:
        return x

# def _find_stop_position(txt: str, pos: int) -> Optional[tuple]:
#     """ Return a stop's (beginning index, ending index) after the starting position (pos) in the text. """
#     assert pos is not None
#     pat = re.compile(f"[{hanzi.punctuation}{string.punctuation}\\s]")
#     result = pat.search(txt, pos=pos)
#     return result.span() if result else None
#
#
# def _shrink_long_content(content: str) -> str:
#     punctuation_idx = _find_stop_position(
#         content, StaticConfigs.content_setting.max_doc_length
#     )
#     if punctuation_idx is None:
#         end_point = StaticConfigs.content_setting.max_doc_length
#     else:
#         end_point = punctuation_idx[0]
#     return content[:end_point]


# def get_input_entity_from_row(row) -> InputExample:
#     if type(row) == tuple or type(row) == list:
#         doc_id = row[0]
#         s_area_id = row[1]
#         author = row[2] if (row[2] is not None or str(row[2]).strip() != "") else "UNK"
#         title = _fix_null_str(row[3])
#         content = _fix_null_str(row[4])
#         content = _shrink_long_content(content)
#         post_time = row[5]
#     else:
#         doc_id = row["id"]
#         s_area_id = row.get("s_area_id", None)
#         author = "UNK"
#         if row.get("author", None) is not None or row.get("author", "").strip() != "":
#             author = row.get("author")
#         title = _fix_null_str(row.get("title", None))
#         content = _fix_null_str(row.get("content", None))
#         content = _shrink_long_content(content)
#         post_time = row.get("post_time", None)
#     result = InputExample(
#         id_=doc_id, s_area_id=s_area_id, author=author, title=title, content=content, post_time=post_time
#     )
#     return result
#
#
# def get_input_entity(conn_info: ConnInfo, sql_query: str = None, condition: str = None) -> Optional[InputExample]:
#     if sql_query is None:
#         sql_query = DEFAULT_SELECT_QUERY.format(f"{conn_info.table}",
#                                                 f"{condition if condition is not None else ''}")
#     result: Optional[InputExample] = select_example(conn_info, sql_query)
#     return get_input_entity_from_row(result)
#
#
# @retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
# def get_input_entities(conn_info: ConnInfo, sql_query: str = None, condition: str = None,
#                        finish_count: int = None, batch: int = None) -> Optional[InputExample]:
#     if sql_query is None:
#         sql_query = DEFAULT_SELECT_QUERY.format(f"{conn_info.table}",
#                                                 f"{condition if condition is not None else ''}")
#     elif finish_count is not None and batch is not None:
#         sql_query = DEFAULT_SELECT_ID_QUERY.format(f"{conn_info.table}",
#                                                    f"{condition if condition is not None else ''} LIMIT {batch} "
#                                                    f"OFFSET {finish_count - batch}")
#     with get_mysql_connection(conn_info) as conn:
#         cursor = conn.cursor()
#         _logger.debug(sql_query)
#         cursor.execute(sql_query)
#
#         row = cursor.fetchone()
#         while row is not None:
#             yield get_input_entity_from_row(row)
#             row = cursor.fetchone()
#         cursor.close()
#
#
# @retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
# def get_input_entities_row_count(conn_info: ConnInfo, condition: str = None):
#     sql_query = DEFAULT_EXPLAIN_COUNT.format(f"{conn_info.table}",
#                                              f"{condition if condition is not None else ''}")
#     return get_row_count(conn_info, sql_query=sql_query, condition=condition,
#                          row_count_col="rows" if conn_info.db_type == DBType.MARIADB else 0)
#
#
# @retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
# def get_input_entities_batch(conn_info: ConnInfo,
#                              sql_query: str = None,
#                              condition: str = None,
#                              batch=1000,
#                              fetch_limit_count=None,
#                              finish_count: int = 0) -> Iterable[InputExample]:
#     sql_query: str = DEFAULT_SELECT_QUERY if sql_query is None else sql_query
#
#     total_row_idx = get_input_entities_row_count(conn_info=conn_info, condition=condition) \
#         if (fetch_limit_count == -1 or fetch_limit_count is None) \
#         else fetch_limit_count
#
#     tmp_rows = list()
#     if finish_count:
#         tmp_rows = get_input_entities(conn_info=conn_info, sql_query=sql_query, condition=condition,
#                                       finish_count=finish_count, batch=batch)
#
#     for current_row_idx in range(finish_count, total_row_idx, batch):
#         last_id = f"'{list(tmp_rows)[-1].id_}'" if tmp_rows else 0
#         _limit = batch if (current_row_idx + batch) <= total_row_idx else (total_row_idx - current_row_idx)
#         _logger.debug(f"LIMIT : {_limit}, LAST_ID : {last_id}")
#
#         _condition = condition + ID_CONDITION.format(last_id)
#         query = sql_query.format(f"{conn_info.table}",
#                                  f"{_condition if _condition is not None else ''} LIMIT {_limit}")
#         tmp_rows = list()
#         with get_mysql_connection(conn_info) as conn:
#             cursor = conn.cursor()
#             _logger.debug(query)
#             cursor.execute(query)
#
#             row = cursor.fetchone()
#             while row is not None:
#                 tmp_rows.append(get_input_entity_from_row(row))
#                 row = cursor.fetchone()
#             cursor.close()
#         yield tmp_rows
#
#
# def init_input_example_schema(conn_info: ConnInfo):
#     query = f'''CREATE TABLE IF NOT EXISTS {conn_info.table}
#                 (
#                     id    CHAR(32) PRIMARY KEY,
#                     s_area_id    CHAR(16),
#                     author    CHAR(64),
#                     title   TEXT,
#                     content   TEXT,
#                     post_time  DATETIME
#                 ) {"DEFAULT CHARSET=utf8mb4" if DBType(conn_info.db_type) != DBType.SQLITE else ""};
#             '''
#     init_schema(conn_info=conn_info, sql_query=query)
#
#
# def insert_input_example(conn_info: ConnInfo, input_example: InputExample):
#     if DBType(conn_info.db_type) == DBType.SQLITE:
#         query = f'''INSERT INTO {conn_info.table}
#                     (`id`, `s_area_id`, `author`, `title`, `content`, `post_time`)
#                     VALUES (?,?,?,?,?,?);'''
#     elif DBType(conn_info.db_type) == DBType.MARIADB:
#         query = f'''INSERT INTO {conn_info.table}
#                     (`id`, `s_area_id`, `author`, `title`, `content`, `post_time`)
#                     VALUES (%s,%s,%s,%s,%s,%s);'''
#     else:
#         raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")
#     insert_example(conn_info=conn_info, sql_query=query, example=[col for col in input_example])
#
#
# def load_examples_from_file(file_path: str, batch_size=None):
#     if not file_path.startswith("/"):
#         file_path = os.path.join(BASE_DIR, file_path)
#     if batch_size is not None:
#         df = pandas.read_csv(file_path, sep='\t', header=0,
#                              names=["id", "s_area_id", "name", "title", "content", "post_time"], chunksize=batch_size)
#     else:
#         df = pandas.read_csv(file_path, sep='\t', header=0,
#                              names=["id", "s_area_id", "name", "title", "content", "post_time"], chunksize=2000)
#
#     examples = list()
#     for chunk in df:
#         for idx, row in chunk.iterrows():
#             example = InputExample(
#                 id_=row["id"],
#                 s_area_id=str(row["s_area_id"]),
#                 author=str(row["name"]),
#                 title=str(row["title"]),
#                 content=str(row["content"]),
#                 post_time=row["post_time"],
#                 label=None)
#             if batch_size is None:
#                 yield example
#             else:
#                 examples.append(example)
#                 if len(examples) >= batch_size:
#                     yield examples.copy()
#                     examples.clear()
#     if batch_size is not None:
#         yield examples.copy()
#
#
# def load_examples_from_dir(dir_path: str, batch_size=None):
#     examples = []
#     if not dir_path.startswith("/"):
#         dir_path = os.path.join(BASE_DIR, dir_path)
#
#     for _file in glob.glob(os.path.join(dir_path, "*.csv")):
#         for rs in load_examples_from_file(_file, batch_size):
#             if batch_size is None:
#                 yield rs
#             else:
#                 for example in rs:
#                     examples.append(example)
#                     if len(examples) >= batch_size:
#                         yield examples.copy()
#                         examples.clear()
#     if batch_size is not None:
#         yield examples.copy()
