import json
import re
from collections import namedtuple, defaultdict
from dataclasses import dataclass, field, astuple
from datetime import datetime
from typing import Dict, List, Optional, Iterable, Any

from tqdm import tqdm

from core.dao.conn_info import ConnInfo
from core.helpers.db_helper import insert_example, init_schema, select_example, update_example, select_examples
from core.helpers.text_helper import REText
from core.helpers.enums_helper import DBType, Errors, ModelType

patterns = [REText.http_pattern, REText.br_pattern]


@dataclass
class Author(object):
    id_: str
    name: str
    s_area_id: str
    docs: Dict[str, Dict[str, Any]] = field(default_factory=lambda: dict())
    content: Dict[str, set] = field(default_factory=lambda: dict())
    recent_result: Optional[Dict[str, Any]] = field(default=None)
    recent_post_count: int = field(default=0)

    def __iter__(self):
        return iter(astuple(self))

    def get_labels(self):
        _labels = set()
        for doc_id, labels in self.docs.items():
            _labels.update({_l for _l in labels.keys()})
        return _labels

    def get_post_num(self):
        _post_num = len(self.docs)
        _post_num += self.recent_post_count
        return _post_num

    def to_dict(self):
        return {
            "id": self.id_,
            "name": self.name,
            "s_area_id": self.s_area_id,
            "docs": self.docs
        }

    def to_api_result(self):
        return {
            "source_id": self.id_,
            "author": self.name,
            "source_author": self.s_area_id,
            "panel": self.panel,
            "score": self.score,
            "content": self.content,
            "create_time": str(self.create_time)
        }

    def get_api_result(self):
        AuthorResult = namedtuple("AuthorResult", ["id", "name", "s_area_id", "post_count", "labeling_result"])
        return AuthorResult(**{
            "id": self.id_,
            "name": self.name if self.name != "" and self.name is not None else 'UNK',
            "s_area_id": self.s_area_id,
            "post_count": self.get_post_num(),
            "labeling_result": self.get_labels()
        })

    def merge_author(self, other):
        if self.recent_result is not None:
            if other.recent_result is not None:
                for l_, c in other.recent_result.items():
                    self.recent_result[l_] = self.recent_result.get(l_, 0) + c
        else:
            if other.recent_result is not None:
                self.recent_result = other.recent_result
        if len(other.docs) > 0:
            for l_, models in other.docs.items():
                for model in models:
                    if l_ not in self.docs:
                        self.docs[l_] = dict()
                    self.docs[l_][model] = other.docs[l_][model]
        if hasattr(other, "recent_post_count"):
            self.recent_post_count += other.recent_post_count

    def add_label(self, doc_id: str, label: str, model_name: str = None, predict_result: Any = None,
                  model_type: ModelType = ModelType.PROB_MODEL):
        if model_name is None:
            model_name = model_type.name
        if doc_id not in self.docs:
            self.docs[doc_id] = {}
        if label not in self.docs[doc_id]:
            self.docs[doc_id][label] = {}
        self.docs[doc_id][label][model_name] = {
            "model_type": model_type.name,
            "predict_result": predict_result,
            "create_time": datetime.now()
        }

    def add_content(self, label: str, content: str):
        if label not in self.content:
            self.content[label] = set()
        for pattern in patterns:
            content = re.sub(pattern, "", content)
        if len(self.content[label]) < 10:
            self.content[label].add(content)

    def reset(self):
        self.docs.clear()

    def get_scores(self) -> Dict[str, list]:
        _labels_scores = defaultdict(list)
        for doc_id, labels in self.docs.items():
            for label, rs in labels.items():
                if label is None:
                    continue
                _labels_scores[label].append(len(rs))
        if self.recent_result is not None:
            for l_, c in self.recent_result.items():
                _labels_scores[l_].append(c)
        return {label: sum(scores) / self.get_post_num() for label, scores in _labels_scores.items()}

    def get_labeling_scores(self) -> Dict[str, list]:
        _labeling_scores = defaultdict(list)
        for doc_id, labels in self.docs.items():
            for label, rs in labels.items():
                if label is None:
                    continue
                for model_name, result in rs.items():
                    model_type = result["model_type"]
                    if model_type == ModelType.RULE_MODEL.name:
                        _labeling_scores[label] = 1000000000
                    elif model_type == ModelType.KEYWORD_MODEL.name:
                        _labeling_scores[label] = 10000000000000
                    else:
                        _labeling_scores[label] = float(result.get("predict_result", 0))
        if self.recent_result is not None:
            for l_, c in self.recent_result.items():
                _labeling_scores[l_].append(c)
        return {label: scores for label, scores in _labeling_scores.items()}

    def get_label_score(self, label: str) -> float:
        raise NotImplementedError

    def get_result_json(self):
        return json.dumps(self.get_scores(), ensure_ascii=False).encode('utf-8')


