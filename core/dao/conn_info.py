import os
from dataclasses import dataclass, field, astuple
from typing import Union, List, Optional

import dataclasses

from definition import ROOT_DIR
from utils.enums import DBType


@dataclass
class ConnInfo:
    table: str = field(default=None)
    schema_lists: Optional[List] = field(default=None)
    schema: str = field(default="audience_sample.db")
    db_type: Union[str, DBType] = field(default=DBType.SQLITE)
    host: str = field(default=os.path.join(ROOT_DIR, "tests"))
    port: int = field(default=None)
    user: str = field(default=None)
    pwd: str = field(default=None)
    authentication_db: str = field(default=None)
    index_db: str = field(default=None)
    connect_timeout: int = field(default=10)
    connect_retries: int = field(default=10)
    condition: str = field(default=None)

    def __iter__(self):
        return iter(astuple(self))

    def __init__(self, **kwargs):
        names = set([f.name for f in dataclasses.fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)