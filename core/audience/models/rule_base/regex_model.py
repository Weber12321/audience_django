from core.audience.models.base_model import AudienceModel


class RegexModel(AudienceModel):
    def __init__(self):
        super().__init__()
        print("RuleModel")
        raise NotImplementedError

    def predict(self, content):
        raise NotImplementedError