def convert_to_content_str(_list: set):
    return "\n\n----\n\n".join(_list),


def get_author_entity_from_row(row) -> Author:
    if type(row) == tuple or type(row) == list:
        author_id = row[0]
        name = row[1]
        s_area_id = row[2]
        post_count = row[3]
        labels = row[4]
        create_time = row[5]
    else:
        author_id = row["author_id"]
        name = row["name"]
        s_area_id = row["s_area_id"]
        post_count = row["post_count"]
        labels = row["labels"]
        create_time = row["create_time"]
    author = Author(
        id_=author_id, name=name, s_area_id=s_area_id
    )
    label_result = json.loads(labels)
    author.recent_post_count = post_count
    author.labels = label_result
    author.recent_result = {l_: c * post_count for l_, c in label_result.items()}
    author.create_time = create_time
    return author


def get_labeling_author_entity_from_row(row) -> Author:
    if type(row) == tuple or type(row) == list:
        source_id = row[0]
        author = row[1]
        source_author = row[2]
        panel = row[3]
        score = row[4]
        create_time = row[5]
    else:
        source_id = row["source_id"]
        author = row["author"]
        source_author = row["source_author"]
        panel = row["panel"]
        score = row["score"]
        content = row["content"]
        create_time = row["create_time"]
    author = Author(
        id_=source_id, name=author, s_area_id=source_author
    )
    author.panel = panel
    author.score = score
    author.content = content
    author.create_time = create_time
    return author


def init_author_schema(conn_info: ConnInfo):
    query = f'''CREATE TABLE IF NOT EXISTS {conn_info.table}
                (author_id    CHAR(64) PRIMARY KEY,
                name TEXT    NOT NULL,
                s_area_id    CHAR(16),
                post_count  INT,
                labels   JSON,
                create_time  DATETIME    NOT NULL)
                {"DEFAULT CHARSET=utf8mb4" if DBType(conn_info.db_type) != DBType.SQLITE else ""};
            '''
    init_schema(conn_info=conn_info, sql_query=query)


def init_labeling_author_schema(conn_info: ConnInfo):
    query = f'''CREATE TABLE IF NOT EXISTS {conn_info.table}
                (source_id CHAR(64) NOT NULL,
                author VARCHAR(100) NOT NULL,
                source_author TEXT NOT NULL ,
                panel CHAR(50) NOT NULL,
                score FLOAT,
                content TEXT NOT NULL,
                create_time DATETIME NOT NULL,
                PRIMARY KEY (source_id, author, panel))
                {"DEFAULT CHARSET=utf8mb4" if DBType(conn_info.db_type) != DBType.SQLITE else ""};
            '''
    init_schema(conn_info=conn_info, sql_query=query)


def insert_author(conn_info: ConnInfo, author: Author):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''INSERT INTO {conn_info.table} 
                    (`author_id`, `name`, `s_area_id`, `post_count`, `labels`, `create_time`) 
                    VALUES (%s,%s,%s,%s,%s,%s);'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''INSERT INTO {conn_info.table} 
                    (`author_id`, `name`, `s_area_id`, `post_count`, `labels`, `create_time`) 
                    VALUES (?,?,?,?,?,?);'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    example: tuple = (
        author.id_,
        author.name,
        author.s_area_id,
        len(author.docs),
        author.get_result_json(),
        datetime.now()
    )
    insert_example(conn_info=conn_info, sql_query=query, example=example)


def insert_labeling_author(conn_info: ConnInfo, author: Author):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f'''INSERT INTO {conn_info.table} 
                    (`source_id`, `author`, `source_author`, `panel`, `score`, `content`, `create_time`) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s);'''
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f'''INSERT INTO {conn_info.table} 
                    (`source_id`, `author`, `source_author`, `panel`, `score`, `content`,`create_time`)
                    VALUES (?,?,?,?,?,?,?);'''
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    scores = author.get_labeling_scores()

    for label, score in scores.items():
        example: tuple = (
            author.s_area_id,
            author.name,
            author.id_,
            f"/{label}",
            score,
            convert_to_content_str(author.content[label]),
            datetime.now()
        )
        insert_example(conn_info=conn_info, sql_query=query, example=example)


