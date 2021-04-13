from core.audience.models.base_model import AudienceModel


class TermWeightModel(AudienceModel):
    def __init__(self):
        super().__init__()
        print("ProbModel")
        raise NotImplementedError

    def predict(self, content):
        raise NotImplementedError
