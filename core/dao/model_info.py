import os
import pickle
import re
import time
from pathlib import Path

import pandas as pd
from dataclasses import dataclass, field
from sqlite3 import Cursor
from typing import Optional, Any, List, Union, Dict

from bson import ObjectId
from pandas import DataFrame

from core.helpers.enums_helper import PredictTarget, ModelType, TokenizerType
from core.helpers.file_helper import make_temporary_dir
from core.helpers.log_helper import get_logger
from audience_toolkits.settings import TEMP_DIR
from core.helpers.tokenizers import JiebaTokenizer, DeepnlpPosTokenizer

DEFAULT_COLUMNS: List = ["label", "title", "content", "s_area_id", "author"]
DEFAULT_KEYWORD_COLUMNS: List = ["label", "term", "rule"]
DEFAULT_RULE_COLUMNS: List = ["label", "term"]
DEFAULT_SVM_COLUMNS: List = ["label", "content"]
DEFAULT_XGBOOST_COLUMNS: List = ["label", "content"]


def _check_columns(model_type: str, title: List[str]) -> Union[List[str], ValueError]:
    """
    驗證欄位名稱是否一致
    :param title: csv開頭欄位
    :return: Union[List, ValueError]
    """
    # print(ModelType(model_type))
    # print(set(title))
    # print(set(DEFAULT_SVM_COLUMNS))
    if ModelType(model_type) is ModelType.RULE_MODEL:
        if set(title) != set(DEFAULT_RULE_COLUMNS):
            raise ValueError("必要欄位有缺少!")
    elif ModelType(model_type) is ModelType.KEYWORD_MODEL:
        if set(title) != set(DEFAULT_KEYWORD_COLUMNS):
            raise ValueError("必要欄位有缺少!")
    elif ModelType(model_type) is ModelType.SVM_MODEL:
        if set(title) != set(DEFAULT_SVM_COLUMNS):
            raise ValueError("必要欄位有缺少!")
    elif ModelType(model_type) is ModelType.XGBOOST_MODEL:
        if set(title) != set(DEFAULT_XGBOOST_COLUMNS):
            raise ValueError("必要欄位有缺少!")
    else:
        if set(title) != set(DEFAULT_COLUMNS):
            raise ValueError("必要欄位有缺少!")

    # 增加_id欄位
    title.insert(0, "_id")
    return title


