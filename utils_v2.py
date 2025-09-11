import pandas as pd
import streamlit as st
import time
from pathlib import Path

# own modules
from packages.schema_utils import infer_schema, schema_to_frame
from packages.target_utils import choose_target, TargetDecision

FOLDER = Path(__file__).resolve().parent.parent
PATH = FOLDER / "data" / "avocado.csv"

#####################
### ALL FUNCTIONS ###
#####################

def load_data(path: str | Path) -> pd.DataFrame:
    """Wczytywanie danych z pliku"""
    path = Path(path)
    try:
        df = pd.read_csv(path, low_memory=False)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Nie znaleziono pliku: {path.resolve()}") from e
    return df

def display_target_selection_with_spinner(df, schema, user_choice, strategy_label=None, openai_api_key=None):
    """Wyświetla wybór targetu z animacją podczas oczekiwania na LLM"""
    
    # Kontener na wynik
    result_container = st.container()
    
    # WAŻNE: Wywołaj choose_target z odpowiednimi parametrami w zależności od strategii
    if strategy_label == "auto_ai":
        # Sprawdź czy klucz API jest dostępny (usuń spacje)
        if not openai_api_key or not openai_api_key.strip():
            st.warning("⚠️ Brak klucza API OpenAI - przełączam na heurystykę")
            decision: TargetDecision = choose_target(
                df=df,
                schema=schema,
                user_choice="__force_heuristics__",  # fallback na heurystykę
                api_key=None
            )
        else:
            # Auto LLM - przekaż None jako user_choice żeby uruchomić LLM
            with st.spinner('🤖 Analizuję dane i konsultuję z AI...'):
                # Placeholder dla postępu
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                # Symulacja etapów (rzeczywiste wywołanie zajmie czas)
                progress_text.text('🔍 Analizuję strukturę danych...')
                progress_bar.progress(25)
                time.sleep(0.5)
                
                progress_text.text('🤖 Konsultuję z modelem AI...')
                progress_bar.progress(50)
                
                # Tutaj następuje rzeczywiste wywołanie LLM
                decision: TargetDecision = choose_target(
                    df=df,
                    schema=schema,
                    user_choice=None,  # None uruchomi LLM
                    api_key=openai_api_key
                )
            
            progress_text.text('✅ Przetwarzam odpowiedź AI...')
            progress_bar.progress(75)
            time.sleep(0.3)
            
            progress_text.text('🎯 Finalizuję wybór...')
            progress_bar.progress(100)
            time.sleep(0.3)
            
            # Wyczyść progress
            progress_text.empty()
            progress_bar.empty()
    
    elif strategy_label == "[Heurystycznie]":
        # Wybór heurystyczny - użyj specjalnego markera
        with st.spinner('🔍 Analizuję dane heurystycznie...'):
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            progress_text.text('📊 Oceniam kolumny...')
            progress_bar.progress(30)
            time.sleep(0.3)
            
            progress_text.text('🔍 Sprawdzam nazwy i typy...')
            progress_bar.progress(60)
            time.sleep(0.3)
            
            # Wywołanie z user_choice="__force_heuristics__" aby wymusić heurystykę
            decision: TargetDecision = choose_target(
                df=df,
                schema=schema,
                user_choice="__force_heuristics__"  # specjalny marker
            )
            
            progress_text.text('🎯 Finalizuję wybór heurystyczny...')
            progress_bar.progress(100)
            time.sleep(0.3)
            
            # Wyczyść progress
            progress_text.empty()
            progress_bar.empty()
            
    else:
        # Wybór użytkownika - przekaż konkretną nazwę kolumny
        decision: TargetDecision = choose_target(
            df=df,
            schema=schema,
            user_choice=user_choice,  # konkretna kolumna wybrana przez użytkownika
            api_key=None
        )
    
    # Wyświetl wyniki
    with result_container:
        source_map = {
            "user_choice": "🙋 Wybór użytkownika",
            "llm_guess": "🤖 Propozycja AI", 
            "heuristics_pick": "🔍 Analiza heurystyczna" if strategy_label == "[Heurystycznie]" else "🔄 Fallback (AI → Heurystyka)",
            "none": "❌ Brak decyzji",
        }
        
        # Metrics w kolumnach
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Źródło decyzji",
                value=source_map.get(decision.source, decision.source),
            )
        
        with col2:
            if decision.target:
                if decision.source == "user_choice":
                    target_info = f"👤 {decision.target}"
                elif decision.source == "llm_guess":
                    target_info = f"🤖 {decision.target}"
                elif decision.source == "heuristics_pick":
                    if strategy_label == "[Auto AI]":  # Auto AI wybrany ale przeszedł na heurystykę
                        target_info = f"🔄 {decision.target}"
                    elif strategy_label == "[Heurystycznie]":  # Wyraźnie wybrana heurystyka
                        target_info = f"🔍 {decision.target}"
                    else:
                        target_info = f"🔍 {decision.target}"
                else:
                    target_info = f"✅ {decision.target}"
                    
                # Dodaj info o typie kolumny
                if decision.target in schema.columns:
                    col_info = schema.columns[decision.target]
                    target_info += f" ({col_info.semantic_type})"
            else:
                target_info = "❌ Nie wybrano"
                
            st.metric(
                label="Kolumna docelowa",
                value=target_info
            )
        
        # Wyjaśnienie - bardziej szczegółowe komunikaty
        if decision.reason:
            if decision.source == "llm_guess":
                st.success(f"🤖 **AI sugeruje**: {decision.reason}")
            elif decision.source == "user_choice":
                st.info(f"👤 **Kolumna wybrana przez użytkownika**")
            elif decision.source == "heuristics_pick":
                # Sprawdź czy to był fallback po nieudanym LLM
                if strategy_label == "[Auto AI]":  # Auto AI wybrany, ale LLM nie zadziałał
                    st.warning(f"🔄 **LLM nie może się określić, wybieramy kolumnę heurystycznie**: {decision.reason}")
                elif strategy_label == "[Heurystycznie]":  # Wyraźnie wybrana heurystyka
                    st.info(f"🔍 **Heurystyka**: {decision.reason}")
                else:
                    st.warning(f"🔍 **Heurystyka**: {decision.reason}")
            else:
                st.error(f"❌ **Problem**: {decision.reason}")
        
        return decision

