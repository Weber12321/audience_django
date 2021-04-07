from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
from sklearn.metrics import classification_report,accuracy_score
import os
import joblib
import jieba
from pathlib import Path
from modeling_jobs.helpers.data_helpers import DataHelper
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
import numpy as np


class AudienceModel(ABC):
    def __init__(self, model_type):
        pass

    @abstractmethod
    def predict(self, content):
        pass

    def val(self, test_x, y_true):
        print("val")


class RuleModel(AudienceModel):
    def __init__(self):
        print("RuleModel")


class KeywordModel(AudienceModel):
    def __init__(self):
        print("KeywordModel")


class ProbModel(AudienceModel):
    def __init__(self):
        print("ProbModel")


class RFModel(AudienceModel):
    def __init__(self):
        print("RFModel")

    def predict(self, content):
        pass


class SvmModel(AudienceModel):
    def __init__(self):
        self.dirname = os.path.dirname(__file__)

    def fit(self, content, labels, modeling_job_id):

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
        self.save(modeling_job_id, SVCModel, vectorizer)

    def multi_fit(self, content, labels, modeling_job_id):
        x_train = []
        for c in content:
            x_train.append(' '.join(jieba.lcut(c)))

        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, min_df=2)

        x_train_features = vectorizer.fit_transform(x_train)
        y_train = self.multiToBinarizerLabels(labels)

        classifier = svm.SVC(kernel='linear')
        multi_target_model = OneVsRestClassifier(classifier)
        multi_svm_model = multi_target_model.fit(x_train_features, y_train)
        self.save(modeling_job_id,multi_svm_model,vectorizer)

    def multiToBinarizerLabels(self,labels):

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


    def save(self, modeling_job_id, SVCModel, vectorizer):
        path = os.path.join(self.dirname, f'..\\models\\modeling_job_id_{modeling_job_id}')
        if not os.path.exists(path):
            os.mkdir(path)
        SVCModelPath = os.path.join(path, 'model.pkl')
        vectorizerSVMPath = os.path.join(path, 'vectorize.pkl')
        joblib.dump(SVCModel, SVCModelPath)
        joblib.dump(vectorizer, vectorizerSVMPath)

    def predict(self, content, labels, modeling_job_id):
        path = Path(__file__).parent.parent / 'models' / f'modeling_job_id_{modeling_job_id}'
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
        except:
            return False

    def predict_multi_label(self, content, labels, modeling_job_id):
        path = Path(__file__).parent.parent / 'models' / f'modeling_job_id_{modeling_job_id}'
        try:
            model = joblib.load(os.path.join(path, "model.pkl"))
            vectorizer = joblib.load(os.path.join(path, "vectorize.pkl"))
            x_pre = []
            for c in content:
                data = ' '.join(jieba.lcut(c))
                x_pre.append(data)

            labels = self.multiToBinarizerLabels(labels)
            y_pre = []
            for x in x_pre:
                data = vectorizer.transform([x])
                y_pre.append(model.predict(data)[0])

            acc = get_multi_accuracy(labels,y_pre)
            report = classification_report(labels, y_pre, output_dict=True)
            report['accuracy'] = acc
            dataHelper = DataHelper()
            dataHelper.save_report(modeling_job_id, report)
            return True
        except:
            return False

def get_multi_accuracy(y_true,y_pre):
    right = 0
    wrong = 0
    for i in range(len(y_true)):
        for j in range(len(y_true[i])):
            if y_true[i][j] == y_pre[i][j]:
                right += 1
            else:
                wrong += 1
    return right / (right + wrong)

class XgboostModel(AudienceModel):
    def __init__(self):
        print("XgboostModel")

    def predict(self, content):
        pass
