"""
Generator wykresów dla raportu - moduł do tworzenia wykresów prognoz
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import io
import base64
from datetime import datetime, timedelta


def generate_prediction_charts(
    df: pd.DataFrame, 
    target_column: str, 
    ml_results: Dict[str, Any],
    business_domain: str
) -> Dict[str, str]:
    """
    Generuje wykresy prognoz na podstawie danych historycznych
    
    Args:
        df: DataFrame z danymi
        target_column: Kolumna docelowa
        ml_results: Wyniki modelu ML
        business_domain: Domena biznesowa
        
    Returns:
        Dict[str, str]: Słownik z wykresami w formacie base64
    """
    
    charts = {}
    
    try:
        # 1. Wykres trendów czasowych
        charts['temporal_trends'] = _create_temporal_trends_chart(df, target_column)
        
        # 2. Wykres feature importance
        charts['feature_importance'] = _create_feature_importance_chart(ml_results)
        
        # 3. Wykres prognozy na przyszłość
        charts['future_prediction'] = _create_future_prediction_chart(df, target_column, business_domain)
        
        # 4. Wykres korelacji
        charts['correlations'] = _create_correlations_chart(df, target_column)
        
        # 5. Wykres rozkładu wartości docelowej
        charts['target_distribution'] = _create_target_distribution_chart(df, target_column)
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w generowaniu wykresów: {e}")
        import traceback
        traceback.print_exc()
    
    return charts


def _create_temporal_trends_chart(df: pd.DataFrame, target_column: str) -> str:
    """Tworzy wykres trendów czasowych"""
    
    try:
        plt.figure(figsize=(12, 6))
        
        # Sprawdź czy mamy kolumny czasowe
        date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
        year_columns = [col for col in df.columns if 'year' in col.lower() or 'date' in col.lower()]
        
        if date_columns:
            # Użyj kolumny daty
            date_col = date_columns[0]
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col])
            df_temp = df_temp.sort_values(date_col)
            
            plt.plot(df_temp[date_col], df_temp[target_column], linewidth=2, alpha=0.7)
            plt.title(f'Trendy czasowe - {target_column}', fontsize=14, fontweight='bold')
            plt.xlabel('Data', fontsize=12)
            plt.ylabel(target_column, fontsize=12)
            plt.xticks(rotation=45)
            
        elif year_columns:
            # Użyj kolumny roku
            year_col = year_columns[0]
            yearly_data = df.groupby(year_col)[target_column].mean()
            
            plt.plot(yearly_data.index, yearly_data.values, marker='o', linewidth=2, markersize=6)
            plt.title(f'Trendy roczne - {target_column}', fontsize=14, fontweight='bold')
            plt.xlabel('Rok', fontsize=12)
            plt.ylabel(f'Średnia {target_column}', fontsize=12)
            
        else:
            # Brak danych czasowych - użyj indeksu
            plt.plot(df.index, df[target_column], linewidth=2, alpha=0.7)
            plt.title(f'Rozkład wartości - {target_column}', fontsize=14, fontweight='bold')
            plt.xlabel('Indeks', fontsize=12)
            plt.ylabel(target_column, fontsize=12)
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return _fig_to_base64(plt.gcf())
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _create_temporal_trends_chart: {e}")
        return ""


def _create_feature_importance_chart(ml_results: Dict[str, Any]) -> str:
    """Tworzy wykres ważności cech"""
    
    try:
        feature_importance = ml_results.get('feature_importance', {})
        
        if feature_importance is None or (hasattr(feature_importance, 'empty') and feature_importance.empty):
            return ""
        
        plt.figure(figsize=(10, 8))
        
        # Konwertuj DataFrame na listę
        if hasattr(feature_importance, 'to_dict'):
            # To jest DataFrame
            df_importance = feature_importance
            features = df_importance['cecha'].tolist()
            importance_values = df_importance['waznosc_srednia'].tolist()
        else:
            return ""
        
        # Sortuj według ważności
        sorted_data = sorted(zip(features, importance_values), key=lambda x: x[1], reverse=True)
        features, importance_values = zip(*sorted_data)
        
        # Ogranicz do top 10
        features = features[:10]
        importance_values = importance_values[:10]
        
        # Stwórz wykres
        bars = plt.barh(range(len(features)), importance_values, color='skyblue', alpha=0.8)
        plt.yticks(range(len(features)), features)
        plt.xlabel('Ważność cechy', fontsize=12)
        plt.title('Top 10 najważniejszych cech', fontsize=14, fontweight='bold')
        
        # Dodaj wartości na słupkach
        for i, (bar, value) in enumerate(zip(bars, importance_values)):
            plt.text(value + 0.01, i, f'{value:.3f}', va='center', fontsize=10)
        
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        return _fig_to_base64(plt.gcf())
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _create_feature_importance_chart: {e}")
        return ""


def _create_future_prediction_chart(df: pd.DataFrame, target_column: str, business_domain: str) -> str:
    """Tworzy wykres prognozy na przyszłość"""
    
    try:
        plt.figure(figsize=(12, 6))
        
        # Oblicz podstawowe statystyki
        mean_value = df[target_column].mean()
        std_value = df[target_column].std()
        
        # Stwórz dane historyczne
        historical_data = df[target_column].values
        
        # Generuj prognozę na podstawie trendu
        if len(historical_data) > 1:
            # Oblicz trend liniowy
            x = np.arange(len(historical_data))
            trend = np.polyfit(x, historical_data, 1)
            
            # Prognoza na następne 12 okresów
            future_periods = 12
            future_x = np.arange(len(historical_data), len(historical_data) + future_periods)
            future_predictions = trend[0] * future_x + trend[1]
            
            # Dodaj niepewność (95% confidence interval)
            uncertainty = std_value * 1.96
            
            # Wykres
            plt.plot(x, historical_data, 'b-', linewidth=2, label='Dane historyczne', alpha=0.8)
            plt.plot(future_x, future_predictions, 'r--', linewidth=2, label='Prognoza', alpha=0.8)
            
            # Dodaj pasmo niepewności
            plt.fill_between(future_x, 
                           future_predictions - uncertainty, 
                           future_predictions + uncertainty, 
                           alpha=0.3, color='red', label='95% przedział ufności')
            
            # Linia oddzielająca historię od prognozy
            plt.axvline(x=len(historical_data)-1, color='gray', linestyle=':', alpha=0.7)
            
        else:
            # Brak wystarczających danych - pokaż tylko średnią
            plt.axhline(y=mean_value, color='red', linestyle='--', linewidth=2, label=f'Średnia: {mean_value:.2f}')
            plt.plot(historical_data, 'b-', linewidth=2, label='Dane historyczne', alpha=0.8)
        
        plt.title(f'Prognoza {target_column} - {business_domain}', fontsize=14, fontweight='bold')
        plt.xlabel('Okres', fontsize=12)
        plt.ylabel(target_column, fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return _fig_to_base64(plt.gcf())
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _create_future_prediction_chart: {e}")
        return ""


def _create_correlations_chart(df: pd.DataFrame, target_column: str) -> str:
    """Tworzy wykres korelacji"""
    
    try:
        plt.figure(figsize=(10, 8))
        
        # Wybierz tylko kolumny numeryczne
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_column not in numeric_cols:
            numeric_cols.append(target_column)
        
        # Oblicz korelacje
        corr_matrix = df[numeric_cols].corr()
        
        # Stwórz heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, 
                   mask=mask,
                   annot=True, 
                   cmap='coolwarm', 
                   center=0,
                   square=True,
                   fmt='.2f',
                   cbar_kws={"shrink": .8})
        
        plt.title(f'Macierz korelacji - {target_column}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return _fig_to_base64(plt.gcf())
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _create_correlations_chart: {e}")
        return ""


def _create_target_distribution_chart(df: pd.DataFrame, target_column: str) -> str:
    """Tworzy wykres rozkładu wartości docelowej"""
    
    try:
        plt.figure(figsize=(10, 6))
        
        # Sprawdź typ danych
        if df[target_column].dtype in ['object', 'category']:
            # Dane kategoryczne - wykres słupkowy
            value_counts = df[target_column].value_counts()
            plt.bar(range(len(value_counts)), value_counts.values, color='lightcoral', alpha=0.8)
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
            plt.title(f'Rozkład kategorii - {target_column}', fontsize=14, fontweight='bold')
            plt.ylabel('Liczba wystąpień', fontsize=12)
            
        else:
            # Dane numeryczne - histogram
            plt.hist(df[target_column], bins=30, color='lightblue', alpha=0.8, edgecolor='black')
            plt.title(f'Rozkład wartości - {target_column}', fontsize=14, fontweight='bold')
            plt.xlabel(target_column, fontsize=12)
            plt.ylabel('Częstość', fontsize=12)
            
            # Dodaj statystyki
            mean_val = df[target_column].mean()
            std_val = df[target_column].std()
            plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Średnia: {mean_val:.2f}')
            plt.axvline(mean_val + std_val, color='orange', linestyle=':', alpha=0.7, label=f'+1σ: {mean_val + std_val:.2f}')
            plt.axvline(mean_val - std_val, color='orange', linestyle=':', alpha=0.7, label=f'-1σ: {mean_val - std_val:.2f}')
            plt.legend()
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return _fig_to_base64(plt.gcf())
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _create_target_distribution_chart: {e}")
        return ""


def _fig_to_base64(fig) -> str:
    """Konwertuje matplotlib figure na base64 string"""
    
    try:
        # Zamknij poprzednie figury
        plt.close('all')
        
        # Konwertuj na base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        
        return image_base64
        
    except Exception as e:
        print(f"🔍 DEBUG: Błąd w _fig_to_base64: {e}")
        return ""
