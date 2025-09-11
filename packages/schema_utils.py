from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Literal, List
import pandas as pd
import json
import random

import numpy as np
from pandas.api.types import (
    is_numeric_dtype,
    is_integer_dtype,
    is_float_dtype,
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_string_dtype,
)


SemanticType = Literal["numeric", "integer", "float", "boolean", "datetime", "categorical", "text", "unknown"]


@dataclass
class ColumnSchema:
    name: str
    pandas_dtype: str
    semantic_type: SemanticType
    n_unique: int
    unique_ratio: float
    is_unique: bool
    n_missing: int
    missing_ratio: float
    is_constant: bool
    example_non_null: Optional[Any] = None
    min_value: Optional[Any] = None           # dla numeric/datetime
    max_value: Optional[Any] = None           # dla numeric/datetime
    datetime_parse_rate: Optional[float] = None  # jeśli próbowaliśmy parsować obiekty na daty


@dataclass
class Schema:
    n_rows: int
    n_cols: int
    columns: Dict[str, ColumnSchema]
    primary_key_candidates: list[str]          # kolumny unikalne i bez braków
    notes: list[str]                           # luźne wskazówki, np. bardzo dużo braków


def _try_parse_datetime(series: pd.Series, sample_size: int = 100) -> tuple[float, Optional[pd.Series]]:
    """
    Próbnie parsuje wartości kolumny `object` jako daty.
    Zwraca odsetek poprawnie sparsowanych (na próbie) oraz pełną serię dat (lub None).
    """
    s = series.dropna()
    if s.empty:
        return 0.0, None

    sample = s.sample(min(sample_size, len(s)), random_state=42) if len(s) > sample_size else s
    # Próbuj różne formaty dat
    parsed_sample = None
    date_formats = [
        "%Y-%m-%d",           # 2025-01-01
        "%Y-%m-%d %H:%M:%S",  # 2025-01-01 12:00:00
        "%d/%m/%Y",           # 01/01/2025
        "%m/%d/%Y",           # 01/01/2025
        "%Y-%m-%dT%H:%M:%S",  # ISO format
        "%Y-%m-%dT%H:%M:%SZ", # ISO format z Z
        "%d-%m-%Y",           # 01-01-2025
        "%m-%d-%Y",           # 01-01-2025
    ]
    
    for date_format in date_formats:
        try:
            parsed_sample = pd.to_datetime(sample, format=date_format, errors="coerce", utc=True)
            if parsed_sample.notna().mean() >= 0.9:
                break
        except:
            continue
    
    # Jeśli żaden format nie zadziałał, spróbuj automatycznego parsowania z wyciszeniem ostrzeżeń
    if parsed_sample is None or parsed_sample.notna().mean() < 0.9:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed_sample = pd.to_datetime(sample, errors="coerce", utc=True)
    
    rate = float(parsed_sample.notna().mean())

    if rate >= 0.9:  # wysoki odsetek trafień -> traktujemy jako daty
        # Użyj tego samego formatu dla pełnej serii z wyciszeniem ostrzeżeń
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed_full = pd.to_datetime(series, errors="coerce", utc=True)
        return rate, parsed_full

    return rate, None


