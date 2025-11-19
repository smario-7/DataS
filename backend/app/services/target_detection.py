from typing import Any, Dict, List, Optional, Tuple
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from app.models.schemas import TargetDetectRequest, TargetDetectResponse
from app.services.artifacts import load_dataset

# Import target_utils z packages - używamy importlib aby poprawnie obsłużyć względne importy
packages_path = Path(__file__).resolve().parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path.parent))
import importlib.util

# Najpierw importujemy schema_utils (używane przez inne moduły)
schema_utils_spec = importlib.util.spec_from_file_location("packages.schema_utils", packages_path / "schema_utils.py")
schema_utils = importlib.util.module_from_spec(schema_utils_spec)
sys.modules["packages.schema_utils"] = schema_utils
schema_utils_spec.loader.exec_module(schema_utils)

# Import config.llm_client (używany przez target_picker_llm)
config_path = packages_path.parent / "config"
sys.path.insert(0, str(config_path.parent))
import importlib
config_module = importlib.import_module("config.llm_client")
sys.modules["config"] = importlib.import_module("config")
sys.modules["config.llm_client"] = config_module

# Import retry_utils (używany przez target_picker_llm)
retry_utils_spec = importlib.util.spec_from_file_location("packages.retry_utils", packages_path / "retry_utils.py")
retry_utils = importlib.util.module_from_spec(retry_utils_spec)
sys.modules["packages.retry_utils"] = retry_utils
retry_utils_spec.loader.exec_module(retry_utils)

# Import target_picker_llm (używany przez target_utils)
target_picker_llm_spec = importlib.util.spec_from_file_location("packages.target_picker_llm", packages_path / "target_picker_llm.py")
target_picker_llm = importlib.util.module_from_spec(target_picker_llm_spec)
sys.modules["packages.target_picker_llm"] = target_picker_llm
target_picker_llm_spec.loader.exec_module(target_picker_llm)

# Teraz importujemy target_utils
target_utils_spec = importlib.util.spec_from_file_location("packages.target_utils", packages_path / "target_utils.py")
target_utils = importlib.util.module_from_spec(target_utils_spec)
sys.modules["packages.target_utils"] = target_utils
target_utils_spec.loader.exec_module(target_utils)

choose_target = target_utils.choose_target
infer_schema = schema_utils.infer_schema


def _czy_datetime(seria: pd.Series) -> bool:
    try:
        pd.to_datetime(seria.dropna().astype(str), errors="raise")
        return True
    except Exception:
        return False


def _czy_idopodobna(nazwa: str, seria: pd.Series) -> bool:
    name_l = (nazwa or "").lower()
    markery = ["id", "uuid", "guid", "code", "pk", "hash", "no", "number", "index"]
    if any(tok in name_l for tok in markery):
        return True
    n = len(seria) if len(seria) else 1
    nunique = seria.nunique(dropna=True)
    return (nunique >= 0.9 * n)


def _dominacja(seria: pd.Series) -> float:
    vc = seria.value_counts(dropna=True)
    if vc.empty:
        return 1.0
    return float(vc.iloc[0] / vc.sum())


def _entropia_znorm(seria: pd.Series) -> float:
    vc = seria.value_counts(dropna=True)
    s = vc.sum()
    if s == 0 or len(vc) == 0:
        return 0.0
    p = vc / s
    ent = float(-(p * np.log2(p + 1e-12)).sum())
    max_ent = float(np.log2(len(vc)))
    return float(ent / (max_ent + 1e-12)) if max_ent > 0 else 0.0


def _monotonicznosc(seria: pd.Series) -> float:
    s = pd.to_numeric(seria, errors="coerce").dropna()
    if len(s) < 3:
        return 0.0
    dif = s.diff().dropna()
    inc = (dif >= 0).mean()
    dec = (dif <= 0).mean()
    return float(max(inc, dec))


