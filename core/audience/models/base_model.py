from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Tuple, Iterable

from sklearn.metrics import classification_report

from audience_toolkits import settings
from core.dao.input_example import InputExample, Features

MODEL_ROOT = Path(settings.MODEL_PATH_FIELD_DIRECTORY)


class AudienceModel(ABC):
    """
    此模型為分類器類型，主要用於依據特徵分類，並輸出類別與機率值（或分數）。
    注意：若有不同類型的模型或輸出方式，請另外設計不同的Interface並繼承之。
    """

    def __init__(self, model_dir_name: str, feature: Features = Features.CONTENT):
        self.model = None
        self.model_dir_name = Path(model_dir_name)
        self.feature = feature if isinstance(feature, Features) else Features(feature)

    @abstractmethod
    def fit(self, examples: Iterable[InputExample], y_true):
        raise NotImplementedError

    @abstractmethod
    def predict(self, examples: Iterable[InputExample]) -> List[Tuple[Tuple]]:
        """
        回傳每個example的結果 用((label_1, probability or score), (label_2, probability or score)...)
        請統一格式，供下游程式使用。
        注意：若有不同類型的模型或輸出方式，請另外設計不同的Interface並繼承之。
        :param examples:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def eval(self, examples: Iterable[InputExample], y_true):
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

    def __init__(self, model_dir_name="DummyModel", dummy_message="This is a DUMMY model.", is_multi_label=False,
                 feature: Features = Features.CONTENT):
        super().__init__(model_dir_name, feature=feature)
        self.dummy_message = dummy_message
        self.is_multi_label = is_multi_label

    def fit(self, examples: Iterable[InputExample], y_true):
        return self.save()

    def predict(self, examples: Iterable[InputExample]):
        contents = [getattr(example, self.feature.value) for example in examples]
        if self.is_multi_label:
            return [(("dummy_label", 1.0), ("dummy label 2", 0.8)) for content in contents]
        else:
            return [(("dummy_label", 0.6), ("dummy label 2", 0.3), ("dummy label 2", 0.1)) for content in contents]

    def eval(self, examples: Iterable[InputExample], y_true):
        report = classification_report(y_true, y_true, output_dict=True)
        return report

    def save(self):
        return MODEL_ROOT

    def load(self):
        pass


if __name__ == '__main__':
    model = DummyModel()
    print(model.predict(""))