def _detect_semantic_type(s: pd.Series) -> tuple[SemanticType, Dict[str, Any]]:
    """
    Określa semantyczny typ kolumny (numeric/integer/float/boolean/datetime/categorical/text/unknown)
    oraz zwraca dodatkowe metryki (min/max, datetime_parse_rate).
    """
    info: Dict[str, Any] = {
        "min_value": None,
        "max_value": None,
        "datetime_parse_rate": None,
    }

    # 1) Natychmiastowe przypadki po dtype
    if is_bool_dtype(s):
        return "boolean", info

    if is_datetime64_any_dtype(s):
        if s.notna().any():
            min_val = s.min()
            max_val = s.max()
            # Konwertuj Timestamp na string dla kompatybilności z PyArrow
            info["min_value"] = str(min_val) if pd.notna(min_val) else None
            info["max_value"] = str(max_val) if pd.notna(max_val) else None
        return "datetime", info

    if is_numeric_dtype(s):
        # rozróżniamy integer vs float
        st: SemanticType = "integer" if is_integer_dtype(s) else ("float" if is_float_dtype(s) else "numeric")
        if s.notna().any():
            info["min_value"] = pd.to_numeric(s, errors="coerce").min()
            info["max_value"] = pd.to_numeric(s, errors="coerce").max()
        return st, info

    # 2) Dla object/string próbujemy:
    if is_string_dtype(s) or s.dtype == "object":
        # a) boolean-like?
        non_null = s.dropna().astype(str).str.strip().str.lower()
        boolean_tokens = {"true", "false", "t", "f", "yes", "no", "y", "n", "0", "1"}
        if not non_null.empty and non_null.isin(boolean_tokens).mean() >= 0.98:
            return "boolean", info

        # b) datetime-like?
        rate, parsed = _try_parse_datetime(s)
        info["datetime_parse_rate"] = rate
        if parsed is not None:
            if parsed.notna().any():
                min_val = parsed.min()
                max_val = parsed.max()
                # Konwertuj Timestamp na string dla kompatybilności z PyArrow
                info["min_value"] = str(min_val) if pd.notna(min_val) else None
                info["max_value"] = str(max_val) if pd.notna(max_val) else None
            return "datetime", info

        # c) categorical vs text (poziom unikalności)
        n_unique = s.nunique(dropna=True)
        n = len(s)
        if n > 0:
            ratio = n_unique / n
            # Heurystyka: mało unikalnych wzgl. liczby wierszy lub bezwzględnie niewiele kategorii
            if n_unique <= 50 or ratio <= 0.05:
                return "categorical", info
            return "text", info

    return "unknown", info


def infer_schema(df: pd.DataFrame) -> Schema:
    """
    Buduje schemat DataFrame:
      - pandas dtype i semantyczny typ kolumny,
      - liczność unikalnych wartości (i ratio),
      - brakujące wartości,
      - wykrywanie dat (także w kolumnach object),
      - flagi: unikalna/stała kolumna,
      - kandydaci na klucz główny.

    Nie modyfikuje wejściowego DataFrame.
    """
    n_rows, n_cols = df.shape
    cols: Dict[str, ColumnSchema] = {}
    notes: list[str] = []

    for name in df.columns:
        s = df[name]
        pandas_dtype = str(s.dtype)

        n_unique = int(s.nunique(dropna=True))
        unique_ratio = float(n_unique / len(s)) if len(s) else 0.0
        is_unique = bool((s.isna().sum() == 0) and (n_unique == len(s)))  # unikalne i bez braków
        n_missing = int(s.isna().sum())
        missing_ratio = float(n_missing / len(s)) if len(s) else 0.0
        is_constant = bool(n_unique == 1 or (n_unique == 0 and n_missing > 0))

        example_non_null = None
        non_null_values = s.dropna()
        if not non_null_values.empty:
            example_non_null = non_null_values.iloc[0]

        semantic_type, extra = _detect_semantic_type(s)

        col_schema = ColumnSchema(
            name=name,
            pandas_dtype=pandas_dtype,
            semantic_type=semantic_type,
            n_unique=n_unique,
            unique_ratio=unique_ratio,
            is_unique=is_unique,
            n_missing=n_missing,
            missing_ratio=missing_ratio,
            is_constant=is_constant,
            example_non_null=example_non_null,
            min_value=extra.get("min_value"),
            max_value=extra.get("max_value"),
            datetime_parse_rate=extra.get("datetime_parse_rate"),
        )
        cols[name] = col_schema

        # Luźne notatki pomocnicze
        if missing_ratio >= 0.3:
            notes.append(f"Kolumna '{name}' ma wysoki odsetek braków: {missing_ratio:.1%}.")
        if is_constant:
            notes.append(f"Kolumna '{name}' jest stała (brak zmienności).")
        if name.lower() in {"id", "uuid", "pk", "primary_key"} and not is_unique:
            notes.append(f"Kolumna '{name}' wygląda na identyfikator, ale nie jest unikalna.")

    primary_key_candidates = [
        c.name for c in cols.values() if c.is_unique and c.missing_ratio == 0.0
    ]

    return Schema(
        n_rows=n_rows,
        n_cols=n_cols,
        columns=cols,
        primary_key_candidates=primary_key_candidates,
        notes=notes,
    )

