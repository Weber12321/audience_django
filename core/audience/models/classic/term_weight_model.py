import csv
import logging
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import List, Optional, Iterable, Dict, Tuple

import jieba
import numpy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import MultiLabelBinarizer

from audience_toolkits import settings
from core.audience.models.base_model import SuperviseModel, MODEL_ROOT
from core.dao.input_example import InputExample, Features

# Get an instance of a logger
logger = logging.getLogger(__name__)


class TermWeightModel(SuperviseModel):
    class DictHeaders(Enum):
        LABEL = "label"
        TERM = "term"
        WEIGHT = "weight"

    def __init__(self, model_dir_name, feature=Features.CONTENT, na_tag=None, **kwargs):
        super().__init__(model_dir_name=model_dir_name, feature=feature, na_tag=na_tag, **kwargs)
        self.dict_file_name = "term_dict.csv"
        logger.debug(self.__class__.__name__)
        self.label_term_weights: Dict[str, List[Tuple[str, float]]] = defaultdict(List)
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.vectorizer = None
        self.threshold = 0.3

    def fit(self, examples: List[InputExample], y_true):
        """
        get feature importance with sgd model or svm model
        :param examples:
        :param y_true:
        :return:
        """
        if isinstance(y_true[0], str):
            classes = list(set(y_true))
            y_true = [[y] for y in y_true]
        else:
            classes = set()
            for _y_pred in y_true:
                for y in _y_pred:
                    # logger.debug()(y)
                    classes.add(y)
            classes = list(classes)
        self.mlb = MultiLabelBinarizer(classes=classes)
        self.mlb.fit(y_true)
        logger.debug(self.mlb.classes_)
        # start training
        ovr_class_features = defaultdict(list)
        for label in self.mlb.classes_:
            tmp_y = []
            tmp_x_examples = []
            for idx, _y_true in enumerate(y_true):
                if isinstance(_y_true, list):
                    for y in _y_true:
                        tmp_y.append(y if y == label else "other")
                        tmp_x_examples.append(examples[idx])
                else:
                    tmp_y.append(_y_true)
                    tmp_x_examples.append(examples[idx])

            x_train = self.convert_feature(examples, update_vectorizer=True)
            feature_list = self.vectorizer.get_feature_names()
            label_term_dict = class_feature_importance(x_train, tmp_y, feature_list)
            ovr_class_features[label] = label_term_dict.get(label)
        self.label_term_weights = ovr_class_features
        return self.save()

    def predict(self, examples: List[InputExample]):
        """

        :param examples:
        :return:
        """
        if not self.label_term_weights:
            raise ValueError(f"模型尚未被讀取，請嘗試執行 ' load() ' 方法讀取模型。")
        matched_keyword = []
        result_labels = []
        logger.debug(f"feature = {self.feature}, threshold = {self.threshold}, labels = {self.label_term_weights.keys()}")
        for example in examples:
            content: str = getattr(example, self.feature.value)
            match_kw = defaultdict(list)
            _result_label = []
            for cls, keywords in self.label_term_weights.items():
                total_matched_count = 0
                total_matched_score = 0
                for keyword, weight in keywords:
                    if count := content.count(keyword):
                        match_kw[cls].append((keyword, weight, count))
                for elem in match_kw.get(cls, []):
                    total_matched_count += elem[2]
                    total_matched_score += elem[1] * elem[2]
                if total_matched_score and total_matched_score:
                    avg_score = total_matched_score / total_matched_count
                    if avg_score > self.threshold:
                        _result_label.append(cls)
            matched_keyword.append(match_kw)
            if self.na_tag and len(_result_label) == 0:
                _result_label.append(self.na_tag)
            result_labels.append(_result_label)
        return result_labels, matched_keyword

    def eval(self, examples: List[InputExample], y_true):
        if isinstance(y_true[0], str):
            y_true = [[y] for y in y_true]
        if self.label_term_weights and self.mlb:
            predict_labels, first_matched_keyword = self.predict(examples)
            if isinstance(y_true[0], str):
                y_true = [[y] for y in y_true]
            y_true = self.mlb.transform(y_true)
            y_pred = self.mlb.transform(predict_labels)
            acc = accuracy_score(y_true=y_true, y_pred=y_pred)
            report = classification_report(y_true=y_true, y_pred=y_pred, output_dict=True, zero_division=1,
                                           target_names=self.mlb.classes)
            report['accuracy'] = acc
            return report
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

    def save(self):
        tmp_model_dir = MODEL_ROOT / self.model_dir_name
        if not tmp_model_dir.exists():
            tmp_model_dir.mkdir(parents=True, exist_ok=True)
        output_file = (tmp_model_dir / self.dict_file_name).__str__()
        # logger.debug()(output_file)
        with open(output_file, 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([self.DictHeaders.LABEL.value, self.DictHeaders.TERM.value, self.DictHeaders.WEIGHT.value])
            for label, term_weights in self.label_term_weights.items():
                for term, score in term_weights:
                    writer.writerow([label, term, score])
        return self.model_dir_name

    def load(self, label_term_weights: Dict[str, List[Tuple[str, float]]] = None):
        self.label_term_weights.clear()
        if label_term_weights is None:
            with open(self.model_dir_name / self.dict_file_name, newline='') as csv_file:
                for row in csv.DictReader(csv_file):
                    label: str = row.get(self.DictHeaders.LABEL.value)
                    term: str = row.get(self.DictHeaders.TERM.value)
                    weight: float = float(row.get(self.DictHeaders.WEIGHT.value))
                    self.label_term_weights[label].append((term, weight))
        else:
            self.label_term_weights = label_term_weights

        self.mlb = MultiLabelBinarizer(classes=list(self.label_term_weights.keys()))
        self.mlb.fit([[label] for label in list(self.label_term_weights.keys())])
        logger.debug(self.mlb.classes)

    def convert_feature(self, examples,
                        update_vectorizer=False,
                        max_features=10000, min_df=None, stop_words='english'):
        min_df = round(max_features * 0.005) if min_df is None else min_df
        logger.debug('min_df:', min_df)
        seg_contents = []
        for example in examples:
            content = getattr(example, self.feature.value)
            if self.feature in {Features.CONTENT, Features.TITLE}:
                sentence = jieba.cut(str(content), cut_all=True)
            elif self.feature in {Features.AUTHOR, }:
                sentence = list(content)
            else:
                raise ValueError(f"Unavailable feature type {self.feature}")
            seg_contents.append(" ".join(sentence))

        if update_vectorizer:
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(max_features=max_features, min_df=min_df, stop_words=stop_words)
            x_features = self.vectorizer.fit_transform(seg_contents)
        else:
            if self.vectorizer:
                x_features = self.vectorizer.transform(seg_contents)
            else:
                raise ValueError("模型尚未被初始化，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")
        return x_features


def class_feature_importance(x, y, feature_list, use_scaler=True) -> Dict[str, List[Tuple[str, float]]]:
    clf = SGDClassifier(loss='log', penalty='elasticnet', l1_ratio=0.9, learning_rate='optimal', n_iter_no_change=10,
                        shuffle=True, n_jobs=3, fit_intercept=True, class_weight='balanced')
    clf.fit(x, y)
    label_fea_importance = {}
    if len(clf.classes_) == 2:
        clf.classes_ = [clf.classes_[1], clf.classes_[0]]
    for label_idx, importance in enumerate(clf.coef_):
        if use_scaler:
            from sklearn.preprocessing import MinMaxScaler
            # from sklearn.preprocessing import MaxAbsScaler
            scaler = MinMaxScaler()
            importance = scaler.fit_transform([[i_] for i_ in importance])
            importance = [i_[0] for i_ in importance]
        feature_importance = [(feature, round(importance, 5)) for feature, importance in
                              zip(feature_list, importance)]
        feature_importance = sorted(feature_importance, key=lambda x_: x_[1], reverse=True)
        label_fea_importance[clf.classes_[label_idx]] = feature_importance
    return label_fea_importance


if __name__ == '__main__':
    test_file = Path('/Users/liaoweifan/Downloads/sample_data/train.csv')
    examples = []
    model_dir = settings.BASE_DIR / settings.MODEL_PATH_FIELD_DIRECTORY
    with open(test_file, 'r') as f:
        for _id, row in enumerate(csv.DictReader(f, dialect=csv.QUOTE_ALL, delimiter='\t')):
            # logger.debug()(row)
            examples.append(InputExample(id_=str(_id), **row))
    y_true = [example.label for example in examples]
    model = TermWeightModel(model_dir_name=model_dir / 'test', na_tag='一般')
    model.fit(examples, y_true)
    logger.debug(examples[1].content)
    logger.debug(model.predict(examples)[0][1])
    logger.debug(model.predict(examples)[1][1])
    logger.debug(model.eval(examples, y_true))
