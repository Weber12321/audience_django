from core.audience.models.base_model import AudienceModel


class RandomForestModel(AudienceModel):
    def __init__(self):
        super().__init__()
        print("RFModel")
        raise NotImplementedError

    def predict(self, content):
        raise NotImplementedError
