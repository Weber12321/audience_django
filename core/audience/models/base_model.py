from abc import abstractmethod, ABC
from pathlib import Path

from sklearn.metrics import classification_report

from audience_toolkits import settings

MODEL_ROOT = Path(settings.MODEL_PATH_FIELD_DIRECTORY)


class AudienceModel(ABC):
    def __init__(self, model_dir_name: str):
        self.model = None
        self.model_dir_name = Path(model_dir_name)

    @abstractmethod
    def fit(self, contents, y_true):
        raise NotImplementedError

    @abstractmethod
    def predict(self, contents):
        raise NotImplementedError

    @abstractmethod
    def eval(self, contents, y_true):
        raise NotImplementedError

    @abstractmethod
    def save(self):
        raise NotImplementedError

    @abstractmethod
    def load(self):
        raise NotImplementedError


class DummyModel(AudienceModel):
    """
    用於測試流程的假模型，無需訓練與輸入，直接使用即可。
    """

    def __init__(self, model_dir_name="DummyModel", dummy_message="This is a DUMMY model."):
        super().__init__(model_dir_name)
        self.dummy_message = dummy_message

    def fit(self, contents, y_true):
        return self.save()

    def predict(self, content):
        result = f"{self.dummy_message} Your input is: '{content}'"
        return ("dummy_label 1", "dummy_label 3"), (0.99, 0.01)

    def eval(self, contents, y_true):
        report = classification_report(y_true, y_true, output_dict=True)
        return report

    def save(self):
        return MODEL_ROOT

    def load(self):
        pass


if __name__ == '__main__':
    model = DummyModel()
    print(model.predict(""))
