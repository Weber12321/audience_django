import datetime

from dataclasses import dataclass, field
from typing import List, Optional, Dict

from audience_toolkits.settings import FETCH_COUNT

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


def convert_to_str(_list: List):
    _str = ",".join(_list)
    return _str if _str else ""
