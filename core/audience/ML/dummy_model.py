from core.audience.ML.base_model import AudienceModel


class DummyModel(AudienceModel):
    """
    用於測試流程的假模型，無需訓練與輸入，直接使用即可。
    """

    def __init__(self, dummy_message="This is a DUMMY model."):
        super().__init__()
        self.dummy_message = dummy_message

    def predict(self, content):
        result = f"{self.dummy_message} Your input is: '{content}'"
        return ("dummy_label 1", "dummy_label 3"), (0.99, 0.01)


if __name__ == '__main__':
    model = DummyModel()
    print(model.predict(""))