def schema_to_frame(schema: "Schema") -> pd.DataFrame:
    """
    Konwertuje Schema na tabelę z podsumowaniem kolumn.
    Kolumny: name, pandas_dtype, semantic_type, n_unique, unique_ratio, is_unique,
             n_missing, missing_ratio, is_constant, min_value, max_value,
             datetime_parse_rate, example_non_null
    """
    rows = []
    for col in schema.columns.values():
        rows.append({
            "name": col.name,
            "pandas_dtype": col.pandas_dtype,
            "semantic_type": col.semantic_type,
            "n_unique": col.n_unique,
            "unique_ratio": col.unique_ratio,
            "is_unique": col.is_unique,
            "n_missing": col.n_missing,
            "missing_ratio": col.missing_ratio,
            "is_constant": col.is_constant,
            "min_value": col.min_value,
            "max_value": col.max_value,
            "datetime_parse_rate": col.datetime_parse_rate,
            "example_non_null": col.example_non_null,
        })

    df_summary = pd.DataFrame(rows, columns=[
        "name", "pandas_dtype", "semantic_type",
        "n_unique", "unique_ratio", "is_unique",
        "n_missing", "missing_ratio", "is_constant",
        "min_value", "max_value", "datetime_parse_rate",
        "example_non_null"
    ])
    
    # Konwertuj min_value, max_value i example_non_null na stringi dla kompatybilności z PyArrow
    df_summary["min_value"] = df_summary["min_value"].astype(str)
    df_summary["max_value"] = df_summary["max_value"].astype(str)
    df_summary["example_non_null"] = df_summary["example_non_null"].astype(str)
    # Zamień 'None' z powrotem na None dla lepszej czytelności
    df_summary["min_value"] = df_summary["min_value"].replace("None", None)
    df_summary["max_value"] = df_summary["max_value"].replace("None", None)
    df_summary["example_non_null"] = df_summary["example_non_null"].replace("None", None)

    # Formatki procentów do czytelnego podglądu (nie zmieniają wartości liczbowych)
    # Jeśli wolisz surowe floaty, usuń te linie.
    df_summary["unique_ratio"] = df_summary["unique_ratio"].astype(float)
    df_summary["missing_ratio"] = df_summary["missing_ratio"].astype(float)

    return df_summary

# (opcjonalnie) helper do wygodnego podglądu jako dict (np. do JSON)
def schema_asdict(schema: Schema) -> dict:
    return {
        "n_rows": schema.n_rows,
        "n_cols": schema.n_cols,
        "columns": {k: asdict(v) for k, v in schema.columns.items()},
        "primary_key_candidates": schema.primary_key_candidates,
        "notes": list(schema.notes),
    }


@dataclass
class BusinessContextAnalysis:
    """Wynik analizy kontekstu biznesowego danych"""
    domain: str
    business_purpose: str
    data_description: str
    key_insights: List[str]


@dataclass
class ColumnRelationships:
    """Wynik analizy relacji między kolumnami"""
    relationships: List[Dict[str, Any]]
    correlation_matrix: Dict[str, Dict[str, float]]
    suggested_groupings: List[List[str]]


@dataclass
class DataCleaningSuggestions:
    """Sugestie do czyszczenia danych"""
    missing_data_strategy: Dict[str, str]
    outlier_treatment: Dict[str, str]
    data_type_conversions: List[Dict[str, str]]
    quality_issues: List[str]


