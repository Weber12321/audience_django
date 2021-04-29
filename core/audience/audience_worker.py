from collections import namedtuple, defaultdict
from typing import Dict, List, Generator, Tuple

from typing import Iterable

from core.audience.models.base_model import SuperviseModel
from core.dao.input_example import InputExample
from core.helpers.log_helper import get_logger

RESULT = namedtuple("Result", "labels, logits, model, feature, value")


class AudienceWorker:
    def __init__(self, model_list: List[SuperviseModel], logger=None):
        if logger is None:
            self.logger = get_logger(context="AudienceWorker")
        else:
            self.logger = logger

        self.models: List[SuperviseModel] = model_list

    def run_labeling(self, input_examples: List[InputExample]) -> List[List[RESULT]]:
        """

        :param input_examples:
        :return: list of models-> list of label results -> label, score
        """
        model_predicted_result = [[] for i in range(len(input_examples))]
        for audience_model in self.models:
            predict_labels, predict_logits = audience_model.predict(input_examples)
            for i, example in enumerate(input_examples):
                model_predicted_result[i].append(
                    RESULT(labels=predict_labels[i], logits=predict_logits[i],
                           model=audience_model.model_dir_name.__str__(),
                           feature=audience_model.feature.value, value=getattr(example, audience_model.feature.value)))
        return model_predicted_result

    @staticmethod
    def ensemble_results(predicting_results: List[RESULT], bypass_same_label=True) \
            -> Tuple[Dict[str, float], Dict[str, List[RESULT]]]:
        """
        :param predicting_results: list of models-> list of label results -> label, score
        :param bypass_same_label: True 先預測先贏，只保留第一個預測到的分數； False 加總所有預測到的分數
        :return: 回傳最終統整完的標籤名稱與分數，以及預測路徑（模型先後順序），這邊的標籤將喪失關聯
        """
        ensemble_results = defaultdict(float)
        apply_path = defaultdict(list)
        for result in predicting_results:
            logits_dict = {cls: logit for cls, logit in result.logits}
            if isinstance(result.labels, str):
                labels = [result.labels]
            else:
                labels = result.labels
            for label in labels:
                if not bypass_same_label:
                    ensemble_results[label] = ensemble_results.get(label, 0) + logits_dict.get(label, 0)
                    apply_path[label].append(result._asdict())
                else:
                    ensemble_results[label] = logits_dict.get(label, 0)
                    apply_path[label] = [result._asdict()]
        return ensemble_results, apply_path