@dataclass
class ModelInfo(object):
    id: str = field(default=0)
    train_file: Optional[Any] = field(default=None)
    name: Optional[str] = field(default=None)
    labels: Optional[str] = field(default=None)
    target: str = field(default=PredictTarget.CONTENT.value)
    modelType: Optional[str] = field(default=None)
    case_sensitive: Optional[bool] = field(default=None)
    tokenizer: Optional[str] = field(default=None)
    threshold: float = field(default=None)
    test_result: Optional[Dict] = field(default=None)
    test_report: Optional[Dict] = field(default=None)
    default_columns: Optional[List] = field(default=None)
    time: str = field(default=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    def to_dict(self):
        return {
            "train_file": self.train_file,
            "name": self.name,
            "labels": self.labels,

            "target": self.target,
            "modelType": self.modelType,
            "case_sensitive": self.case_sensitive,
            "tokenizer": self.tokenizer,
            "threshold": self.threshold,
            "time": self.time
        }

    def to_update_data(self):
        return {
            "name": self.name,
            "target": self.target,
            "case_sensitive": self.case_sensitive,
            "tokenizer": self.tokenizer,
            "time": self.time
        }

    def to_show_model_list(self):
        # fixme
        self.target = self.target.value
        self.modelType = self.modelType.value
        self.train_file = str(self.train_file) if type(self.train_file) is ObjectId else None
        return self

    def to_api_model_info(self):
        return {
            "name": self.name,
            "labels": self.labels.split(","),
            "target": self.target,
            "modelType": self.modelType,
            "case_sensitive": self.case_sensitive,
            "tokenizer": self.tokenizer,
            "threshold": self.threshold,
            "time": self.time
        }

    def to_model_list(self):
        return {
            "name": self.name
        }

    def to_keyword_param(self):
        return {
            "name": self.name,
            "target": self.target,
            "model_type": self.modelType,
            "case_sensitive": self.case_sensitive
        }

    def to_rule_param(self):
        return {
            "name": self.name,
            "target": self.target,
            "model_type": self.modelType
        }

    def to_prob_param(self):
        if type(self.threshold) is str:
            self.threshold = float(self.threshold)
        return {
            "name": self.name,
            "target": self.target,
            "model_type": self.modelType,
            "case_sensitive": self.case_sensitive,
            "threshold": self.threshold,
            "tokenizer": self.identify_tokenizer()
        }

    def to_rf_param(self):
        return {
            "name": self.name,
            "target": self.target,
            "model_type": self.modelType,
            "case_sensitive": self.case_sensitive,
            "tokenizer": self.identify_tokenizer()
        }

    def to_svm_param(self):
        return {
            "name": self.name,
            "target": self.target,
            "model_type": self.modelType,
            "case_sensitive": self.case_sensitive,
            "tokenizer": self.identify_tokenizer()
        }

    def identify_tokenizer(self):
        if self.tokenizer == TokenizerType.JIEBA.value:
            word_tokenizer = JiebaTokenizer()
        elif self.tokenizer == TokenizerType.DEEPNLP.value:
            word_tokenizer = DeepnlpPosTokenizer(api_host="http://172.18.20.183/segment", token="")
        else:
            raise ValueError(f"Unsupported tokenizer '{self.tokenizer}'")
        return word_tokenizer

    def process_csv_file(self):
        """
        處理csv檔內的資料
        :return:
        """
        csv_data, title = _preprocess_csv_file(files=self.train_file)

        # 驗證欄位名稱是否一致
        if not csv_data:
            raise IndexError("資料空值")
        title = _check_columns(model_type=self.modelType, title=title)

        # 處理成塞入db的資料
        data = list()
        for index, d in enumerate(csv_data):
            d.insert(0, str(index + 1))
            if len(title) == len(d):
                data.append(dict(zip(title, d)))
        self.train_file = data

        # 取出labels標籤
        labels = set()
        [labels.add(f["label"]) for f in data]
        self.labels = ",".join([str(s) for s in labels])
        return self

    def process_pkl_file(self):
        """
        處理pkl檔內的資料
        :return:
        """
        _file_path = _preprocess_temp_file(self.train_file[0])
        p = pickle.load(open(_file_path, "rb"))
        if p["model"]:
            self.labels = ",".join(p["model"].classes_)
        else:
            self.labels = ",".join(p["labels"])
        return _file_path, self

    def process_db_columns(self):
        # 移除名稱空白
        self.name = re.sub(r"\s+", "", self.name)
        return self


def preprocess_data_form_mongodb(dataset: Cursor) -> Union[ModelInfo, List]:
    """
    把從DB拉出來的資料轉成ModelInfo格式
    :param dataset:
    :return:
    """
    new_data = list()
    for data in dataset:
        data["id"] = str(data.pop("_id"))
        # todo: advanced
        if "case_sensitive" in data:
            if data["case_sensitive"] is not None:
                data["case_sensitive"] = data["case_sensitive"] == "true"

        if "modelType" in data:
            data["modelType"] = ModelType(data["modelType"])

        if "target" in data:
            data["target"] = PredictTarget(data["target"])
        new_data.append(data)

    new_dataset = [ModelInfo(**m) for m in new_data]
    return new_dataset


def _preprocess_csv_file(files):
    """
    處理csv檔，先存到temporary，再用讀檔的方式抓取encoding，並寫入DB
    :param files:
    :return:
    """
    sheets = DataFrame()
    title = None
    for file in files:
        _file_path = _preprocess_temp_file(file=file)
        # fixme: 編碼衝突問題
        with open(_file_path, "r", newline='', encoding="utf-8") as f:
            encoding = f.encoding
        sheet = (pd.read_csv(_file_path, header=None, encoding=encoding, sep="\t"))
        title = sheet.iloc[0]
        sheets = sheets.append(sheet.drop(sheet.index[0]))
        os.unlink(_file_path)
    # 抓出資料表上的欄位名稱 cp950 編碼方式
    # csv_data = list()
    # ioStream = io.StringIO(file.stream.read().strip().decode("cp950"), newline=None)
    # for row in csv.reader(ioStream):
    #     csv_data.append(row)
    # # 將指標撥回到開始位置，否則將會讀取不到任何東西
    # ioStream.seek(0)
    return sheets.values.tolist(), title.to_list()


def _preprocess_temp_file(file):
    logger = get_logger("modelInfo")
    temp_dir = make_temporary_dir(logger, TEMP_DIR)
    _file_path = Path(temp_dir, file.filename)

    file.save(_file_path)
    return _file_path
