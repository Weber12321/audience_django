from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

import requests

from audience_toolkits.settings import DEEPNLP_POS_API, DEEPNLP_POS_API_TOKEN, BASE_DIR as ROOT_DIR, STOP_WORD_DIR
from text_helper import split_batch


def _read_file(file_path) -> str:
    with open(file_path, "r", encoding="utf-8") as fr:
        for data in fr.readlines():
            data = data.strip()
            yield data


def read_stop_words():
    stopWordsConfig = STOP_WORD_DIR
    stopWords = list()
    # read files
    if "files" in stopWordsConfig:
        for file_ in stopWordsConfig["files"]:
            for words in _read_file(Path(ROOT_DIR / file_)):
                stopWords.append(words)
    return stopWords


class Tokenizer(ABC):
    @abstractmethod
    def tokenize(self, docs: Iterable[str]):
        pass

    @abstractmethod
    def remainderWords(self, segments: Iterable):
        pass


class DeepnlpPosTokenizer(Tokenizer):
    """
    DeepNLP API斷詞器
    """

    def __init__(self, api_host=DEEPNLP_POS_API, black_list=None, white_list=None, mode="segment",
                 api_token=DEEPNLP_POS_API_TOKEN):
        self.api_host = api_host
        self.api_token = api_token if api_token is not None else ""
        self.mode = mode
        self.black_list = black_list if black_list is not None else []
        self.white_list = white_list if white_list is not None else []

    def tokenize(self, docs: Iterable[str], batch: int = 100) -> List[Iterable[str]]:
        """
        呼叫DeepNLP API斷詞器
        Args:
            docs: 文件集
            batch: 每次請求文章數量，預設為100

        Returns:
            斷詞後的文件sequence列表
        """
        rs = []
        for _docs in split_batch(docs, batch):
            query = {
                "token": self.api_token,
                "settings": {
                    "black_list": self.black_list,
                    "white_list": self.white_list,
                    "mode": self.mode
                },
                "doc_list": [{"id": idx, "content": doc} for idx, doc in enumerate(_docs)]
            }
            r = requests.post(self.api_host, json=query)
            # todo http請求例外處理
            rs.extend([_rs["segment_content"] for _rs in r.json()["result_list"]])
        return rs

    def remainderWords(self, segments: Iterable):
        pass


class JiebaTokenizer(Tokenizer):
    def __init__(self):
        self.stopwords = read_stop_words()

    def tokenize(self, docs: Iterable[str]):
        import jieba
        rs = []
        for doc in docs:
            rs.append(jieba.cut(doc))
        return rs

    def remainderWords(self, segments: Iterable):
        return filter(lambda a: a not in self.stopwords and a != '\n', segments)


if __name__ == '__main__':
    text = ["$剛去拿飯店員一直看著我叫先生先生：）到底是怎麼發現我是男的"]
    jieba = JiebaTokenizer()

    rs = jieba.tokenize(text)

    print([" ".join(jieba.remainderWords(i)) for i in rs])
