from enum import Enum
from typing import Dict, Optional, List, Tuple

from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer

from core.audience.models.base_model import RuleBaseModel
from core.dao.input_example import Features, InputExample


class MatchType(Enum):
    START = 'start'
    END = 'end'
    EXACTLY = 'exactly'
    ABSOLUTELY = 'absolutely'
    PARTIALLY = 'partially'


class KeywordModel(RuleBaseModel):

    def __init__(self, model_dir_name, feature=Features.CONTENT, na_tag=None, **kwargs):
        super().__init__(model_dir_name=model_dir_name, feature=feature, na_tag=na_tag, **kwargs)
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.rules: Optional[Dict[str, List[Tuple[str, MatchType]]]] = None

    def predict(self, examples: List[InputExample]):
        if not self.rules:
            raise ValueError(f"模型尚未被讀取，請嘗試執行 ' load() ' 方法讀取模型。")
        first_matched_keyword = []
        result_labels = []
        for example in examples:
            content: str = getattr(example, self.feature.value)
            match_kw = {}
            if content:
                for cls, keywords in self.rules.items():
                    for keyword, match_type in keywords:

                        try:
                            _match_type = match_type if isinstance(match_type, MatchType) else MatchType(match_type)
                        except Exception as e:
                            print(e, match_type)
                            continue
                        if _match_type == MatchType.PARTIALLY:
                            if content.__contains__(keyword):
                                match_kw[cls] = (keyword, _match_type.value)
                                break
                        elif _match_type == MatchType.START:
                            if content.startswith(keyword):
                                match_kw[cls] = (keyword, _match_type.value)
                                break
                        elif _match_type == MatchType.END:
                            if content.endswith(keyword):
                                match_kw[cls] = (keyword, _match_type.value)
                                break
                        elif _match_type in [MatchType.EXACTLY, MatchType.ABSOLUTELY]:
                            if content == keyword:
                                match_kw[cls] = (keyword, _match_type.value)
                                break
                        else:
                            continue

            first_matched_keyword.append(match_kw)
            result_labels.append(list(match_kw.keys()))
        return result_labels, first_matched_keyword

    def eval(self, examples: List[InputExample], y_true):
        for index, y in enumerate(y_true):
            y_true[index] = y

        if self.rules and self.mlb:
            predict_labels, first_matched_keyword = self.predict(examples)
            y_true = self.mlb.transform(y_true)
            y_pred = self.mlb.transform(predict_labels)
            acc = accuracy_score(y_true=y_true, y_pred=y_pred)
            report = classification_report(y_true=y_true, y_pred=y_pred, output_dict=True, zero_division=1,
                                           target_names=self.mlb.classes)
            report['accuracy'] = acc
            return report
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

    def save(self):
        raise NotImplementedError

    def load(self, rules: Dict[str, List[Tuple[str, MatchType]]]):
        self.rules = rules
        self.mlb = MultiLabelBinarizer(classes=list(rules.keys()))
        self.mlb.fit([[label] for label in list(rules.keys())])
        print(self.mlb.classes)


if __name__ == '__main__':
    kw_cls = KeywordModel
    print(kw_cls, kw_cls.__class__.__base__, kw_cls.__name__)
    kw = kw_cls('')
    print(kw.__class__.__base__)
    test_rules = {"male": [("小弟我", MatchType.START)], "female": [("小妹我", MatchType.PARTIALLY)],
                  "married": [("我老婆", MatchType.PARTIALLY)]}
    kw.load(test_rules)
    print(kw.predict([
        InputExample(content="小弟我今天很棒"),
        InputExample(content="小妹我今天很棒"),
        InputExample(content="小弟我老婆今天很棒"),
    ]))
    print(kw.eval(examples=[
        InputExample(content="小弟我今天很棒"),
        InputExample(content="小妹我今天很棒"),
        InputExample(content="小弟我老婆今天很棒"),
    ], y_true=[["male"], ["female"], ["male", "married"]]))
