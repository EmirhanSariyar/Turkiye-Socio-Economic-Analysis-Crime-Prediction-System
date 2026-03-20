from sklearn.metrics import accuracy_score, f1_score


def evaluate_classification(y_true, y_pred) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_score": f1_score(y_true, y_pred),
    }
