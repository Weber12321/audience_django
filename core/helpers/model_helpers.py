import importlib
from pathlib import Path

import joblib

from audience_toolkits import settings


def get_multi_accuracy(y_true, y_pre):
    right = 0
    wrong = 0
    for i in range(len(y_true)):
        for j in range(len(y_true[i])):
            if y_true[i][j].all(y_pre[i][j]):
                right += 1
            else:
                wrong += 1
    return right / (right + wrong)


def load_joblib(path: Path):
    if path.exists():
        return joblib.load(path)
    else:
        raise FileNotFoundError(f"{path.__str__()} not found. Please train your model first.")


def get_model_class(name: str):
    """
    藉由settings中的ML_MODELS的設定讀取機器學習模型模組
    :param name: 設定中的模組名稱
    :return: AudienceModel Class
    """
    mod_path, class_name = settings.ML_MODELS.get(name).get('module').rsplit(sep='.', maxsplit=1)
    return getattr(importlib.import_module(mod_path), class_name)
