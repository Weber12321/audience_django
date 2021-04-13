import os
import pickle
import sqlite3
from contextlib import contextmanager
from typing import Iterable, List, Optional, Union

import gridfs
import pymysql
from bson import ObjectId
from core.dao.conn_info import ConnInfo
from pymongo import MongoClient
from retry import retry

from audience_toolkits.settings import BASE_DIR as ROOT_DIR
from core.dao.model_info import ModelInfo, preprocess_data_form_mongodb
from enums_helper import DBType, Errors
from log_helper import get_logger

_logger = get_logger("DBOperator", verbose=True)

DB_ARGS_MAP = {"AUTOINCREMENT": {DBType.MARIADB: "AUTO_INCREMENT", DBType.SQLITE: "AUTOINCREMENT"}}
DEFAULT_MARIA_COUNT_QUERY = "SELECT count(*) as row_count FROM {} {};"
DEFAULT_SQLITE_COUNT_QUERY = "SELECT count(*) as row_count FROM {} {};"


@contextmanager
def get_db_connection(conn_info: ConnInfo):
    conn = None
    if type(conn_info.db_type) == str:
        conn_info.db_type = DBType(conn_info.db_type)
    if conn_info.db_type == DBType.MARIADB:
        try:
            conn = pymysql.connect(
                host=conn_info.host, port=conn_info.port, user=conn_info.user,
                passwd=conn_info.pwd, db=conn_info.schema,
                cursorclass=pymysql.cursors.SSDictCursor,
                connect_timeout=conn_info.connect_timeout
            )
            # _logger.debug(f"{conn_info.host}:{conn_info.schema} connect ok!")
            yield conn
        finally:
            if conn is not None:
                conn.close()
    elif conn_info.db_type == DBType.SQLITE:
        try:
            if not conn_info.host.startswith("/"):
                conn_info.host = os.path.join(ROOT_DIR, conn_info.host)
            conn = sqlite3.connect(
                os.path.join(conn_info.host, conn_info.schema)
            )
            # _logger.debug(f"{os.path.join(conn_info.host, conn_info.schema)} connect ok!")
            yield conn
        finally:
            if conn is not None:
                conn.close()
    elif conn_info.db_type == DBType.MONGODB:
        try:
            conn = MongoClient(f"mongodb://{conn_info.user}:"
                               f"{conn_info.pwd}@"
                               f"{conn_info.host}:"
                               f"{conn_info.port}/"
                               f"{conn_info.authentication_db}"
                               f"?w=1&authMechanism=SCRAM-SHA-1"
                               f"&appName=deepnlp&maxPoolSize=5"
                               f"&maxIdleTimeMS=10000", connect=False)
            yield conn
        finally:
            if conn is not None:
                conn.close()
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def init_schema(conn_info: ConnInfo, sql_query: str):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        c.execute(sql_query)
        if conn_info.db_type == DBType.MARIADB:
            c.execute("SET NAMES utf8mb4")
            c.execute("SET CHARACTER SET utf8mb4")
            c.execute("SET character_set_connection = utf8mb4")
        conn.commit()
        c.close()


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def drop_schema(conn_info: ConnInfo):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        c.execute(f'''DROP TABLE IF EXISTS {conn_info.table}''')
        conn.commit()
        c.close()


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def insert_example(conn_info: ConnInfo, sql_query: str, example: Iterable):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        result = c.execute(sql_query, example)
        conn.commit()
        c.close()
        return result


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def select_example(conn_info: ConnInfo, sql_query: str, example: Iterable = None):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        if example is None:
            c.execute(sql_query)
        else:
            c.execute(sql_query, example)
        row = c.fetchone()
        c.close()
    return row


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def select_examples(conn_info: ConnInfo, sql_query: str, example: Iterable = None):
    tmp_rows = list()
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        if example is None:
            c.execute(sql_query)
        else:
            c.execute(sql_query, example)
        row = c.fetchone()
        while row is not None:
            # tmp_rows.append([r for r in row])
            # tmp_rows.append(row)
            yield row
            row = c.fetchone()
        c.close()
    # return tmp_rows


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def update_example(conn_info: ConnInfo, sql_query: str, example: Iterable):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        result = c.execute(sql_query, example)
        conn.commit()
        c.close()
        return result


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def delete_example(conn_info: ConnInfo, sql_query: str, example: Iterable):
    with get_db_connection(conn_info) as conn:
        c = conn.cursor()
        result = c.execute(sql_query, example)
        conn.commit()
        c.close()
        return result


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def get_row_count(conn_info: ConnInfo, sql_query=None, condition: str = None, row_count_col="row_count"):
    if sql_query is None:
        if DBType(conn_info.db_type) == DBType.MARIADB:
            sql_query = DEFAULT_MARIA_COUNT_QUERY.format(f"{conn_info.table}",
                                                         f"{condition if condition is not None else ''}")
        elif DBType(conn_info.db_type) == DBType.SQLITE:
            sql_query = DEFAULT_SQLITE_COUNT_QUERY.format(f"{conn_info.table}",
                                                          f"{condition if condition is not None else ''}")
    with get_db_connection(conn_info) as conn:
        cursor = conn.cursor()
        _logger.debug(sql_query)
        cursor.execute(sql_query)

        row = cursor.fetchone()
        cursor.close()
    if conn_info.db_type is DBType.SQLITE:
        return row[0]
    elif conn_info.db_type is DBType.MARIADB:
        return row[row_count_col]
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def drop_model_collection(conn_info: ConnInfo, collection_name: str) -> None:
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        collection = db[collection_name]
        collection.drop()


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def delete_model(conn_info: ConnInfo, condition: dict) -> bool:
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        collection = db[conn_info.table]
        x = collection.delete_one(condition)
        return x.deleted_count > 0


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def operate_file_data(conn_info: ConnInfo, condition=None, query=None) -> bool:
    """
    操作子元素內的資料
    :param conn_info: 連線資訊
    :param condition: 查詢條件
    :param query: 更改條件
    :return:
    """
    if query is None:
        query = {}
    if condition is None:
        condition = {}
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        collection = db[conn_info.table]
        x = collection.update_one(condition, query)
        return x.acknowledged


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def get_collections_name(conn_info: ConnInfo) -> Optional[List]:
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        return db.list_collection_names()


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def insert_model(conn_info: ConnInfo, model_data: dict) -> bool:
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        collection = db[conn_info.table]
        result = collection.insert_one(model_data)
        return result is not None


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def select_model(conn_info: ConnInfo, condition=None) -> Union[ModelInfo, List]:
    with get_db_connection(conn_info=conn_info) as conn:
        if condition is None:
            condition = {}
        db = conn[conn_info.schema]
        collection = db[conn_info.table]
        _cursor = collection.find(condition)
        return preprocess_data_form_mongodb(dataset=_cursor)


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def select_models(conn_info: ConnInfo, condition=None, field=None) -> Union[ModelInfo, List]:
    if condition is None:
        condition = {}
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.schema]
        collection = db[conn_info.table]
        if field is None:
            _cursor = collection.find(condition).sort('_id', -1)
        else:
            _cursor = collection.find(condition, field).sort('_id', -1)
        return preprocess_data_form_mongodb(dataset=_cursor)


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def insert_temp_data(conn_info: ConnInfo, file) -> ObjectId:
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.index_db]
        fs = gridfs.GridFS(db)
        _id = fs.put(file)
        return _id


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def get_temp_data(conn_info: ConnInfo, train_file_id: str):
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.index_db]
        fs = gridfs.GridFS(db)
        out = fs.get(ObjectId(train_file_id))
        _temp_data = pickle.loads(out.read())
        return _temp_data


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def delete_temp_data(conn_info: ConnInfo, train_file_id: str):
    with get_db_connection(conn_info=conn_info) as conn:
        db = conn[conn_info.index_db]
        fs = gridfs.GridFS(db)
        fs.delete(ObjectId(train_file_id))


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def update_model_label(conn_info: ConnInfo, sql_query: str, modelId, id, label):
    with get_db_connection(conn_info) as conn:
        mydb = conn[conn_info.index_db]
        mycol = mydb[conn_info.table]

        id = int(id) - 1
        query = {"_id": ObjectId(modelId)}
        new_values = {"$set": {f'train_file.{id}.label': label}}
        mycol.update(query, new_values)
        return "finish update label"


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def getModelLabels(conn_info: ConnInfo, modelId):
    with get_db_connection(conn_info) as conn:
        query = {"_id": ObjectId(modelId)}
        mydb = conn[conn_info.index_db]
        mycol = mydb[conn_info.table]
        data = mycol.distinct("train_file", query)
        labels = []
        for info in data:
            labels.append(info["label"])
        labels = set(labels)
        labels = ",".join(labels)
        return labels


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def update_labels(conn_info: ConnInfo, model_id, labels):
    with get_db_connection(conn_info) as conn:
        mydb = conn[conn_info.index_db]
        mycol = mydb[conn_info.table]
        query = {"_id": ObjectId(model_id)}
        new_values = {"$set": {'labels': labels}}
        mycol.update(query, new_values)
        return "finish update defined_labels"


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def count_labels_info(conn_info: ConnInfo, model_id):
    with get_db_connection(conn_info) as conn:
        mydb = conn[conn_info.index_db]
        mycol = mydb[conn_info.table]
        query = {"_id": ObjectId(model_id)}
        datas = mycol.find(query)
        label_counter = {"nan": 0}

        for data in datas:
            for info in data["train_file"]:
                label = info["label"]
                if type(label) is float:  # for nan labels
                    label_counter["nan"] += 1
                elif label in label_counter.keys():
                    label_counter[label] += 1
                else:
                    label_counter[label] = 1
        return label_counter


@retry(tries=StaticConfigs.database_setting.connect_retries, delay=3, backoff=1.5, logger=_logger)
def get_model_defined_labels(conn_info: ConnInfo, model_id):
    with get_db_connection(conn_info) as conn:
        mydb = conn[conn_info.index_db]
        mycol = mydb[conn_info.table]
        query = {"_id": ObjectId(model_id)}
        datas = mycol.find(query)
        defined_labels = ""
        for data in datas:
            defined_labels = data["labels"]
        defined_labels = defined_labels.split(",")
        return defined_labels
