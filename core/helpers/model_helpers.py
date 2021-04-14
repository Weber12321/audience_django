from pathlib import Path
import joblib


def get_multi_accuracy(y_true, y_pre):
    right = 0
    wrong = 0
    for i in range(len(y_true)):
        for j in range(len(y_true[i])):
            if y_true[i][j] == y_pre[i][j]:
                right += 1
            else:
                wrong += 1
    return right / (right + wrong)


def load_joblib(path: Path):
    if path.exists():
        return joblib.load(path)
    else:
        raise FileNotFoundError(f"{path.__str__()} not found. Please train your model first.")