############
### MAIN ###
############

if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="ML Data Analyzer",
        page_icon="🤖"
    )
    
    st.title("🤖 Rozkmiamy każde dane!")
    st.markdown("*Automatyczna analiza danych z inteligentnym wyborem kolumny docelowej*")

    # Inicjalizacja session state - BARDZO WAŻNE!
    if 'analysis_triggered' not in st.session_state:
        st.session_state.analysis_triggered = False
    if 'last_analysis_params' not in st.session_state:
        st.session_state.last_analysis_params = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    # Wczytywanie danych
    try:
        df = load_data(PATH)
        data_loaded = True
        st.success(f"✅ Załadowano dane: {df.shape[0]} wierszy, {df.shape[1]} kolumn")
    except FileNotFoundError as e:
        st.error(f"❌ Nie znaleziono pliku: {PATH.resolve()}")
        data_loaded = False

    if data_loaded:   
        schema = infer_schema(df)
        summary = schema_to_frame(schema)
    else:
        schema = None
        summary = None

    ### SIDEBAR ###
    with st.sidebar:
        st.header("⚙️ Ustawienia")
        
        if data_loaded:
            # Sortowanie podsumowania
            st.subheader("📊 Podsumowanie danych")
            select_column_summary_schema = st.selectbox(
                "Sortuj kolumny według:",
                options=summary.columns,
                index=summary.columns.get_loc("missing_ratio"),
                help="Wybierz metrykę do sortowania kolumn w podsumowaniu"
            )

            # Wybór targetu
            st.subheader("🎯 Kolumna docelowa")
            # Dodajemy opcję heurystyczną
            manual_option = ["[Auto AI]", "[Heurystycznie]"] + list(df.columns)
            
            user_choice_label = st.selectbox(
                "Wybierz strategię:",
                options=manual_option,
                index=0,  # zawsze zaczynamy od [Auto AI]
                key="strategy_selector",
                help="🤖 [Auto AI] - inteligentny wybór przez AI\n🔍 [Heurystycznie] - analiza heurystyczna\n📋 Lub wybierz konkretną kolumnę"
            )
                
            # Przycisk uruchomienia analizy
            run_analysis = st.button(
                "🚀 Uruchom analizę",
                type="primary",
                help="Kliknij aby uruchomić analizę według wybranej strategii"
            )
            
            # KLUCZOWA LOGIKA: Zapisz parametry analizy TYLKO po naciśnięciu przycisku
            if run_analysis:
                # Określ user_choice na podstawie wybranej strategii
                if user_choice_label == "[Auto AI]":
                    actual_user_choice = None  # None uruchomi LLM
                elif user_choice_label == "[Heurystycznie]":
                    actual_user_choice = "__force_heuristics__"  # marker heurystyki
                else:
                    actual_user_choice = user_choice_label  # konkretna kolumna
                
                # Zapisz parametry analizy
                analysis_params = {
                    'strategy_label': user_choice_label,
                    'user_choice': actual_user_choice,
                }
                
                st.session_state.analysis_triggered = True
                st.session_state.last_analysis_params = analysis_params
                st.session_state.analysis_result = None  # wyczyść poprzedni wynik
                
                st.success(f"🚀 Uruchamianie analizy: {user_choice_label}")
                
            # Info o strategiach
            st.markdown("---")
            st.markdown("### 📝 Strategie wyboru:")
            st.markdown("""
            - **🤖 Auto AI**: AI analizuje dane i proponuje najlepszą kolumnę
            - **🔍 Heurystycznie**: Wybór na podstawie nazw i typów kolumn
            - **👤 Ręczny**: Wybierz konkretną kolumnę z listy
            
            **💡 Zmiana strategii nie uruchamia analizy!**  
            Aby uruchomić, naciśnij przycisk "🚀 Uruchom analizę"
            """)
            
        else:
            st.info("⏳ Załaduj poprawnie dane, aby wybrać kolumnę docelową")

    ### TABS ###
    tab_summary, tab_selection, tab_debug = st.tabs([
        "📊 Podsumowanie danych", 
        "🎯 Wybór targetu",
        "🔧 Debug & Logs"
    ])

    with tab_summary:
        if data_loaded:
            st.markdown(f"### 📊 Analiza kolumn (sortowanie: **{select_column_summary_schema}**)")
            
            # Dodatkowe metryki
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Wiersze", f"{df.shape[0]:,}")
            with col2:
                st.metric("Kolumny", df.shape[1])
            with col3:
                missing_cols = sum(1 for col in schema.columns.values() if col.missing_ratio > 0.1)
                st.metric("Kolumny z brakami >10%", missing_cols)
            with col4:
                unique_cols = len(schema.primary_key_candidates)
                st.metric("Kandydaci na klucz", unique_cols)
            
            # Główne podsumowanie
            st.dataframe(
                summary.sort_values(select_column_summary_schema, ascending=False), 
                use_container_width=True,
                height=400
            )
            
            # Notatki
            if schema.notes:
                st.markdown("### ⚠️ Zauważone problemy:")
                for note in schema.notes:
                    st.warning(note)
                    
        else:
            st.warning("❌ Brak danych – nie można wyświetlić podsumowania")

    with tab_selection:
        st.markdown("## 🎯 Inteligentny wybór kolumny docelowej")
        
        if data_loaded:
            # KLUCZOWA LOGIKA: Uruchom analizę TYLKO jeśli została wywołana przyciskiem
            if st.session_state.get('analysis_triggered', False) and st.session_state.get('last_analysis_params'):
                
                # Pobierz parametry ostatniej analizy
                params = st.session_state.last_analysis_params
                strategy_label = params['strategy_label']
                user_choice = params['user_choice']
                
                # Uruchom analizę TYLKO RAZ (po naciśnięciu przycisku)
                if st.session_state.analysis_result is None:
                    st.info(f"🚀 Uruchamianie analizy: **{strategy_label}**")
                    
                    # Tutaj FAKTYCZNIE następuje analiza (w tym LLM jeśli [Auto AI])
                    decision = display_target_selection_with_spinner(
                        df, schema, user_choice, strategy_label
                    )
                    
                    # Zapisz wynik żeby nie uruchamiać ponownie
                    st.session_state.analysis_result = decision
                    st.session_state.analysis_triggered = False  # resetuj flagę
                
                else:
                    # Wyświetl zapisany wynik (bez ponownej analizy)
                    st.success("✅ Wyniki analizy (zapisane):")
                    decision = st.session_state.analysis_result
                    
                    # Wyświetl wyniki ponownie (bez spinnera)
                    source_map = {
                        "user_choice": "🙋 Wybór użytkownika",
                        "llm_guess": "🤖 Propozycja AI", 
                        "heuristics_pick": "🔍 Analiza heurystyczna",
                        "none": "❌ Brak decyzji",
                    }
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Źródło decyzji", source_map.get(decision.source, decision.source))
                    
                    with col2:
                        if decision.target:
                            target_info = f"✅ {decision.target}"
                            if decision.target in schema.columns:
                                col_info = schema.columns[decision.target]
                                target_info += f" ({col_info.semantic_type})"
                        else:
                            target_info = "❌ Nie wybrano"
                        st.metric("Kolumna docelowa", target_info)
                    
                    if decision.reason:
                        if decision.source == "llm_guess":
                            st.success(f"🤖 **AI sugeruje**: {decision.reason}")
                        elif decision.source == "user_choice":
                            st.info(f"👤 **Kolumna wybrana przez użytkownika**")
                        elif decision.source == "heuristics_pick":
                            st.info(f"🔍 **Heurystyka**: {decision.reason}")
                        else:
                            st.error(f"❌ **Problem**: {decision.reason}")
                
            else:
                # Pokaż komunikat zachęcający do uruchomienia analizy
                st.info("🎯 **Wybierz strategię w sidebarze i kliknij '🚀 Uruchom analizę' aby rozpocząć**")
                
                # Pokaż informacje o dostępnych opcjach
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 🤖 Auto AI")
                    st.markdown("""
                    - AI analizuje dane i proponuje najlepszą kolumnę
                    - Używa zaawansowanych algorytmów ML
                    - Pokazuje szczegółowe uzasadnienie
                    - **⚠️ Wymaga wywołania LLM**
                    """)
                
                with col2:
                    st.markdown("### 🔍 Heurystycznie")
                    st.markdown("""
                    - Analiza na podstawie nazw kolumn
                    - Ocena typów danych i jakości
                    - Szybkie wyniki bez AI
                    - **✅ Bez wywołania LLM**
                    """)
                
                with col3:
                    st.markdown("### 👤 Ręczny wybór")
                    st.markdown("""
                    - Wybierz konkretną kolumnę z listy
                    - Natychmiastowe wyniki
                    - Pełna kontrola nad wyborem
                    - **✅ Bez wywołania LLM**
                    """)
                    
        else:
            st.warning("❌ Brak danych – nie można uruchomić analizy")

    with tab_debug:
        if data_loaded:
            st.markdown("### 🔧 Debug & Logs")
            
            # Session state debug
            st.markdown("#### Session State:")
            debug_info = {
                "analysis_triggered": st.session_state.get('analysis_triggered', 'Not set'),
                "last_analysis_params": st.session_state.get('last_analysis_params', 'Not set'),
                "analysis_result": "Present" if st.session_state.get('analysis_result') else "None",
            }
            st.json(debug_info)
            
            # Schema debug
            if st.checkbox("Pokaż pełny schemat"):
                st.markdown("#### Schemat danych:")
                st.json({
                    "n_rows": schema.n_rows,
                    "n_cols": schema.n_cols,
                    "primary_key_candidates": schema.primary_key_candidates,
                    "notes": schema.notes
                })
                
            # Button to reset analysis
            if st.button("🔄 Resetuj analizę"):
                st.session_state.analysis_triggered = False
                st.session_state.last_analysis_params = None
                st.session_state.analysis_result = None
                st.rerun()
        else:
            st.info("⏳ Brak danych do debugowania")