def select_author(conn_info: ConnInfo, author_id: str) -> Optional[Author]:
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f"""SELECT * FROM {conn_info.table} WHERE `author_id` = %s;"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table} WHERE `author_id` = ?;"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    result: Optional[Author] = select_example(conn_info, query, [author_id])
    return get_author_entity_from_row(result) if result is not None else None


def select_labeling_authors(conn_info: ConnInfo, source_author: str) -> List[Optional[Author]]:
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f"""SELECT * FROM {conn_info.table} WHERE `source_author` = %s;"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table} WHERE `source_author` = ?;"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    results: List[Optional[Author]] = [get_labeling_author_entity_from_row(result) for result in
                                       select_examples(conn_info, query, [source_author])]
    return results


def select_labeling_authors_sample(conn_info: ConnInfo, panel: str = None,
                                   limit: int = 100, offset: int = 0) -> List[Dict]:
    if DBType(conn_info.db_type) == DBType.MARIADB:
        where_query = f"WHERE `panel` = %s" if panel else ""
        query = f"""SELECT * FROM {conn_info.table} {where_query} LIMIT {limit} OFFSET {offset};"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        where_query = f"WHERE `panel` = ?" if panel else ""
        query = f"""SELECT * FROM {conn_info.table} {where_query} LIMIT {limit} OFFSET {offset};"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    results: List[Dict] = [get_labeling_author_entity_from_row(result).to_api_result() for result in
                           select_examples(conn_info, query, panel)]
    return results


def select_authors(conn_info: ConnInfo, limit: int = 100, offset: int = 0) -> List[Optional[Author]]:
    if DBType(conn_info.db_type) == DBType.MARIADB or DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""SELECT * FROM {conn_info.table} LIMIT {limit} OFFSET {offset};"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    results: List[Optional[Author]] = [get_author_entity_from_row(result) for result in
                                       select_examples(conn_info, query)]
    return results


def update_author(conn_info: ConnInfo, author: Author):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f"""UPDATE {conn_info.table} SET post_count=%s, labels=%s WHERE `author_id` = %s;"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""UPDATE {conn_info.table} SET post_count=?, labels=? WHERE `author_id` = ?;"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")
    labels = author.get_scores()
    update_example(conn_info, query, (len(author.docs), json.dumps(labels, ensure_ascii=False), author.id_))


def update_labeling_author_score(conn_info: ConnInfo, author: Author, other: List[Optional[Author]]):
    if DBType(conn_info.db_type) == DBType.MARIADB:
        query = f"""UPDATE {conn_info.table} SET score=%s, content=%s WHERE `source_author`=%s AND `panel`=%s;"""
    elif DBType(conn_info.db_type) == DBType.SQLITE:
        query = f"""UPDATE {conn_info.table} SET score=? WHERE `source_author`=? AND `panel`=?;"""
    else:
        raise ValueError(f"{Errors.UNKNOWN_DB_TYPE}: {conn_info.db_type}")

    scores = author.get_labeling_scores()
    other_panel_score = {p.panel: p.score for p in other}

    for _l, score in scores.items():
        _label = f"/{_l}"
        if _label in other_panel_score:
            if score < other_panel_score[_label]:
                score = other_panel_score[_label]
            else:
                continue
        example: tuple = (
            score,
            convert_to_content_str(author.content[_l]),
            author.id_,
            _label
        )
        update_example(conn_info=conn_info, sql_query=query, example=example)


def upsert_authors(conn_info: ConnInfo, authors: Iterable[Author]):
    for author in tqdm(authors, desc="Insert author results"):
        _author = select_author(conn_info, author_id=author._id)
        if _author is None:
            insert_author(conn_info, author=author)
        else:
            author.merge_author(_author)
        update_author(conn_info, author=author)


def upsert_labeling_authors(conn_info: ConnInfo, authors: Iterable[Author]):
    for author in tqdm(authors, desc="Insert labeling author results"):
        _author: List[Optional[Author]] = select_labeling_authors(conn_info, source_author=author._id)
        if not _author:
            # 初始化該作者標籤
            insert_labeling_author(conn_info, author=author)
        else:
            # 更新該作者沒被貼到的標籤
            update_labeling_author_score(conn_info, author=author, other=_author)
