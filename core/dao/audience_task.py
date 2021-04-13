import datetime

from dataclasses import dataclass, field
from typing import List, Optional, Dict

from audience_toolkits.settings import FETCH_COUNT
from core.dao.conn_info import ConnInfo
from core.helpers.db_helper import init_schema, insert_example, update_example, select_examples, delete_example, \
    select_example
from core.helpers.enums_helper import DBType, Errors, TaskStatus

DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class AudienceTask(object):
    _id: Optional[int] = field(default=None)
    name: str = field(default=f"task")
    description: str = field(default=f"")
    source_list: Optional[List] = field(default=None)
    model_list: Optional[List] = field(default=None)
    start_post_time: str = field(default=f"{str(datetime.date.today())} 00:00:00")
    end_post_time: str = field(default=f"{datetime.datetime.now().strftime(DATE_FORMAT)}")
    fetch_count: int = field(default=FETCH_COUNT)
    minContentLength: int = field(default=1)
    maxContentLength: int = field(default=2000)
    output_db_name: str = field(default="audience_sample")
    output_table_name: str = field(default="author_result")
    black_list: List = field(default_factory=list)
    white_list: List = field(default_factory=list)
    status: str = field(default=TaskStatus.WAIT.value)
    progress_db_name: List = field(default_factory=list)
    progress_status: str = field(default="0/0")
    time: str = field(default=datetime.datetime.now().strftime(DATE_FORMAT))

    def to_api_result(self):
        return {
            "id": self._id,
            "name": self.name,
            "description": self.description,
            "source_list": self.source_list,
            "model_list": self.model_list,
            "start_post_time": self.start_post_time,
            "end_post_time": self.end_post_time,
            "limit_count": self.fetch_count,
            "minContentLength": self.minContentLength,
            "maxContentLength": self.maxContentLength,
            "black_list": self.black_list,
            "white_list": self.white_list,
            "status": self.status,
            "progress_db_name": self.progress_db_name,
            "progress_status": self.progress_status,
            "time": self.time
        }

    def to_database_fields(self):
        return [
            ("id", self._id),
            ("name", self.name),
            ("description", self.description),
            ("source_list", convert_to_str(self.source_list)),
            ("model_list", convert_to_str(self.model_list)),
            ("start_post_time", self.start_post_time),
            ("end_post_time", self.end_post_time),
            ("limit_count", self.fetch_count),
            ("minContentLength", self.minContentLength),
            ("maxContentLength", self.maxContentLength),
            ("black_list", convert_to_str(self.black_list)),
            ("white_list", convert_to_str(self.white_list)),
            ("status", self.status),
            ("progress_db_name", convert_to_str(self.progress_db_name)),
            ("progress_status", self.progress_status),
            ("time", self.time)
        ]


def get_audience_task_entity_from_row(row) -> AudienceTask:
    i = 0
    if type(row) == tuple or type(row) == list:
        _id = row[++i]
        name = row[++i]
        description = row[++i]
        _source_list = row[++i]
        _model_list = row[++i]
        start_post_time = row[++i]
        end_post_time = row[++i]
        limit_count = row[++i]
        minContentLength = row[++i]
        maxContentLength = row[++i]
        output_db_name = row[++i]
        output_table_name = row[++i]
        _black_list = row[++i]
        _white_list = row[++i]
        status = row[++i]
        _progress_db_name = row[++i]
        progress_status = row[++i]
        time = row[++i]
        # author = AudienceTask(id_=_id, start_post_time=start_post_time, end_post_time=end_post_time,
        #                       limit_count=limit_count, minContentLength=minContentLength,
        #                       maxContentLength=maxContentLength, input_db_info=input_db_info,
        #                       input_table_name=input_table_name, output_db_info=output_db_info,
        #                       output_db_name=output_db_name, output_table_name=output_table_name,
        #                       status=status, progress_status=progress_status,
        #                       time=time)
        author = AudienceTask(*row)
        # author = AudienceTask(_id=_id, name=name, description=description, start_post_time=start_post_time, end_post_time=end_post_time,
        #                       limit_count=limit_count, minContentLength=minContentLength,
        #                       maxContentLength=maxContentLength, output_db_name=output_db_name,
        #                       output_table_name=output_table_name, status=status,
        #                       progress_status=progress_status, time=time)
    else:
        row["_id"] = int(row.pop("id"))
        _source_list: str = row.pop("source_list")
        _model_list: str = row.pop("model_list")
        _black_list: str = row.pop("black_list")
        _white_list: str = row.pop("white_list")
        _progress_db_name: str = row.pop("progress_db_name")
        author = AudienceTask(**row)

    author.source_list = _source_list.split(",")
    author.model_list = _model_list.split(",")
    author.black_list = list() if _black_list == "" else _black_list.split(",")
    author.white_list = list() if _white_list == "" else _white_list.split(",")
    author.progress_db_name = _progress_db_name.split(",") if _progress_db_name else list()
    author.start_post_time = str(author.start_post_time)
    author.end_post_time = str(author.end_post_time)
    author.time = str(author.time)

    return author


