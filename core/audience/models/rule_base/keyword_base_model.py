from core.audience.models.base_model import AudienceModel


class KeywordModel(AudienceModel):
    def __init__(self):
        super().__init__()
        print("KeywordModel")
        raise NotImplementedError

    def predict(self, content):
        raise NotImplementedError