def determine_business_domain(df: pd.DataFrame, schema: Schema, api_key: str) -> Optional[str]:
    """
    Krok 1: Określa domenę biznesową danych za pomocą LLM.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        api_key: Klucz API OpenAI
    
    Returns:
        Nazwa domeny biznesowej lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj przykładowe dane z kolumn tekstowych
        text_columns = [col for col, info in schema.columns.items() 
                       if info.semantic_type in ["text", "categorical"] and info.n_unique > 1]
        
        sample_data = {}
        for col in text_columns[:5]:  # Maksymalnie 5 kolumn tekstowych
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                # Pobierz 5 losowych wartości
                sample_size = min(5, len(non_null_values))
                sample_values = random.sample(list(non_null_values), sample_size)
                sample_data[col] = sample_values
        
        # Przygotuj prompt
        columns_info = []
        for col, info in schema.columns.items():
            columns_info.append(f"- {col}: {info.semantic_type} ({info.n_unique} unikalnych wartości, {info.missing_ratio:.1%} braków)")
        
        prompt = f"""
Jako ekspert analizy danych, przeanalizuj poniższy zbiór danych i określ JEDYNIE domenę biznesową.

**Informacje o kolumnach:**
{chr(10).join(columns_info)}

**Przykładowe dane z kolumn tekstowych:**
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

**Zadanie:** Określ w jakiej branży/obszarze działalności mogą być te dane.

**Odpowiedz TYLKO nazwą domeny biznesowej w jednym zdaniu, np.:**
"Handel detaliczny - sprzedaż produktów spożywczych"
"Finanse - analiza kredytowa klientów"
"E-commerce - dane o transakcjach online"
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ [Business Domain] Błąd: {e}")
        return None


def llm_guess_target_with_domain(df: pd.DataFrame, schema: Schema, business_domain: str, api_key: str) -> Optional[str]:
    """
    Krok 2: Wybiera kolumnę docelową używając wcześniej określonej domeny biznesowej.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        business_domain: Wcześniej określona domena biznesowa
        api_key: Klucz API OpenAI
    
    Returns:
        Nazwa kolumny docelowej lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj informacje o kolumnach
        columns_info = []
        for col, info in schema.columns.items():
            columns_info.append(f"- {col}: {info.semantic_type} ({info.n_unique} unikalnych wartości)")
        
        prompt = f"""
Jako ekspert analizy danych, wybierz najlepszą kolumnę docelową dla modelu ML.

**Domena biznesowa:** {business_domain}

**Kolumny w zbiorze danych:**
{chr(10).join(columns_info)}

**Zadanie:** Wybierz kolumnę, która będzie najlepszym targetem dla modelu ML w kontekście tej domeny biznesowej.

**Odpowiedz TYLKO nazwą kolumny, np.:**
"price"
"survived"
"Total Volume"
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        target = response.choices[0].message.content.strip()
        
        # Usuń cudzysłowy jeśli są
        if target.startswith('"') and target.endswith('"'):
            target = target[1:-1]
        
        # Sprawdź czy kolumna istnieje
        print(f"🔍 [LLM Target] LLM wybrał kolumnę: '{target}'")
        print(f"🔍 [LLM Target] Dostępne kolumny: {list(df.columns)}")
        if target in df.columns:
            return target
        else:
            print(f"⚠️ [LLM Target] LLM wybrał nieistniejącą kolumnę: {target}")
            return None
        
    except Exception as e:
        print(f"❌ [LLM Target] Błąd: {e}")
        return None