def init_audience_task_schema(conn_info: ConnInfo):
    query = f'''CREATE TABLE IF NOT EXISTS {conn_info.table}
                (id {"INT(11)" if DBType(conn_info.db_type) != DBType.SQLITE else "INTEGER"}
                NOT NULL PRIMARY KEY
                {"AUTO_INCREMENT" if DBType(conn_info.db_type) != DBType.SQLITE else "AUTOINCREMENT"},
                name varchar(64) DEFAULT NULL,
                description text DEFAULT NULL,
                source_list VARCHAR(256) NOT NULL,
                model_list  NVARCHAR(256) NOT NULL,
                start_post_time  DATETIME NOT NULL,
                end_post_time  DATETIME NOT NULL,
                limit_count   INT(10) NOT NULL,
                minContentLength INT(10) NOT NULL,
                maxContentLength INT(10) NOT NULL,
                output_db_name VARCHAR(64) NOT NULL,
                output_table_name VARCHAR(64) NOT NULL,
                black_list VARCHAR(256) NULL,
                white_list VARCHAR(256) NULL,
                status VARCHAR(64) NOT NULL,
                progress_db_name VARCHAR(64) NULL,
                progress_status VARCHAR(64) NOT NULL,
                time  DATETIME NOT NULL)
                {"DEFAULT CHARSET=utf8mb4" if DBType(conn_info.db_type) != DBType.SQLITE else ""};
            '''
    init_schema(conn_info=conn_info, sql_query=query)


def insert_audience_task(conn_info: ConnInfo, audience_task: AudienceTask):
    insert_fields = audience_task.to_database_fields()
    field_name, task_id = insert_fields.pop(0)
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''INSERT INTO {conn_info.table} 
                    ({",".join(["`" + k + "`" for k, v in insert_fields])})  
                    VALUES ({",".join(["%s"] * len(insert_fields))});'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''INSERT INTO {conn_info.table} 
                    ({",".join(["`" + k + "`" for k, v in insert_fields])})
                    VALUES ({",".join(["?"] * len(insert_fields))});'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    example = list([v for k, v in insert_fields])
    return insert_example(conn_info=conn_info, sql_query=query, example=example)


def update_audience_task(conn_info: ConnInfo, audience_task: AudienceTask):
    insert_fields = audience_task.to_database_fields()
    field_name, task_id = insert_fields.pop(0)
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''
                    UPDATE {conn_info.table} 
                    SET {", ".join([k+"=%s" for k, v in insert_fields])} 
                    WHERE id = %s
                 '''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''
        UPDATE {conn_info.table} 
                    SET {", ".join([k+"=?" for k, v in insert_fields])} 
                    WHERE id = ?
                 '''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    example = list([v for k, v in insert_fields])
    example.append(task_id)
    return update_example(conn_info, query, example=example)


def update_audience_task_status(conn_info: ConnInfo, status: str, task_id: int):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''UPDATE {conn_info.table} SET status=%s WHERE id = %s'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''UPDATE {conn_info.table} SET status=? WHERE id = ?'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    return update_example(conn_info, query, example=(status, task_id))


def update_audience_task_progress_status(conn_info: ConnInfo, progress_db_name: List, progress_status: str,
                                         task_id: int):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''UPDATE {conn_info.table} SET progress_db_name=%s, progress_status=%s WHERE id = %s'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''UPDATE {conn_info.table} SET progress_db_name=?, progress_status=? WHERE id = ?'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    return update_example(conn_info, query, example=(convert_to_str(progress_db_name), progress_status, task_id))


def select_audience_task(conn_info: ConnInfo, audience_task_id: int) -> Optional[AudienceTask]:
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f"""SELECT * FROM {conn_info.table} WHERE `id` = %s;"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table} WHERE `id` = ?;"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    result: Optional[AudienceTask] = select_example(conn_info, query, [audience_task_id])
    return get_audience_task_entity_from_row(result) if result is not None else None


def select_audiences_task(conn_info: ConnInfo) -> List[Optional[AudienceTask]]:
    if DBType(conn_info.db_type) == DBType.MARIADB or DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table};"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    results: List[Optional[Dict]] = [get_audience_task_entity_from_row(result).to_api_result() for result in
                                     select_examples(conn_info, query)]
    return results


def select_wait_audiences_task(conn_info: ConnInfo) -> List[Optional[AudienceTask]]:
    if DBType(conn_info.db_type) == DBType.MARIADB or DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table} WHERE status = 'wait';"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    results: List[Optional[AudienceTask]] = [get_audience_task_entity_from_row(result) for result in
                                             select_examples(conn_info, query)]
    return results


def delete_audience_task(conn_info: ConnInfo, task_id: int):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''DELETE FROM {conn_info.table} WHERE id = %s'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''DELETE FROM {conn_info.table} WHERE id = ?'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    return delete_example(conn_info, query, example=(task_id,))


def convert_to_str(_list: List):
    _str = ",".join(_list)
    return _str if _str else ""