def _klasyfikuj_typ_kolumny(seria: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(seria):
        return "liczbowa"
    if _czy_datetime(seria):
        return "czasowa"
    return "kategoryczna"


def _integerowosc(seria: pd.Series) -> float:
    s = pd.to_numeric(seria, errors="coerce").dropna()
    if len(s) == 0:
        return 0.0
    return float((np.abs(s - np.round(s)) < 1e-9).mean())


def _ocen_kandydatow(df: pd.DataFrame) -> pd.DataFrame:
    wiersze: List[Dict[str, Any]] = []
    n = len(df) if len(df) else 1
    for kol in df.columns:
        s = df[kol]
        typ = _klasyfikuj_typ_kolumny(s)
        braki = float(s.isna().mean())
        nunique = int(s.nunique(dropna=True))

        fl_id = _czy_idopodobna(kol, s)
        fl_time = (typ == "czasowa")

        reg_score = np.nan
        if typ == "liczbowa":
            s_num = pd.to_numeric(s, errors="coerce")
            std = float(s_num.std(skipna=True) or 0.0)
            mono = _monotonicznosc(s)
            uniq_ratio = nunique / n
            reg_score = (std > 0) * (1 - braki) * np.log2(1 + nunique) * (1 - mono) * (1 + uniq_ratio)

        cls_score = np.nan
        if typ == "kategoryczna":
            dom = _dominacja(s)
            ent = _entropia_znorm(s)
            ok_klas = int(2 <= nunique <= max(2, min(50, int(0.3 * n))))
            cls_score = ok_klas * (1 - braki) * (1 - dom) * (0.5 + 0.5 * ent)

        scores = [sc for sc in [reg_score, cls_score] if not (isinstance(sc, float) and np.isnan(sc))]
        best_score = max(scores) if scores else np.nan

        wiersze.append({
            "kolumna": kol,
            "typ_wykryty": typ,
            "odsetek_brakow": round(braki, 4),
            "n_unikalnych": nunique,
            "monotonicznosc": round(_monotonicznosc(s), 4) if typ == "liczbowa" else np.nan,
            "dominacja_max": round(_dominacja(s), 4) if typ == "kategoryczna" else np.nan,
            "entropia_norm": round(_entropia_znorm(s), 4) if typ == "kategoryczna" else np.nan,
            "regresja_score": None if np.isnan(reg_score) else float(reg_score),
            "klasyfikacja_score": None if np.isnan(cls_score) else float(cls_score),
            "kandydat_score": None if np.isnan(best_score) else float(best_score),
            "odrzucic_idopodobna": bool(fl_id),
            "odrzucic_czasowa": bool(fl_time),
        })
    rank = pd.DataFrame(wiersze)
    rank["odrzucic"] = rank["odrzucic_idopodobna"] | rank["odrzucic_czasowa"]
    rank = rank.sort_values(by=["odrzucic", "kandydat_score"], ascending=[True, False], na_position="last")
    return rank.reset_index(drop=True)


def _wykryj_typ_problemu(df: pd.DataFrame, target: str) -> str:
    s = df[target]
    typ = _klasyfikuj_typ_kolumny(s)
    if typ == "kategoryczna":
        return "klasyfikacja"
    if typ == "liczbowa":
        n = len(s) if len(s) else 1
        nunique = s.nunique(dropna=True)
        int_share = _integerowosc(s)
        if nunique <= max(20, int(0.05 * n)) and int_share >= 0.95:
            return "klasyfikacja"
        return "regresja"
    return "regresja"


def _wybierz_target_i_typ(
    df: pd.DataFrame,
    wybor_uzytkownika: Optional[str] = None,
    sugestia_llm: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    rank = _ocen_kandydatow(df)

    if wybor_uzytkownika and wybor_uzytkownika in df.columns:
        target = wybor_uzytkownika
        zrodlo = "uzytkownik"
    elif sugestia_llm and sugestia_llm in df.columns:
        target = sugestia_llm
        zrodlo = "LLM"
    else:
        kandydaci = rank[~rank["odrzucic"]].copy()
        if kandydaci.empty:
            kandydaci = rank.copy()
        target = str(kandydaci.iloc[0]["kolumna"])
        zrodlo = "heurystyka"

    typ = _wykryj_typ_problemu(df, target)
    meta = {"zrodlo_wyboru": zrodlo, "ranking": rank}
    return target, typ, meta


def detect_target_service(req: TargetDetectRequest) -> TargetDetectResponse:
    df = load_dataset(req.datasetId)
    schema = infer_schema(df)
    
    # Użyj klucza z .env jeśli frontend nie podał klucza lub podał '__env__'
    api_key = None
    if req.openaiApiKey and req.openaiApiKey.strip() and req.openaiApiKey != '__env__':
        api_key = req.openaiApiKey.strip()
    else:
        # Spróbuj użyć klucza z .env
        import sys
        import os
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        from config.settings import settings
        env_key = settings.openai_api_key.strip() if settings.openai_api_key else None
        api_key = env_key if env_key else None
    
    # Użyj choose_target z target_utils, który obsługuje LLM
    decision = choose_target(
        df=df,
        schema=schema,
        user_choice=req.userTarget,
        api_key=api_key
    )
    
    if decision.target is None:
        # Fallback do heurystyki
        target, problem_type, meta = _wybierz_target_i_typ(
            df, wybor_uzytkownika=req.userTarget, sugestia_llm=None
        )
        rank_df = meta["ranking"]
        ranking = rank_df.fillna(None).to_dict(orient="records")
        return TargetDetectResponse(
            datasetId=req.datasetId,
            suggestedTarget=target,
            problemType=problem_type,
            ranking=ranking,
            source="heuristics_pick",
        )
    
    # Określ typ problemu
    problem_type = _wykryj_typ_problemu(df, decision.target)
    
    # Pobierz ranking z debug info jeśli dostępne
    ranking = []
    if decision.debug and "scores" in decision.debug:
        # Konwertuj scores na ranking
        scores = decision.debug["scores"]
        for name, sc in sorted(scores.items(), key=lambda kv: kv[1].get("total", 0), reverse=True):
            ranking.append({
                "kolumna": name,
                "kandydat_score": sc.get("total", 0),
                "name_score": sc.get("name_score", 0),
                "type_score": sc.get("type_score", 0),
                "quality_score": sc.get("quality_score", 0),
            })
    else:
        # Fallback - użyj heurystyki do rankingu
        _, _, meta = _wybierz_target_i_typ(df, wybor_uzytkownika=None, sugestia_llm=None)
        rank_df = meta["ranking"]
        ranking = rank_df.fillna(None).to_dict(orient="records")
    
    return TargetDetectResponse(
        datasetId=req.datasetId,
        suggestedTarget=decision.target,
        problemType=problem_type,
        ranking=ranking,
        source=decision.source,
    )


