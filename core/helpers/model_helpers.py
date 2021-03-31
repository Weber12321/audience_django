from abc import ABC, abstractmethod

class AudienceModel(ABC):
    def __init__(self, model_type):
        pass

    @abstractmethod
    def predict(self,content):
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
    def predict(self,content):
        pass
class SvmModel(AudienceModel):
    def __init__(self):
        print("SvmModel")
    def fit(self):
        print("fit svm")
    def predict(self,content):
        pass

class XgboostModel(AudienceModel):
    def __init__(self):
        print("XgboostModel")
    def predict(self,content):
        pass