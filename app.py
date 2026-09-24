import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="NFL Fantasy League - Stats Historiques",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Stats Historiques - NFL Fantasy League")

# Chargement optimisé des données avec mise en cache
@st.cache_data
def load_data():
    file_path = "NFL Fantasy Stats.xlsx"
    
    # 1. Onglet SCORES (Colonnes A à J -> 0 à 9)
    df_scores = pd.read_excel(file_path, sheet_name="SCORES", usecols=range(10))
    
    # 2. Onglet GameCenter (Colonnes A à J -> 0 à 9)
    df_gamecenter = pd.read_excel(file_path, sheet_name="GameCenter", usecols=range(10))
    
    # 3. Onglet Awards (Colonnes A à K -> 0 à 10)
    df_awards = pd.read_excel(file_path, sheet_name="Awards", usecols=range(11))
    
    return df_scores, df_gamecenter, df_awards

# Chargement
try:
    df_scores, df_gamecenter, df_awards = load_data()
    st.sidebar.success("Données chargées avec succès !")
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Excel : {e}")
    st.stop()

# Navigation par onglets dans l'application
tab1, tab2, tab3 = st.tabs(["📊 Scores & Matchups", "⭐ GameCenter (Joueurs)", "🏆 Trophées & Awards"])

# --- ONGLET 1 : SCORES ---
with tab1:
    st.header("Historique des Scores & Matchups")
    
    col1, col2 = st.columns(2)
    with col1:
        managers = ["Tous"] + sorted([str(m) for m in df_scores['Manager'].dropna().unique()])
        selected_manager = st.selectbox("Filtrer par Manager :", managers)
    with col2:
        clean_years_scores = sorted([int(y) for y in df_scores['Year'].dropna().unique() if str(y).replace('.0','').isdigit()], reverse=True)
        years = ["Toutes"] + [str(y) for y in clean_years_scores]
        selected_year = st.selectbox("Filtrer par Saison :", years, key="scores_year")
    
    df_filtered_scores = df_scores.copy()
    if selected_manager != "Tous":
        df_filtered_scores = df_filtered_scores[df_filtered_scores['Manager'].astype(str) == selected_manager]
    if selected_year != "Toutes":
        df_filtered_scores = df_filtered_scores[df_filtered_scores['Year'].astype(str).str.replace('.0','') == selected_year]
        
    st.dataframe(df_filtered_scores, use_container_width=True)

# --- ONGLET 2 : GAMECENTER ---
with tab2:
    st.header("Performances Individuelles des Joueurs")
    
    col1, col2 = st.columns(2)
    with col1:
        pos_list = ["Toutes"] + sorted([str(p) for p in df_gamecenter['POS'].dropna().unique()])
        selected_pos = st.selectbox("Filtrer par Position (POS) :", pos_list)
    with col2:
        player_search = st.text_input("Rechercher un joueur (ex: M. Ryan) :")
        
    df_filtered_gc = df_gamecenter.copy()
    if selected_pos != "Toutes":
        df_filtered_gc = df_filtered_gc[df_filtered_gc['POS'].astype(str) == selected_pos]
    if player_search:
        df_filtered_gc = df_filtered_gc[df_filtered_gc['Player'].astype(str).str.contains(player_search, case=False, na=False)]
        
    st.dataframe(df_filtered_gc, use_container_width=True)

# --- ONGLET 3 : AWARDS ---
with tab3:
    st.header("Palmarès & Récompenses")
    
    clean_years_awards = sorted([int(y) for y in df_awards['Year'].dropna().unique() if str(y).replace('.0','').isdigit()], reverse=True)
    years_awards = ["Toutes"] + [str(y) for y in clean_years_awards]
    selected_award_year = st.selectbox("Filtrer par Année :", years_awards, key="awards_year")
    
    df_filtered_awards = df_awards.copy()
    if selected_award_year != "Toutes":
        df_filtered_awards = df_filtered_awards[df_filtered_awards['Year'].astype(str).str.replace('.0','') == selected_award_year]
        
    st.dataframe(df_filtered_awards, use_container_width=True)
