from typing import Dict, Any, List

import pandas as pd

from app.models.schemas import PrepareRequest, PrepareResponse
from app.services.artifacts import load_dataset


def auto_clean_dataframe(df_input: pd.DataFrame):
    import numpy as np
    from typing import Tuple

    log: List[Dict[str, Any]] = []
    dfc = df_input.copy()

    def add_log(step: str, before_shape, after_shape, affected_columns=None, notes: str = "") -> None:
        log.append({
            'step': step,
            'before_shape': list(before_shape),
            'after_shape': list(after_shape),
            'affected_columns': affected_columns or [],
            'notes': notes
        })

    before = dfc.shape
    cols_before = list(dfc.columns)
    new_cols = []
    seen = set()
    for c in cols_before:
        nc = str(c).strip()
        nc = nc.replace("\n", " ").replace("\t", " ")
        nc = nc.replace(" ", "_")
        nc = ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in nc)
        if not nc:
            nc = "col"
        orig_nc = nc
        i = 1
        while nc in seen:
            nc = f"{orig_nc}_dup{i}"
            i += 1
        seen.add(nc)
        new_cols.append(nc)
    dfc.columns = new_cols
    empty_cols = [c for c in dfc.columns if dfc[c].isna().all()]
    if empty_cols:
        dfc = dfc.drop(columns=empty_cols)
    add_log("normalize_columns", before, dfc.shape, affected_columns=empty_cols, notes="Kolumny znormalizowane; usunięto całe puste")

    before = dfc.shape
    placeholders = {"", "NA", "N/A", "na", "n/a", "NULL", "Null", "null", "None", "-", "?", "nan", "NaN"}
    affected: List[str] = []
    for c in dfc.columns:
        if dfc[c].dtype == object:
            if not dfc[c].isna().all():
                mask = dfc[c].isin(placeholders)
                if mask.any():
                    dfc.loc[mask, c] = np.nan
                    affected.append(c)
    add_log("unify_missing_tokens", before, dfc.shape, affected_columns=affected)

    before = dfc.shape
    converted_dates: List[str] = []
    converted_nums: List[str] = []
    marked_cats: List[str] = []
    for c in list(dfc.columns):
        s = dfc[c]
        if s.dtype == object:
            try:
                s_dt = pd.to_datetime(s, errors='coerce', infer_datetime_format=True)
                ratio = s_dt.notna().mean()
                if ratio >= 0.8:
                    dfc[c] = s_dt
                    converted_dates.append(c)
                    continue
            except Exception:
                pass
            try:
                s_num = pd.to_numeric(s, errors='coerce')
                ratio = s_num.notna().mean()
                if ratio >= 0.8:
                    dfc[c] = s_num
                    converted_nums.append(c)
            except Exception:
                pass
        if dfc[c].dtype == object:
            nun = dfc[c].nunique(dropna=True)
            if len(dfc) > 0 and (nun / max(len(dfc), 1)) < 0.5:
                try:
                    dfc[c] = dfc[c].astype('category')
                    marked_cats.append(c)
                except Exception:
                    pass
    add_log("type_conversions", before, dfc.shape, affected_columns=converted_dates + converted_nums + marked_cats,
            notes=f"dates={len(converted_dates)}, nums={len(converted_nums)}, cats={len(marked_cats)}")

    before = dfc.shape
    drop_cols: List[str] = []
    for c in list(dfc.columns):
        miss_ratio = dfc[c].isna().mean()
        if miss_ratio > 0.95:
            drop_cols.append(c)
    if drop_cols:
        dfc = dfc.drop(columns=drop_cols)
    if dfc.shape[1] > 0:
        row_miss = dfc.isna().mean(axis=1)
        to_drop_idx = row_miss[row_miss > 0.95].index
        if len(to_drop_idx) > 0:
            dfc = dfc.drop(index=to_drop_idx)
    for c in dfc.columns:
        s = dfc[c]
        if pd.api.types.is_numeric_dtype(s):
            skew_val = float(s.dropna().skew()) if s.dropna().size > 0 else 0.0
            fill_val = s.median() if abs(skew_val) > 1.0 else s.mean()
            dfc[c] = s.fillna(fill_val)
        elif pd.api.types.is_datetime64_any_dtype(s):
            dfc[c] = s.fillna(method='ffill').fillna(method='bfill')
        else:
            if s.isna().any():
                if s.dropna().size > 0:
                    try:
                        mode_val = s.mode(dropna=True).iloc[0]
                    except Exception:
                        mode_val = "__MISSING__"
                else:
                    mode_val = "__MISSING__"
                dfc[c] = s.fillna(mode_val)
    add_log("missing_handling", before, dfc.shape, affected_columns=drop_cols)

    before = dfc.shape
    clipped_cols: List[str] = []
    for c in dfc.columns:
        s = dfc[c]
        if pd.api.types.is_numeric_dtype(s):
            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            iqr = q3 - q1
            if pd.notna(iqr) and iqr > 0:
                low = q1 - 1.5 * iqr
                high = q3 + 1.5 * iqr
                dfc[c] = s.clip(lower=low, upper=high)
                clipped_cols.append(c)
    add_log("winsorize_outliers", before, dfc.shape, affected_columns=clipped_cols)

    before = dfc.shape
    low_info_cols = [c for c in dfc.columns if dfc[c].nunique(dropna=True) <= 1]
    if low_info_cols:
        dfc = dfc.drop(columns=low_info_cols)
    before_rows = dfc.shape
    dfc = dfc.drop_duplicates()
    add_log("deduplicate_low_info", before, dfc.shape, affected_columns=low_info_cols,
            notes=f"removed_dup_rows={before_rows[0]-dfc.shape[0]}")

    before = dfc.shape
    rare_applied: List[str] = []
    for c in dfc.columns:
        s = dfc[c]
        if hasattr(s, 'cat') or (s.dtype == object):
            vc = s.value_counts(dropna=True, normalize=True)
            if len(vc) > 20:
                rare = vc[vc < 0.01].index
                if len(rare) > 0:
                    rare_set = set(rare)
                    dfc[c] = s.apply(lambda x: "__OTHER__" if x in rare_set else x)
                    rare_applied.append(c)
    add_log("rare_categories", before, dfc.shape, affected_columns=rare_applied)

    num_cols = sum(pd.api.types.is_numeric_dtype(dfc[c]) for c in dfc.columns)
    dt_cols = sum(pd.api.types.is_datetime64_any_dtype(dfc[c]) for c in dfc.columns)
    cat_cols = len(dfc.columns) - num_cols - dt_cols
    avg_missing = float(dfc.isna().mean().mean()) if dfc.size else 0.0
    add_log("validation_summary", df_input.shape, dfc.shape,
            notes=f"num={num_cols}, dt={dt_cols}, cat={cat_cols}, avg_missing={avg_missing:.3f}")

    return dfc, log


def auto_clean_service(req: PrepareRequest) -> PrepareResponse:
    df = load_dataset(req.datasetId)
    cleaned, prep_log = auto_clean_dataframe(df)
    preview_rows = cleaned.head(50)
    preview = {
        "columns": list(preview_rows.columns),
        "rows": preview_rows.to_dict(orient="records"),
        "shape": list(cleaned.shape),
    }
    return PrepareResponse(datasetId=req.datasetId, preview=preview, prepLog=prep_log)



