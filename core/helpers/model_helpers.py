import os

import jieba
import joblib
import numpy as np
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
# from xgboost import XGBClassifier

from audience_toolkits import settings
from core.helpers.data_helpers import DataHelper
from modeling_jobs.models import ModelingJob


def save(self, modeling_job_id, model, vectorizer):
    if not os.path.exists(settings.MODEL_PATH_FIELD_DIRECTORY):
        os.mkdir(settings.MODEL_PATH_FIELD_DIRECTORY)
    path = os.path.join(settings.MODEL_PATH_FIELD_DIRECTORY, f'modeling_job_id_{modeling_job_id}')
    if not os.path.exists(path):
        os.mkdir(path)
    SVCModelPath = os.path.join(path, 'model.pkl')
    vectorizerSVMPath = os.path.join(path, 'vectorize.pkl')
    joblib.dump(model, SVCModelPath)

    joblib.dump(vectorizer, vectorizerSVMPath)
    return os.path.join(settings.MODEL_PATH_FIELD_DIRECTORY, f'modeling_job_id_{modeling_job_id}')









def get_multi_accuracy(y_true, y_pre):
    right = 0
    wrong = 0
    for i in range(len(y_true)):
        for j in range(len(y_true[i])):
            if y_true[i][j] == y_pre[i][j]:
                right += 1
            else:
                wrong += 1
    return right / (right + wrong)


def multiToBinarizerLabels(labels):
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


