from pathlib import Path
from typing import List, Optional

import jieba
import joblib
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from core.audience.models.base_model import AudienceModel
from core.helpers.data_helpers import DataHelper
from core.helpers.model_helpers import get_multi_accuracy, load_joblib


class SvmModel(AudienceModel):
    def __init__(self, model_dir_name, is_multi_label=False):
        super().__init__(model_dir_name)
        self.vectorizer = None
        self.is_multi_label = is_multi_label
        self.model_path = self.model_dir_path / 'model.pkl'
        self.vectorizer_path = self.model_dir_path / 'vectorizer.pkl'
        self.mlb: Optional[MultiLabelBinarizer] = None  # MultiLabelBinarizer, for multi-label task
        self.mlb_path = self.model_dir_path / 'mlb.pkl'

    def convert_feature(self, contents, update_vectorizer=False):
        seg_contents = [' '.join(jieba.lcut(content)) for content in contents]
        if update_vectorizer:
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(max_features=5000, min_df=2, stop_words='english')
            x_features = self.vectorizer.fit_transform(seg_contents)
        else:
            if self.vectorizer:
                x_features = self.vectorizer.transform(seg_contents)
            else:
                raise ValueError("模型尚未被初始化，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")
        return x_features

    def fit(self, contents, y_true: List):
        """

        :param contents:
        :param y_true:
                - normal classifier: List,
                    i.e. ['sci-fi', 'thriller', 'comedy']
                - multi-label classifier: List[Union[List, Set, Tuple]]
                    i.e. [('sci-fi', 'thriller'), ('comedy',)]
                    or [{'sci-fi', 'thriller'}, {'comedy'}]
                    or [['sci-fi', 'thriller'], ['comedy']]
        :return:
        """
        x_train_features = self.convert_feature(contents, update_vectorizer=True)
        classifier = svm.SVC(kernel='linear')
        if self.is_multi_label:
            self.mlb = MultiLabelBinarizer()
            y_true = self.mlb.fit_transform(y_true)
            self.model = OneVsRestClassifier(classifier)
        else:
            self.model = classifier
        self.model.fit(x_train_features, y_true)
        return self.save()

    def predict(self, contents):
        x_features = self.convert_feature(contents)
        return self.model.predict(x_features)

    def eval(self, contents, y_true):
        if self.model and self.vectorizer:
            x_features = self.convert_feature(contents)
            y_pre = self.predict(x_features)
            if self.is_multi_label:
                y_true = self.mlb.transform(y_true)
                acc = get_multi_accuracy(y_true, y_pre)
                report = classification_report(y_true, y_pre, output_dict=True)
                report['accuracy'] = acc
                dataHelper = DataHelper()
                dataHelper.save_report(self.model_dir_path, report)
            else:
                report = classification_report(y_true, y_pre, output_dict=True)
                dataHelper = DataHelper()
                dataHelper.save_report(self.model_dir_path, report)
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

    def save(self):
        if not self.model_dir_path.exists():
            self.model_dir_path.mkdir(parents=True, exist_ok=True)
        # todo 未來可嘗試加入model版控
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        if self.is_multi_label:
            joblib.dump(self.mlb, self.mlb_path)
        return self.model_dir_path

    def load(self):
        # todo 未來可嘗試加入model版控
        self.model = load_joblib(self.model_path)
        self.vectorizer = load_joblib(self.vectorizer_path)
        if self.is_multi_label:
            self.mlb = load_joblib(self.mlb_path)

