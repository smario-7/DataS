import os
from typing import Optional, List

import pandas as pd

from app.core.config import settings


def datasets_dir() -> str:
    return os.path.join(settings.storage_dir, "datasets")


def ensure_dirs() -> None:
    os.makedirs(datasets_dir(), exist_ok=True)


def dataset_path(dataset_id: str) -> Optional[str]:
    ensure_dirs()
    base = os.path.join(datasets_dir(), dataset_id)
    candidates = [f"{base}.parquet", f"{base}.csv"]
    for p in candidates:
        if os.path.exists(p):
            return p
    
    # Fallback: sprawdź w oryginalnej lokalizacji data/ (dla kompatybilności)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(project_root, "data")
    if os.path.exists(data_dir):
        fallback_base = os.path.join(data_dir, dataset_id)
        fallback_candidates = [f"{fallback_base}.parquet", f"{fallback_base}.csv"]
        for p in fallback_candidates:
            if os.path.exists(p):
                return p
    
    return None


def load_dataset(dataset_id: str) -> pd.DataFrame:
    path = dataset_path(dataset_id)
    if path is None:
        raise FileNotFoundError(f"Dataset not found: {dataset_id}")
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def save_dataset(dataset_id: str, df: pd.DataFrame, fmt: str = "parquet") -> str:
    ensure_dirs()
    base = os.path.join(datasets_dir(), dataset_id)
    if fmt == "csv":
        path = f"{base}.csv"
        df.to_csv(path, index=False)
        return path
    path = f"{base}.parquet"
    df.to_parquet(path, index=False)
    return path


def list_datasets() -> List[str]:
    ensure_dirs()
    ids: List[str] = []
    for name in os.listdir(datasets_dir()):
        if name.endswith(".csv") or name.endswith(".parquet"):
            ds_id = os.path.splitext(name)[0]
            ids.append(ds_id)
    ids.sort()
    return ids