def analyze_column_correlations_by_names(df: pd.DataFrame, schema: Schema, business_domain: str, target_column: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Krok 3: Analizuje korelacje między kolumnami na podstawie nazw.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        business_domain: Domena biznesowa
        target_column: Wybrana kolumna docelowa
        api_key: Klucz API OpenAI
    
    Returns:
        Słownik z analizą korelacji lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj informacje o kolumnach
        columns_info = []
        for col, info in schema.columns.items():
            columns_info.append(f"- {col}: {info.semantic_type} ({info.n_unique} unikalnych wartości)")
        
        prompt = f"""
Jako ekspert analizy danych, przeanalizuj korelacje między kolumnami na podstawie ich nazw.

**Domena biznesowa:** {business_domain}
**Kolumna docelowa:** {target_column}

**Kolumny w zbiorze danych:**
{chr(10).join(columns_info)}

**Zadanie:** Przeanalizuj i określ prawdopodobne korelacje między kolumnami na podstawie ich nazw i kontekstu biznesowego.

**Odpowiedz w formacie JSON:**
{{
    "correlations": [
        {{
            "column1": "nazwa_kolumny_1",
            "column2": "nazwa_kolumny_2",
            "correlation_strength": "wysoka/średnia/niska",
            "correlation_type": "dodatnia/ujemna",
            "business_reason": "uzasadnienie biznesowe"
        }}
    ],
    "target_correlations": [
        {{
            "column": "nazwa_kolumny",
            "expected_impact": "wysoki/średni/niski",
            "relationship": "opis relacji z targetem"
        }}
    ]
}}
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # Spróbuj wyciągnąć JSON z odpowiedzi
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Jeśli nie jest to czysty JSON, spróbuj wyciągnąć JSON z tekstu
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
            else:
                print(f"❌ [Column Correlations] Nie można wyciągnąć JSON z odpowiedzi: {content}")
                return {"error": "Nie można sparsować odpowiedzi LLM jako JSON"}
        
    except Exception as e:
        print(f"❌ [Column Correlations] Błąd: {e}")
        return None


def generate_data_cleaning_suggestions_step(df: pd.DataFrame, schema: Schema, business_domain: str, target_column: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Krok 4: Generuje sugestie do naprawy danych.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        business_domain: Domena biznesowa
        target_column: Wybrana kolumna docelowa
        api_key: Klucz API OpenAI
    
    Returns:
        Słownik z sugestiami lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj szczegółowe informacje o kolumnach
        columns_details = []
        for col, info in schema.columns.items():
            details = {
                "name": col,
                "semantic_type": info.semantic_type,
                "missing_ratio": info.missing_ratio,
                "n_unique": info.n_unique,
                "is_constant": info.is_constant,
                "example_value": str(info.example_non_null) if info.example_non_null else None
            }
            columns_details.append(details)
        
        prompt = f"""
Jako ekspert data science, przeanalizuj poniższy schemat danych i wygeneruj sugestie do naprawy danych.

**Domena biznesowa:** {business_domain}
**Kolumna docelowa:** {target_column}

**Szczegółowe informacje o kolumnach:**
{json.dumps(columns_details, ensure_ascii=False, indent=2)}

**Zauważone problemy:**
{chr(10).join(f"- {note}" for note in schema.notes)}

**Zadanie:** Wygeneruj sugestie do naprawy danych w kontekście domeny biznesowej i wybranej kolumny docelowej.

**Odpowiedz w formacie JSON:**
{{
    "missing_data_strategy": {{
        "kolumna1": "strategia obsługi braków",
        "kolumna2": "strategia obsługi braków"
    }},
    "outlier_treatment": {{
        "kolumna1": "strategia obsługi outliers",
        "kolumna2": "strategia obsługi outliers"
    }},
    "data_type_conversions": [
        {{"column": "kolumna1", "from": "obecny_typ", "to": "docelowy_typ", "reason": "uzasadnienie"}}
    ],
    "quality_issues": [
        "problem 1",
        "problem 2"
    ],
    "target_specific_suggestions": [
        "sugestia specyficzna dla targetu 1",
        "sugestia specyficzna dla targetu 2"
    ]
}}
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # Spróbuj wyciągnąć JSON z odpowiedzi
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Jeśli nie jest to czysty JSON, spróbuj wyciągnąć JSON z tekstu
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
            else:
                print(f"❌ [Data Cleaning] Nie można wyciągnąć JSON z odpowiedzi: {content}")
                return {"error": "Nie można sparsować odpowiedzi LLM jako JSON"}
        
    except Exception as e:
        print(f"❌ [Data Cleaning] Błąd: {e}")
        return None


def analyze_business_context(df: pd.DataFrame, schema: Schema, api_key: str) -> Optional[BusinessContextAnalysis]:
    """
    Analizuje kontekst biznesowy danych za pomocą LLM.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        api_key: Klucz API OpenAI
    
    Returns:
        BusinessContextAnalysis lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj przykładowe dane z kolumn tekstowych
        text_columns = [col for col, info in schema.columns.items() 
                       if info.semantic_type in ["text", "categorical"] and info.n_unique > 1]
        
        sample_data = {}
        for col in text_columns[:5]:  # Maksymalnie 5 kolumn tekstowych
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                # Pobierz 5 losowych wartości
                sample_size = min(5, len(non_null_values))
                sample_values = random.sample(list(non_null_values), sample_size)
                sample_data[col] = sample_values
        
        # Przygotuj prompt
        columns_info = []
        for col, info in schema.columns.items():
            columns_info.append(f"- {col}: {info.semantic_type} ({info.n_unique} unikalnych wartości, {info.missing_ratio:.1%} braków)")
        
        prompt = f"""
Jako ekspert analizy danych, przeanalizuj poniższy zbiór danych i określ:

1. **Domenę biznesową** - w jakiej branży/obszarze działalności mogą być te dane?
2. **Cel biznesowy** - do czego mogą służyć te dane?
3. **Opis danych** - co reprezentują te dane w kontekście biznesowym?
4. **Kluczowe spostrzeżenia** - jakie ważne informacje można wyciągnąć z nazw kolumn i przykładowych danych?

**Informacje o kolumnach:**
{chr(10).join(columns_info)}

**Przykładowe dane z kolumn tekstowych:**
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

**Odpowiedz w formacie JSON:**
{{
    "domain": "nazwa domeny biznesowej",
    "business_purpose": "cel biznesowy danych",
    "data_description": "opis co reprezentują dane",
    "key_insights": ["spostrzeżenie 1", "spostrzeżenie 2", "spostrzeżenie 3"]
}}
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return BusinessContextAnalysis(
            domain=result["domain"],
            business_purpose=result["business_purpose"],
            data_description=result["data_description"],
            key_insights=result["key_insights"]
        )
        
    except Exception as e:
        print(f"❌ [Business Context] Błąd: {e}")
        return None


def analyze_column_relationships(df: pd.DataFrame, schema: Schema, business_context: BusinessContextAnalysis, api_key: str) -> Optional[ColumnRelationships]:
    """
    Analizuje relacje między kolumnami na podstawie nazw i kontekstu biznesowego.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        business_context: Kontekst biznesowy danych
        api_key: Klucz API OpenAI
    
    Returns:
        ColumnRelationships lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj informacje o kolumnach
        columns_info = []
        for col, info in schema.columns.items():
            columns_info.append(f"- {col}: {info.semantic_type} ({info.n_unique} unikalnych wartości)")
        
        prompt = f"""
Jako ekspert analizy danych, przeanalizuj relacje między kolumnami w kontekście domeny biznesowej.

**Kontekst biznesowy:**
- Domena: {business_context.domain}
- Cel: {business_context.business_purpose}
- Opis: {business_context.data_description}

**Kolumny w zbiorze danych:**
{chr(10).join(columns_info)}

Przeanalizuj i określ:

1. **Relacje między kolumnami** - które kolumny mogą być powiązane logicznie?
2. **Macierz korelacji na podstawie nazw** - jakie są prawdopodobne korelacje między kolumnami?
3. **Sugerowane grupowania** - które kolumny można pogrupować tematycznie?

**Odpowiedz w formacie JSON:**
{{
    "relationships": [
        {{
            "column1": "nazwa_kolumny_1",
            "column2": "nazwa_kolumny_2", 
            "relationship_type": "typ_relacji",
            "description": "opis relacji"
        }}
    ],
    "correlation_matrix": {{
        "kolumna1": {{"kolumna2": 0.8, "kolumna3": 0.3}},
        "kolumna2": {{"kolumna1": 0.8, "kolumna3": 0.5}}
    }},
    "suggested_groupings": [
        ["kolumna1", "kolumna2"],
        ["kolumna3", "kolumna4", "kolumna5"]
    ]
}}
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return ColumnRelationships(
            relationships=result["relationships"],
            correlation_matrix=result["correlation_matrix"],
            suggested_groupings=result["suggested_groupings"]
        )
        
    except Exception as e:
        print(f"❌ [Column Relationships] Błąd: {e}")
        return None


def generate_data_cleaning_suggestions(df: pd.DataFrame, schema: Schema, api_key: str) -> Optional[DataCleaningSuggestions]:
    """
    Generuje sugestie do czyszczenia danych na podstawie schematu.
    
    Args:
        df: DataFrame z danymi
        schema: Schemat danych
        api_key: Klucz API OpenAI
    
    Returns:
        DataCleaningSuggestions lub None w przypadku błędu
    """
    try:
        from config.llm_client import get_openai_client, MODEL
        
        client = get_openai_client(api_key)
        if not client:
            return None
            
        # Przygotuj szczegółowe informacje o kolumnach
        columns_details = []
        for col, info in schema.columns.items():
            details = {
                "name": col,
                "semantic_type": info.semantic_type,
                "missing_ratio": info.missing_ratio,
                "n_unique": info.n_unique,
                "is_constant": info.is_constant,
                "example_value": str(info.example_non_null) if info.example_non_null else None
            }
            columns_details.append(details)
        
        prompt = f"""
Jako ekspert data science, przeanalizuj poniższy schemat danych i wygeneruj sugestie do czyszczenia danych.

**Szczegółowe informacje o kolumnach:**
{json.dumps(columns_details, ensure_ascii=False, indent=2)}

**Zauważone problemy:**
{chr(10).join(f"- {note}" for note in schema.notes)}

Wygeneruj sugestie w następujących kategoriach:

1. **Strategia obsługi braków danych** - jak obsłużyć wartości brakujące w każdej kolumnie?
2. **Obsługa wartości odstających** - jak zidentyfikować i obsłużyć outliers?
3. **Konwersje typów danych** - jakie konwersje są potrzebne?
4. **Problemy jakościowe** - jakie inne problemy jakościowe zauważasz?

**Odpowiedz w formacie JSON:**
{{
    "missing_data_strategy": {{
        "kolumna1": "usunąć wiersze",
        "kolumna2": "wypełnić medianą",
        "kolumna3": "wypełnić modą"
    }},
    "outlier_treatment": {{
        "kolumna1": "winsorization",
        "kolumna2": "usunąć wartości > 3*std"
    }},
    "data_type_conversions": [
        {{"column": "kolumna1", "from": "object", "to": "datetime", "reason": "zawiera daty"}},
        {{"column": "kolumna2", "from": "object", "to": "category", "reason": "małe unikalne wartości"}}
    ],
    "quality_issues": [
        "problem 1",
        "problem 2"
    ]
}}
"""
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return DataCleaningSuggestions(
            missing_data_strategy=result["missing_data_strategy"],
            outlier_treatment=result["outlier_treatment"],
            data_type_conversions=result["data_type_conversions"],
            quality_issues=result["quality_issues"]
        )
        
    except Exception as e:
        print(f"❌ [Data Cleaning] Błąd: {e}")
        return None
