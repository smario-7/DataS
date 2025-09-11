"""
Generator raportów z LLM - główny moduł
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.llm_client import get_openai_client
from .chart_generator import generate_prediction_charts


@dataclass
class ReportData:
    """Struktura danych wejściowych dla raportu"""
    business_domain: str
    target_column: str
    ai_analyses_steps: Dict[str, Any]
    ml_results: Dict[str, Any]
    df: pd.DataFrame
    feature_importance_data: Optional[Dict] = None
    model_metrics: Optional[Dict] = None


def generate_comprehensive_report(
    business_domain: str,
    target_column: str,
    ai_analyses_steps: Dict[str, Any],
    ml_results: Dict[str, Any],
    df: pd.DataFrame,
    api_key: str
) -> str:
    """
    Generuje komprehensywny raport z LLM na podstawie wszystkich zebranych danych
    
    Args:
        business_domain: Domena biznesowa danych
        target_column: Kolumna docelowa
        ai_analyses_steps: Wyniki analiz AI (step1-step4)
        ml_results: Wyniki trenowania modelu
        df: DataFrame z danymi
        api_key: Klucz API OpenAI
        
    Returns:
        str: Wygenerowany raport w formacie markdown
    """
    
    # Przygotuj dane wejściowe
    report_data = ReportData(
        business_domain=business_domain,
        target_column=target_column,
        ai_analyses_steps=ai_analyses_steps,
        ml_results=ml_results,
        df=df
    )
    
    # Wygeneruj wykresy
    charts = generate_prediction_charts(df, target_column, ml_results, business_domain)
    
    # Wygeneruj raport
    report = _generate_llm_report(report_data, api_key, charts)
    
    return report


def _generate_llm_report(report_data: ReportData, api_key: str, charts: Dict[str, str] = None) -> str:
    """Generuje raport używając LLM"""
    
    try:
        # Przygotuj dane do promptu
        prompt_data = _prepare_prompt_data(report_data)
        
        # Stwórz prompt dla LLM
        prompt = _create_report_prompt(prompt_data, charts)
        
        # Wyślij zapytanie do LLM
        client = get_openai_client(api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "Jesteś ekspertem w analizie danych i machine learning. Generujesz profesjonalne raporty analityczne w języku polskim z wykresami."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"# Błąd podczas generowania raportu\n\nWystąpił błąd: {str(e)}\n\nSprawdź logi aplikacji dla więcej szczegółów."


def _prepare_prompt_data(report_data: ReportData) -> Dict[str, Any]:
    """Przygotowuje dane do promptu"""
    
    try:
        # Podstawowe informacje
        basic_info = {
            "business_domain": report_data.business_domain,
            "target_column": report_data.target_column,
            "data_shape": f"{report_data.df.shape[0]} wierszy, {report_data.df.shape[1]} kolumn",
            "columns": list(report_data.df.columns),
            "data_types": report_data.df.dtypes.astype(str).to_dict()
        }
        
        # Analiza korelacji
        correlations_data = _extract_correlations_data(report_data.ai_analyses_steps)
        
        # Sugestie czyszczenia danych
        cleaning_suggestions = _extract_cleaning_suggestions(report_data.ai_analyses_steps)
        
        # Wyniki modelu ML
        ml_analysis = _extract_ml_analysis(report_data.ml_results, report_data.df)
        
        # Analiza trendów czasowych
        temporal_analysis = _extract_temporal_analysis(report_data.df, report_data.target_column)
        
        return {
            "basic_info": basic_info,
            "correlations": correlations_data,
            "cleaning_suggestions": cleaning_suggestions,
            "ml_analysis": ml_analysis,
            "temporal_analysis": temporal_analysis
        }
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _prepare_prompt_data: {e}")
        import traceback
        traceback.print_exc()
        raise


def _extract_correlations_data(ai_analyses_steps: Dict[str, Any]) -> Dict[str, Any]:
    """Wyciąga dane o korelacjach z analiz AI"""
    
    step3 = ai_analyses_steps.get('step3', {})
    
    correlations = step3.get('correlations', [])
    target_correlations = step3.get('target_correlations', [])
    
    return {
        "general_correlations": correlations,
        "target_correlations": target_correlations,
        "total_correlations": len(correlations),
        "target_related": len(target_correlations)
    }


def _extract_cleaning_suggestions(ai_analyses_steps: Dict[str, Any]) -> Dict[str, Any]:
    """Wyciąga sugestie czyszczenia danych"""
    
    step4 = ai_analyses_steps.get('step4', {})
    
    return {
        "missing_data_strategy": step4.get('missing_data_strategy', {}),
        "outlier_treatment": step4.get('outlier_treatment', {}),
        "data_type_conversions": step4.get('data_type_conversions', []),
        "quality_issues": step4.get('quality_issues', []),
        "target_specific_suggestions": step4.get('target_specific_suggestions', [])
    }


def _extract_ml_analysis(ml_results: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """Wyciąga analizę wyników modelu ML"""
    
    try:
        if not ml_results:
            return {"error": "Brak wyników modelu ML"}
        
        # Podstawowe metryki
        metrics = ml_results.get('metrics', {})
        
        # Analiza feature importance
        feature_importance = ml_results.get('feature_importance', {})
        
        # Informacje o modelu
        model_info = ml_results.get('model_info', {})
        
        # Konwertuj feature importance na format JSON-serializable
        serializable_importance = {}
        if feature_importance is not None and not (hasattr(feature_importance, 'empty') and feature_importance.empty):
            if isinstance(feature_importance, dict):
                # Jeśli feature_importance to dict z pandas Series, konwertuj na dict
                for key, value in feature_importance.items():
                    if hasattr(value, 'to_dict'):
                        serializable_importance[key] = value.to_dict()
                    elif hasattr(value, 'tolist'):
                        serializable_importance[key] = value.tolist()
                    else:
                        serializable_importance[key] = value
            elif hasattr(feature_importance, 'to_dict'):
                # Jeśli to DataFrame, konwertuj na dict
                serializable_importance = feature_importance.to_dict('records')
            else:
                serializable_importance = feature_importance
        
        return {
            "metrics": metrics,
            "feature_importance": serializable_importance,
            "model_info": model_info,
            "data_quality": {
                "total_rows": int(len(df)),
                "missing_values": int(df.isnull().sum().sum()),
                "duplicate_rows": int(df.duplicated().sum())
            }
        }
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _extract_ml_analysis: {e}")
        import traceback
        traceback.print_exc()
        raise


def _extract_temporal_analysis(df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
    """Analizuje trendy czasowe w danych"""
    
    # Sprawdź czy są kolumny czasowe
    date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    # Sprawdź czy są kolumny z rokiem
    year_columns = [col for col in df.columns if 'year' in col.lower() or 'date' in col.lower()]
    
    temporal_info = {
        "has_temporal_data": len(date_columns) > 0 or len(year_columns) > 0,
        "date_columns": date_columns,
        "year_columns": year_columns,
        "target_column": target_column
    }
    
    # Jeśli mamy dane czasowe, przeanalizuj trendy
    if temporal_info["has_temporal_data"]:
        temporal_info.update(_analyze_temporal_trends(df, target_column, date_columns, year_columns))
    
    return temporal_info


def _analyze_temporal_trends(df: pd.DataFrame, target_column: str, date_columns: list, year_columns: list) -> Dict[str, Any]:
    """Analizuje trendy czasowe"""
    
    trends = {}
    
    # Analiza trendów rocznych
    if year_columns:
        year_col = year_columns[0]
        if year_col in df.columns:
            try:
                yearly_stats = df.groupby(year_col)[target_column].agg(['mean', 'count', 'std'])
                # Konwertuj na dict z float values
                trends['yearly_analysis'] = {
                    'mean': yearly_stats['mean'].to_dict(),
                    'count': yearly_stats['count'].to_dict(),
                    'std': yearly_stats['std'].to_dict()
                }
            except Exception as e:
                trends['yearly_analysis'] = {"error": f"Błąd analizy rocznej: {str(e)}"}
    
    # Analiza trendów miesięcznych (jeśli mamy kolumny dat)
    if date_columns:
        date_col = date_columns[0]
        if date_col in df.columns:
            try:
                df_temp = df.copy()
                df_temp['year'] = pd.to_datetime(df_temp[date_col]).dt.year
                df_temp['month'] = pd.to_datetime(df_temp[date_col]).dt.month
                
                monthly_stats = df_temp.groupby(['year', 'month'])[target_column].mean()
                # Konwertuj na dict z float values
                trends['monthly_analysis'] = monthly_stats.to_dict()
            except Exception as e:
                trends['monthly_analysis'] = {"error": f"Błąd analizy miesięcznej: {str(e)}"}
    
    return trends


def _create_report_prompt(prompt_data: Dict[str, Any], charts: Dict[str, str] = None) -> str:
    """Tworzy prompt dla LLM"""
    
    # Informacje o wykresach
    charts_info = ""
    if charts:
        charts_info = f"""
