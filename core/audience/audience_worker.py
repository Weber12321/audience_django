from collections import namedtuple
from typing import Dict, List, Generator

from typing import Iterable

from core.audience.models.base_model import AudienceModel
from core.dao.input_example import InputExample
from core.helpers.log_helper import get_logger

RESULT = namedtuple("Result", "labels, logits")


class AudienceWorker:
    def __init__(self, model_list: List[AudienceModel], logger=None):
        if logger is None:
            self.logger = get_logger(context="AudienceWorker")
        else:
            self.logger = logger

        self.models: List[AudienceModel] = model_list

    def run_labeling(self, input_examples: List[InputExample]) -> List[List[RESULT]]:
        """

        :param input_examples:
        :return: list of models-> list of label results -> label, score
        """
        model_predicted_result = [[] for i in range(len(input_examples))]
        for audience_model in self.models:
            predict_labels, predict_logits = audience_model.predict(input_examples)
            for i in range(len(input_examples)):
                model_predicted_result[i].append(RESULT(predict_labels[i], predict_logits[i]))
        return model_predicted_result

    @staticmethod
    def ensemble_results(predicting_results: List[RESULT], bypass_same_label=False) -> Dict[str, float]:
        """
        
        :param predicting_results: list of models-> list of label results -> label, score
        :param bypass_same_label: if False -> sum of scores of each label, else -> use first score of each label
        :return: dictionary of each label and score {label: score}
        """
        ensemble_results = {}
        for result in predicting_results:
            logits_dict = {cls: logit for cls, logit in result.logits}
            if isinstance(result.labels, str):
                labels = [result.labels]
            else:
                labels = result.labels
            for label in labels:
                if not bypass_same_label:
                    ensemble_results[label] = ensemble_results.get(label, 0) + logits_dict.get(label, 0)
                else:
                    ensemble_results[label] = logits_dict.get(label, 0)
        return ensemble_results
