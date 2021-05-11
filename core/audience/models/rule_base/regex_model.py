import re
from typing import Dict, Optional, List

from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer

from core.audience.models.base_model import RuleBaseModel
from core.dao.input_example import Features, InputExample


class RegexModel(RuleBaseModel):
    def __init__(self, model_dir_name, feature=Features.CONTENT, na_tag=None, **kwargs):
        super().__init__(model_dir_name=model_dir_name, feature=feature, na_tag=na_tag, **kwargs)
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.patterns: Optional[Dict] = None

    def predict(self, examples: List[InputExample]):
        if not self.patterns:
            raise ValueError(f"模型尚未被讀取，請嘗試執行 ' load() ' 方法讀取模型。")
        first_matched_keyword = []
        result_labels = []
        for example in examples:
            content = getattr(example, self.feature.value)
            match_pattern = {}
            for cls, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        match_pattern[cls] = pattern
                        break
            first_matched_keyword.append(match_pattern)
            result_labels.append(list(match_pattern.keys()))
        return result_labels, first_matched_keyword

    def eval(self, examples: List[InputExample], y_true):
        for index, y in enumerate(y_true):
            y_true[index] = y

        if self.patterns and self.mlb:
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

    def load(self, rules: Dict[str, List[str]]):
        self.patterns = rules
        self.mlb = MultiLabelBinarizer(classes=list(rules.keys()))
        self.mlb.fit([[label] for label in list(rules.keys())])
        print(self.mlb.classes)


if __name__ == '__main__':
    rg = RegexModel('')
    print(rg.__class__.__base__)
    test_rules = {
        "male": [".弟我.+"],
        "female": ["小妹我"],
        "married": ["我.{,3}老婆"]
    }
    rg.load(test_rules)
    print(rg.predict([
        InputExample(content="小弟我今天很棒"),
        InputExample(content="小妹我今天很棒"),
        InputExample(content="小弟我老婆今天很棒"),
    ]))
    print(rg.eval(examples=[
        InputExample(content="小弟我今天很棒"),
        InputExample(content="小妹我今天很棒"),
        InputExample(content="小弟我美麗的老婆今天很棒"),
    ], y_true=[["male"], ["female"], ["male", "married"]]))
