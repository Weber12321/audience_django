from typing import List, Optional

import jieba
import joblib
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
import numpy as np
from core.audience.models.base_model import AudienceModel, MODEL_ROOT
from core.helpers.model_helpers import get_multi_accuracy, load_joblib


class SvmModel(AudienceModel):
    def __init__(self, model_dir_name, is_multi_label=False):
        super().__init__(model_dir_name)
        self.vectorizer = None
        self.is_multi_label = is_multi_label
        self.model_path = self.model_dir_name / 'model.pkl'

        self.vectorizer_path = self.model_dir_name / 'vectorizer.pkl'
        self.mlb: Optional[MultiLabelBinarizer] = None  # MultiLabelBinarizer, for multi-label task
        self.mlb_path = self.model_dir_name / 'mlb.pkl'

    def convert_feature(self, contents, update_vectorizer=False):
        # seg_contents = [' '.join(jieba.lcut(content)) for content in contents]
        seg_contents = []
        for content in contents:
            sentence = jieba.lcut(str(content))
            seg_contents.append(" ".join(sentence))

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

        for index, y in enumerate(y_true):
            y_true[index] = y_true[index][0].split(',')

        if self.is_multi_label:
            self.mlb = MultiLabelBinarizer()
            y_true = self.mlb.fit_transform(y_true)
            self.model = OneVsRestClassifier(classifier)
        else:
            y_true = np.asarray(y_true).ravel()
            self.model = classifier
        self.model.fit(x_train_features, y_true)
        return self.save()

    def predict(self, contents):
        x_features = self.convert_feature(contents)
        return self.model.predict(x_features)

    def eval(self, contents, y_true):

        for index, y in enumerate(y_true):
            y_true[index] = y

        if self.model and self.vectorizer:
            y_pre = self.predict(contents)
            if self.is_multi_label:
                y_true = self.mlb.transform(y_true)
                acc = get_multi_accuracy(y_true, y_pre)
                report = classification_report(y_true, y_pre, output_dict=True)
                report['accuracy'] = acc
            else:
                report = classification_report(y_true, y_pre, output_dict=True)
            return report
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

    def save(self):
        tmp_model_dir = MODEL_ROOT / self.model_dir_name
        if not tmp_model_dir.exists():
            tmp_model_dir.mkdir(parents=True, exist_ok=True)
        # todo 未來可嘗試加入model版控
        joblib.dump(self.model, MODEL_ROOT / self.model_path)
        joblib.dump(self.vectorizer, MODEL_ROOT / self.vectorizer_path)
        if self.is_multi_label:
            joblib.dump(self.mlb, MODEL_ROOT / self.mlb_path)

        return self.model_dir_name

    def load(self):
        # todo 未來可嘗試加入model版控
        self.model = load_joblib(MODEL_ROOT / self.model_path)
        self.vectorizer = load_joblib(MODEL_ROOT / self.vectorizer_path)
        if self.is_multi_label:
            self.mlb = load_joblib(MODEL_ROOT / self.mlb_path)
