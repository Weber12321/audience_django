from abc import abstractmethod, ABC


class AudienceModel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def predict(self, content):
        pass

    def eval(self, test_x, y_true):
        print("eval")
