import os
import uuid
from typing import Dict, Any

import joblib
import pandas as pd
import json
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

from app.core.config import settings
from app.services.artifacts import load_dataset
from app.services.jobs import JobRecord


def _prepare_xy(df: pd.DataFrame, target: str):
    df_clean = df.dropna(subset=[target])
    y = df_clean[target]
    X = df_clean.drop(columns=[target])
    cat_cols = [c for c in X.columns if (not pd.api.types.is_numeric_dtype(X[c]))]
    num_cols = [c for c in X.columns if c not in cat_cols]
    return X, y, num_cols, cat_cols


def _build_transformer(num_cols, cat_cols) -> ColumnTransformer:
    num_tr = Pipeline(steps=[("imputer", SimpleImputer(strategy="median")),
                             ("scaler", StandardScaler(with_mean=False))])
    cat_tr = Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")),
                             ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer(transformers=[("num", num_tr, num_cols), ("cat", cat_tr, cat_cols)], remainder="drop")


def _train_regression(X, y, transformer) -> (Pipeline, Dict[str, float]):
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(random_state=42),
    }
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    best_pipe = None
    best_score = -1e9
    best_metrics: Dict[str, float] = {}
    for name, model in models.items():
        pipe = Pipeline([("prep", transformer), ("model", model)])
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        r2 = r2_score(y_te, pred)
        mae = mean_absolute_error(y_te, pred)
        rmse = root_mean_squared_error(y_te, pred)
        if r2 > best_score:
            best_score = r2
            best_pipe = pipe
            best_metrics = {"model": name, "R2": r2, "MAE": mae, "RMSE": rmse}
    return best_pipe, best_metrics


def _train_classification(X, y, transformer) -> (Pipeline, Dict[str, float]):
    y = y.astype("category")
    models = {
        "LogisticRegression": LogisticRegression(max_iter=200),
        "RandomForestClassifier": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced"),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(random_state=42),
    }
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    best_pipe = None
    best_score = -1e9
    best_metrics: Dict[str, float] = {}
    for name, model in models.items():
        pipe = Pipeline([("prep", transformer), ("model", model)])
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        acc = accuracy_score(y_te, pred)
        bal_acc = balanced_accuracy_score(y_te, pred)
        f1 = f1_score(y_te, pred, average="macro")
        if bal_acc > best_score:
            best_score = bal_acc
            best_pipe = pipe
            best_metrics = {"model": name, "balanced_accuracy": bal_acc, "accuracy": acc, "f1_macro": f1}
    return best_pipe, best_metrics


def _models_dir() -> str:
    path = os.path.join(settings.storage_dir, "models")
    os.makedirs(path, exist_ok=True)
    return path


def _save_model(pipe: Pipeline) -> str:
    model_id = str(uuid.uuid4())
    model_dir = os.path.join(_models_dir(), model_id)
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(pipe, os.path.join(model_dir, "model.pkl"))
    return model_id


def training_job(rec: JobRecord, dataset_id: str, target: str, problem_type: str) -> None:
    df = load_dataset(dataset_id)
    rec.progress = 0.1
    X, y, num_cols, cat_cols = _prepare_xy(df, target)
    rec.progress = 0.2
    transformer = _build_transformer(num_cols, cat_cols)
    rec.progress = 0.3
    if problem_type == "regresja":
        pipe, metrics = _train_regression(X, y, transformer)
    else:
        pipe, metrics = _train_classification(X, y, transformer)
    rec.progress = 0.8
    model_id = _save_model(pipe)
    rec.progress = 0.95
    rec.details = {"datasetId": dataset_id, "target": target, "problemType": problem_type, "metrics": metrics, "modelId": model_id}
    # save metadata
    model_dir = os.path.join(settings.storage_dir, "models", model_id)
    meta_path = os.path.join(model_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(rec.details, f, ensure_ascii=False, indent=2)
    rec.progress = 1.0


