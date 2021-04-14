from core.audience.models.base_model import AudienceModel


class KeywordModel(AudienceModel):
    def __init__(self, model_dir_path):
        super().__init__(model_dir_path=model_dir_path)
        print(self.__name__)
        raise NotImplementedError

    def fit(self, contents, y_true):
        raise NotImplementedError

    def predict(self, contents):
        raise NotImplementedError

    def eval(self, contents, y_true):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError
