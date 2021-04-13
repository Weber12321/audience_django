# import os
#
# import jieba
# import joblib
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics import classification_report
# from sklearn.multiclass import OneVsRestClassifier
#
# from core.audience.models.base_model import AudienceModel
# from core.helpers.data_helpers import DataHelper
# from core.helpers.model_helpers import multiToBinarizerLabels, get_multi_accuracy
#
#
# class XgboostModel(AudienceModel):
#     def __init__(self):
#         self.dirname = os.path.dirname(__file__)
#
#     def fit(self, content, labels, modeling_job_id):
#         train_labels = []
#         for y in labels:
#             train_labels.append(y[0])
#         y_train = train_labels
#         x_train = []
#         for c in content:
#             x_train.append(' '.join(jieba.lcut(c)))
#
#         vectorizer = TfidfVectorizer(max_features=5000, min_df=2, stop_words='english')
#         x_train_features = vectorizer.fit_transform(x_train)
#         xgboostModel = XGBClassifier(n_estimators=100, learning_rate=0.1)
#         xgboostModel.fit(x_train_features, y_train)
#         return self.save(modeling_job_id, xgboostModel, vectorizer)
#
#     def predict(self, content, labels, modeling_job_id):
#         path = ModelingJob.objects.get(pk=modeling_job_id).model_path
#         try:
#             model = joblib.load(os.path.join(path, "model.pkl"))
#             vectorizer = joblib.load(os.path.join(path, "vectorize.pkl"))
#             x_pre = []
#             for c in content:
#                 data = ' '.join(jieba.lcut(c))
#                 x_pre.append(data)
#             y_pre = []
#             for x in x_pre:
#                 data = vectorizer.transform([x])
#                 y_pre.append(model.predict(data)[0])
#             report = classification_report(labels, y_pre, output_dict=True)
#             dataHelper = DataHelper()
#             dataHelper.save_report(modeling_job_id, report)
#             return True
#         except:
#             return '請先訓練模型'
#
#     def multi_fit(self, content, labels, modeling_job_id):
#         x_train = []
#         for c in content:
#             x_train.append(' '.join(jieba.lcut(c)))
#
#         vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, min_df=2)
#
#         x_train_features = vectorizer.fit_transform(x_train)
#         y_train = multiToBinarizerLabels(labels)
#
#         classifier = XGBClassifier(n_estimators=100, learning_rate=0.1)
#         multi_target_model = OneVsRestClassifier(classifier)
#         multi_xgboost_model = multi_target_model.fit(x_train_features, y_train)
#         return self.save(modeling_job_id, multi_xgboost_model, vectorizer)
#
#     def predict_multi_label(self, content, labels, modeling_job_id):
#         path = ModelingJob.objects.get(pk=modeling_job_id).model_path
#         try:
#             model = joblib.load(os.path.join(path, "model.pkl"))
#             vectorizer = joblib.load(os.path.join(path, "vectorize.pkl"))
#             x_pre = []
#             for c in content:
#                 data = ' '.join(jieba.lcut(c))
#                 x_pre.append(data)
#
#             labels = multiToBinarizerLabels(labels)
#             y_pre = []
#             for x in x_pre:
#                 data = vectorizer.transform([x])
#                 y_pre.append(model.predict(data)[0])
#
#             acc = get_multi_accuracy(labels, y_pre)
#             report = classification_report(labels, y_pre, output_dict=True)
#
#             report['accuracy'] = acc
#             dataHelper = DataHelper()
#             dataHelper.save_report(modeling_job_id, report)
#             return True
#         except:
#             return '請先訓練模型'