## 6. WYKRESY I WIZUALIZACJE
Dostępne wykresy:
- **Trendy czasowe**: Wykres pokazujący zmiany {prompt_data['basic_info']['target_column']} w czasie
- **Ważność cech**: Wykres top 10 najważniejszych cech wpływających na {prompt_data['basic_info']['target_column']}
- **Prognoza na przyszłość**: Wykres z przewidywaniami na następne 12 okresów
- **Korelacje**: Macierz korelacji między wszystkimi zmiennymi numerycznymi
- **Rozkład wartości**: Histogram/bar chart pokazujący rozkład {prompt_data['basic_info']['target_column']}

"""
    
    prompt = f"""
Wygeneruj profesjonalny raport analityczny w języku polskim na podstawie następujących danych:

## 1. INFORMACJE PODSTAWOWE
- **Domena biznesowa**: {prompt_data['basic_info']['business_domain']}
- **Kolumna docelowa**: {prompt_data['basic_info']['target_column']}
- **Rozmiar danych**: {prompt_data['basic_info']['data_shape']}
- **Kolumny**: {', '.join(prompt_data['basic_info']['columns'])}
- **Typy danych**: {json.dumps(prompt_data['basic_info']['data_types'], ensure_ascii=False, indent=2)}

## 2. ANALIZA KORELACJI
**Korelacje ogólne** ({prompt_data['correlations']['total_correlations']} relacji):
{json.dumps(prompt_data['correlations']['general_correlations'], ensure_ascii=False, indent=2)}

