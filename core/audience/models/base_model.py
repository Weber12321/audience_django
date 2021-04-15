from abc import abstractmethod, ABC
from pathlib import Path

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

    def __init__(self, model_dir_name=None, dummy_message="This is a DUMMY model."):
        super().__init__(model_dir_name)
        self.dummy_message = dummy_message

    def fit(self, contents, labels):
        pass

    def predict(self, content):
        result = f"{self.dummy_message} Your input is: '{content}'"
        return ("dummy_label 1", "dummy_label 3"), (0.99, 0.01)

    def eval(self, test_x, y_true):
        pass

    def save(self):
        pass

    def load(self):
        pass


if __name__ == '__main__':
    model = DummyModel()
    print(model.predict(""))
