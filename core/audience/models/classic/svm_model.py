import os

import jieba
import joblib
import numpy as np
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from core.audience.models.base_model import AudienceModel
from core.helpers.data_helpers import DataHelper
from core.helpers.model_helpers import multiToBinarizerLabels, get_multi_accuracy
from modeling_jobs.models import ModelingJob


class SvmModel(AudienceModel):
    def __init__(self):
        super().__init__()
        self.dirname = os.path.dirname(__file__)

    def fit(self, content, labels, model_file_name):

        train_labels = []
        for y in labels:
            train_labels.append(y[0])
        y_train = train_labels
        x_train = []
        for c in content:
            x_train.append(' '.join(jieba.lcut(c)))

        vectorizer = TfidfVectorizer(max_features=5000, min_df=2, stop_words='english')
        x_train_features = vectorizer.fit_transform(x_train)
        SVCModel = svm.SVC(kernel='linear')
        SVCModel.fit(x_train_features, y_train)
        return self.save(model_file_name, SVCModel, vectorizer)

    def multi_fit(self, content, labels, modeling_job_id):
        x_train = []
        for c in content:
            x_train.append(' '.join(jieba.lcut(c)))

        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, min_df=2)

        x_train_features = vectorizer.fit_transform(x_train)
        y_train = multiToBinarizerLabels(labels)

        classifier = svm.SVC(kernel='linear')
        multi_target_model = OneVsRestClassifier(classifier)
        multi_svm_model = multi_target_model.fit(x_train_features, y_train)
        return self.save(modeling_job_id, multi_svm_model, vectorizer)

    def multiToBinarizerLabels(self, labels):

        label_list = []
        for label in labels:
            for l in label[0].split(','):
                if l not in label_list:
                    label_list.append(l)

        mlb = MultiLabelBinarizer()
        mlb.fit([label_list])
        trans_labels = []
        for label in labels:
            l = label[0].split(',')
            trans_labels.append(mlb.transform([l])[0])

        return np.array(trans_labels)

    def predict(self, content, labels, modeling_job_id):
        path = ModelingJob.objects.get(pk=modeling_job_id).model_path
        try:
            model = joblib.load(os.path.join(path, "model.pkl"))
            vectorizer = joblib.load(os.path.join(path, "vectorize.pkl"))
            x_pre = []
            for c in content:
                data = ' '.join(jieba.lcut(c))
                x_pre.append(data)
            y_pre = []
            for x in x_pre:
                data = vectorizer.transform([x])
                y_pre.append(model.predict(data)[0])
            report = classification_report(labels, y_pre, output_dict=True)
            dataHelper = DataHelper()
            dataHelper.save_report(modeling_job_id, report)
            return True
        except Exception as e:
            return e

    def predict_multi_label(self, content, labels, modeling_job_id):
        path = ModelingJob.objects.get(pk=modeling_job_id).model_path
        try:
            model = joblib.load(os.path.join(path, "model.pkl"))
            vectorizer = joblib.load(os.path.join(path, "vectorize.pkl"))
            x_pre = []
            for c in content:
                data = ' '.join(jieba.lcut(c))
                x_pre.append(data)

            labels = multiToBinarizerLabels(labels)
            y_pre = []
            for x in x_pre:
                data = vectorizer.transform([x])
                y_pre.append(model.predict(data)[0])

            acc = get_multi_accuracy(labels, y_pre)
            report = classification_report(labels, y_pre, output_dict=True)
            report['accuracy'] = acc
            dataHelper = DataHelper()
            dataHelper.save_report(modeling_job_id, report)
            return True
        except:
            return '請先訓練模型'