**Korelacje z kolumną docelową** ({prompt_data['correlations']['target_related']} relacji):
{json.dumps(prompt_data['correlations']['target_correlations'], ensure_ascii=False, indent=2)}

## 3. SUGESTIE CZYSZCZENIA DANYCH
**Strategie obsługi brakujących danych**:
{json.dumps(prompt_data['cleaning_suggestions']['missing_data_strategy'], ensure_ascii=False, indent=2)}

**Obsługa wartości odstających**:
{json.dumps(prompt_data['cleaning_suggestions']['outlier_treatment'], ensure_ascii=False, indent=2)}

**Problemy jakościowe**:
{json.dumps(prompt_data['cleaning_suggestions']['quality_issues'], ensure_ascii=False, indent=2)}

## 4. WYNIKI MODELU ML
**Metryki modelu**:
{json.dumps(prompt_data['ml_analysis'].get('metrics', {}), ensure_ascii=False, indent=2)}

**Ważność cech**:
{json.dumps(prompt_data['ml_analysis'].get('feature_importance', {}), ensure_ascii=False, indent=2)}

**Jakość danych**:
{json.dumps(prompt_data['ml_analysis'].get('data_quality', {}), ensure_ascii=False, indent=2)}

## 5. ANALIZA TRENDÓW CZASOWYCH
**Informacje o danych czasowych**:
{json.dumps(prompt_data['temporal_analysis'], ensure_ascii=False, indent=2)}
{charts_info}
---

**ZADANIE**: Wygeneruj profesjonalny raport zawierający:

1. **Wstęp** - krótkie wprowadzenie do analizy
2. **Analiza korelacji** - interpretacja relacji między zmiennymi
3. **Jakość danych** - ocena i rekomendacje
4. **Wyniki modelu** - interpretacja metryk i ważności cech
5. **Prognozy** - przewidywania na przyszłość na podstawie trendów
6. **Rekomendacje** - konkretne działania biznesowe
7. **Podsumowanie** - kluczowe wnioski

Raport powinien być napisany w sposób profesjonalny, zrozumiały dla menedżerów biznesowych, z konkretnymi wnioskami i rekomendacjami.

**WAŻNE**: Jeśli dostępne są wykresy, odwołuj się do nich w raporcie używając opisów jak "Wykres trendów czasowych pokazuje...", "Analiza ważności cech wskazuje...", itp.
"""
    
    return prompt
