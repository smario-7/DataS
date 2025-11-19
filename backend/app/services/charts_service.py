import json
import os
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
import joblib

from app.core.config import settings
from app.services.artifacts import load_dataset


def _model_dir(model_id: str) -> str:
    return os.path.join(settings.storage_dir, "models", model_id)


def feature_importance_series(model_id: str) -> Dict[str, Any]:
    model_dir = _model_dir(model_id)
    with open(os.path.join(model_dir, "meta.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    dataset_id = meta["datasetId"]
    target = meta["target"]

    pipe = joblib.load(os.path.join(model_dir, "model.pkl"))
    df = load_dataset(dataset_id)
    df = df.dropna(subset=[target])
    y = df[target]
    X = df.drop(columns=[target])

    prep = pipe.named_steps["prep"]
    # Ensure fitted
    pipe.fit(X, y)

    # feature names after transform
    num_names = prep.transformers_[0][2]
    cat_enc = prep.transformers_[1][1]
    cat_names = prep.transformers_[1][2]
    try:
        cat_ohe_names = list(cat_enc.get_feature_names_out(cat_names))
    except Exception:
        cat_ohe_names = [f"{cat_names[i]}_{j}" for i in range(len(cat_names)) for j in range(1)]
    feature_names = list(num_names) + list(cat_ohe_names)

    result = permutation_importance(pipe, X, y, n_repeats=5, random_state=42, scoring=None)
    mean = result.importances_mean
    std = result.importances_std
    order = np.argsort(-mean)
    series: List[Dict[str, Any]] = []
    for idx in order:
        if idx >= len(feature_names):
            continue
        series.append({"name": feature_names[idx], "importance": float(mean[idx]), "std": float(std[idx])})
    return {"modelId": model_id, "series": series}



