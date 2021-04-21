from core.audience.models.base_model import AudienceModel


class RandomForestModel(AudienceModel):

    def __init__(self, model_dir_name):
        super().__init__(model_dir_name=model_dir_name)
        print(self.__name__)
        raise NotImplementedError

    def fit(self, contents, y_true):
        pass

    def predict(self, contents):
        raise NotImplementedError

    def eval(self, contents, y_true):
        pass

    def save(self):
        pass

    def load(self):
        pass
