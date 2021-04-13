from collections import namedtuple
from typing import Dict, List

from typing import Iterable

from core.audience.models.base_model import AudienceModel
from core.dao.input_example import InputExample
from core.helpers.log_helper import get_logger

RESULT = namedtuple("Result", "label, score")


class AudienceWorker:
    def __init__(self, model_list: List[AudienceModel], logger=None):
        if logger is None:
            self.logger = get_logger(context="AudienceWorker")
        else:
            self.logger = logger

        self.models: List[AudienceModel] = model_list

    def run(self, input_examples: Iterable[InputExample]):
        for example in input_examples:
            yield self.run_labeling(example)

    def run_labeling(self, doc: InputExample) -> List[List[RESULT]]:
        """

        :param doc:
        :return: list of models-> list of label results -> label, score
        """
        results = []
        for audience_model in self.models:
            labels, logits = audience_model.predict([doc])
            rs_list = [RESULT(*rs) for rs in zip(labels, logits)]
            results.append(rs_list)
        return results

    @staticmethod
    def ensemble_results(predicting_results: List[List[RESULT]], bypass_same_label=False) -> Dict[str, float]:
        """
        
        :param predicting_results: list of models-> list of label results -> label, score
        :param bypass_same_label: if False -> sum of scores of each label, else -> use first score of each label
        :return: dictionary of each label and score {label: score}
        """
        ensemble_results = {}
        for model_result in predicting_results:
            for rs in model_result:
                if not bypass_same_label:
                    ensemble_results[rs.label] = ensemble_results.get(rs.label, 0) + rs.score
                else:
                    if rs.label not in ensemble_results:
                        ensemble_results[rs.label] = rs.score
        return ensemble_results
