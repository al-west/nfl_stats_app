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

# Nettoyage et typage préventif
# --- SCORES ---
for col in ['Offense', 'Defense', 'Delta', 'Combine']:
    if col in df_scores.columns:
        df_scores[col] = pd.to_numeric(df_scores[col], errors='coerce')

if 'Year' in df_scores.columns:
    df_scores['Year_Clean'] = pd.to_numeric(df_scores['Year'], errors='coerce').fillna(0).astype(int).astype(str)
else:
    df_scores['Year_Clean'] = ""

if 'Wk' in df_scores.columns:
    df_scores['Wk_Clean'] = pd.to_numeric(df_scores['Wk'], errors='coerce').fillna(0).astype(int).astype(str)

# --- GAMECENTER ---
if 'Fantasy Points' in df_gamecenter.columns:
    df_gamecenter['Fantasy Points'] = pd.to_numeric(df_gamecenter['Fantasy Points'], errors='coerce')

if 'Year' in df_gamecenter.columns:
    df_gamecenter['Year_Clean'] = pd.to_numeric(df_gamecenter['Year'], errors='coerce').fillna(0).astype(int).astype(str)

if 'Week' in df_gamecenter.columns:
    df_gamecenter['Week_Clean'] = pd.to_numeric(df_gamecenter['Week'], errors='coerce').fillna(0).astype(int).astype(str)

# --- AWARDS ---
if 'Year' in df_awards.columns:
    df_awards['Year_Clean'] = pd.to_numeric(df_awards['Year'], errors='coerce').fillna(0).astype(int).astype(str)


# Navigation par onglets
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Scores & Matchups", 
    "⚔️ Face-à-Face", 
    "⭐ GameCenter (Joueurs)", 
    "🏆 Trophées & Awards"
])

# --- ONGLET 1 : SCORES ---
with tab1:
    st.header("Historique des Scores & Matchups")
    
    # Filtrage des vrais matchs joués pour les KPIs (Offense > 0 et Defense > 0)
    valid_games = df_scores[(df_scores['Offense'] > 0) & (df_scores['Defense'] > 0)].copy()
    
    if not valid_games.empty:
        valid_games['Combine_Calc'] = valid_games['Offense'] + valid_games['Defense']
        valid_games['Delta_Calc'] = (valid_games['Offense'] - valid_games['Defense']).abs()
        
        c1, c2, c3, c4, c5 = st.columns(5)
        
        # 1. Record Score
        max_score_row = valid_games.loc[valid_games['Offense'].idxmax()]
        c1.metric(
            label="💥 Record Score",
            value=f"{max_score_row['Offense']:.2f} pts",
            delta=f"{max_score_row['Manager']} ({max_score_row['Year_Clean']} Wk {max_score_row.get('Wk_Clean', '')})",
            delta_color="normal"
        )
        
        # 2. Pire Score (Hors 0)
        min_score_row = valid_games.loc[valid_games['Offense'].idxmin()]
        c2.metric(
            label="🧊 Pire Score All-Time",
            value=f"{min_score_row['Offense']:.2f} pts",
            delta=f"{min_score_row['Manager']} ({min_score_row['Year_Clean']} Wk {min_score_row.get('Wk_Clean', '')})",
            delta_color="inverse"
        )
        
        # 3. Plus gros Combine
        max_combine_row = valid_games.loc[valid_games['Combine_Calc'].idxmax()]
        c3.metric(
            label="🔥 Plus gros Combine",
            value=f"{max_combine_row['Combine_Calc']:.2f} pts",
            delta=f"{max_combine_row['Manager']} vs {max_combine_row['Opponent']} ({max_combine_row['Year_Clean']})",
            delta_color="normal"
        )
        
        # 4. Plus gros Écart (Blowout)
        max_delta_row = valid_games.loc[valid_games['Delta_Calc'].idxmax()]
        c4.metric(
            label="🚀 Plus gros Écart",
            value=f"{max_delta_row['Delta_Calc']:.2f} pts",
            delta=f"{max_delta_row['Manager']} vs {max_delta_row['Opponent']} ({max_delta_row['Year_Clean']})",
            delta_color="normal"
        )
        
        # 5. Plus petit Écart (Hors Tie parfait)
        strict_deltas = valid_games[valid_games['Delta_Calc'] > 0.001]
        if not strict_deltas.empty:
            min_delta_row = strict_deltas.loc[strict_deltas['Delta_Calc'].idxmin()]
            c5.metric(
                label="🔍 Plus petit Écart",
                value=f"{min_delta_row['Delta_Calc']:.2f} pts",
                delta=f"{min_delta_row['Manager']} vs {min_delta_row['Opponent']} ({min_delta_row['Year_Clean']})",
                delta_color="off"
            )

    st.markdown("---")

    # Filtres interactifs
    col1, col2 = st.columns(2)
    with col1:
        managers = ["Tous"] + sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() != ""])
        selected_manager = st.selectbox("Filtrer par Manager :", managers)
    with col2:
        years_list = sorted([y for y in df_scores['Year_Clean'].unique() if y != "0"], reverse=True)
        years = ["Toutes"] + years_list
        selected_year = st.selectbox("Filtrer par Saison :", years, key="scores_year")
    
    df_filtered_scores = df_scores.copy()
    if selected_manager != "Tous":
        df_filtered_scores = df_filtered_scores[df_filtered_scores['Manager'].astype(str) == selected_manager]
    if selected_year != "Toutes":
        df_filtered_scores = df_filtered_scores[df_filtered_scores['Year_Clean'] == selected_year]
    
    # Formatage d'affichage pour Scores
    df_display_scores = df_filtered_scores.copy()
    
    if 'Winl' in df_display_scores.columns:
        df_display_scores['Result'] = df_display_scores['Winl'].map({'W': '🟢 WIN', 'L': '🔴 LOSS', 'T': '⚪ TIE'}).fillna(df_display_scores['Winl'])
    
    rename_dict_scores = {
        'Year_Clean': 'Saison',
        'Season vs.': 'Phase',
        'Wk_Clean': 'Semaine',
        'Manager': 'Manager',
        'Offense': 'Points Marqués',
        'Result': 'Résultat',
        'Defense': 'Points Encaissés',
        'Opponent': 'Adversaire',
        'Delta': 'Écart (Delta)',
        'Combine': 'Total Match (Combine)'
    }
    
    cols_to_show_scores = [c for c in ['Year_Clean', 'Season vs.', 'Wk_Clean', 'Manager', 'Offense', 'Result', 'Defense', 'Opponent', 'Delta', 'Combine'] if c in df_display_scores.columns or c == 'Result']
    df_display_scores = df_display_scores.rename(columns=rename_dict_scores)
    show_cols = [rename_dict_scores.get(c, c) for c in cols_to_show_scores if rename_dict_scores.get(c, c) in df_display_scores.columns]
    
    st.dataframe(
        df_display_scores[show_cols],
        use_container_width=True,
        column_config={
            "Points Marqués": st.column_config.NumberColumn(format="%.2f"),
            "Points Encaissés": st.column_config.NumberColumn(format="%.2f"),
            "Écart (Delta)": st.column_config.NumberColumn(format="%.2f"),
            "Total Match (Combine)": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True
    )

# --- ONGLET 2 : FACE-A-FACE ---
with tab2:
    st.header("⚔️ Comparateur Face-à-Face / Rivalités")
    
    managers_list_h2h = sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() != ""])
    
    if len(managers_list_h2h) >= 2:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m1 = st.selectbox("Sélectionner le Manager 1 :", managers_list_h2h, index=0)
        with col_m2:
            default_m2_idx = 1 if len(managers_list_h2h) > 1 else 0
            m2 = st.selectbox("Sélectionner le Manager 2 :", managers_list_h2h, index=default_m2_idx)
            
        if m1 == m2:
            st.warning("Veuillez sélectionner deux managers différents pour afficher la rivalité.")
        else:
            h2h_df = df_scores[(df_scores['Manager'].astype(str) == m1) & (df_scores['Opponent'].astype(str) == m2) & (df_scores['Offense'] > 0)].copy()
            
            if h2h_df.empty:
                st.info(f"Aucun affrontement enregistré dans l'historique entre **{m1}** et **{m2}**.")
            else:
                wins_m1 = len(h2h_df[h2h_df['Winl'] == 'W'])
                wins_m2 = len(h2h_df[h2h_df['Winl'] == 'L'])
                ties_h2h = len(h2h_df[h2h_df['Winl'] == 'T'])
                avg_m1 = h2h_df['Offense'].mean()
                avg_m2 = h2h_df['Defense'].mean()
                
                h2h_df['Delta_Abs'] = (h2h_df['Offense'] - h2h_df['Defense']).abs()
                
                st.markdown(f"### Bilan Global : **{m1}** `{wins_m1}` - `{wins_m2}` **{m2}**" + (f" *({ties_h2h} nul(s))* " if ties_h2h > 0 else ""))
                
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Matchs Joués", f"{len(h2h_df)}")
                mc2.metric(f"Moyenne {m1}", f"{avg_m1:.2f} pts")
                mc3.metric(f"Moyenne {m2}", f"{avg_m2:.2f} pts")
                
                m1_wins_df = h2h_df[h2h_df['Winl'] == 'W']
                if not m1_wins_df.empty:
                    best_win_m1 = m1_wins_df.loc[m1_wins_df['Delta_Abs'].idxmax()]
                    mc4.metric(
                        f"Plus grosse victoire {m1}",
                        f"+{best_win_m1['Delta_Abs']:.2f} pts",
                        f"{best_win_m1['Year_Clean']} Wk {best_win_m1.get('Wk_Clean', '')}"
                    )
                else:
                    mc4.metric(f"Plus grosse victoire {m1}", "Aucune")
                
                st.markdown("---")
                st.subheader("Historique des Confrontations Directes")
                
                h2h_display = h2h_df.copy()
                h2h_display['Result'] = h2h_display['Winl'].map({'W': f'🟢 {m1}', 'L': f'🔴 {m2}', 'T': '⚪ TIE'}).fillna(h2h_display['Winl'])
                
                rename_h2h = {
                    'Year_Clean': 'Saison',
                    'Season vs.': 'Phase',
                    'Wk_Clean': 'Semaine',
                    'Offense': f'Pts {m1}',
                    'Result': 'Vainqueur',
                    'Defense': f'Pts {m2}',
                    'Delta_Abs': 'Écart'
                }
                
                cols_h2h_show = ['Year_Clean', 'Season vs.', 'Wk_Clean', 'Offense', 'Result', 'Defense', 'Delta_Abs']
                h2h_display = h2h_display[cols_h2h_show].rename(columns=rename_h2h)
                
                st.dataframe(
                    h2h_display,
                    use_container_width=True,
                    column_config={
                        f"Pts {m1}": st.column_config.NumberColumn(format="%.2f"),
                        f"Pts {m2}": st.column_config.NumberColumn(format="%.2f"),
                        "Écart": st.column_config.NumberColumn(format="%.2f"),
                    },
                    hide_index=True
                )

# --- ONGLET 3 : GAMECENTER ---
with tab3:
    st.header("Performances Individuelles des Joueurs")
    
    col1, col2 = st.columns(2)
    with col1:
        pos_list = ["Toutes"] + sorted([str(p) for p in df_gamecenter['POS'].dropna().unique() if str(p).strip() != ""])
        selected_pos = st.selectbox("Filtrer par Position (POS) :", pos_list)
    with col2:
        player_search = st.text_input("Rechercher un joueur (ex: M. Ryan) :")
        
    df_filtered_gc = df_gamecenter.copy()
    if selected_pos != "Toutes":
        df_filtered_gc = df_filtered_gc[df_filtered_gc['POS'].astype(str) == selected_pos]
    if player_search:
        df_filtered_gc = df_filtered_gc[df_filtered_gc['Player'].astype(str).str.contains(player_search, case=False, na=False)]
        
    df_display_gc = df_filtered_gc.copy()
    rename_gc = {
        'Year_Clean': 'Saison',
        'Week_Clean': 'Semaine',
        'Season vs. Playoffs': 'Phase',
        'Manager': 'Manager',
        'POS': 'POS',
        'Player': 'Joueur',
        'Opp': 'Adversaire NFL',
        'Status': 'Résultat Match',
        'Stats': 'Statistiques',
        'Fantasy Points': 'Points Fantasy'
    }
    
    cols_gc = [c for c in ['Year_Clean', 'Week_Clean', 'Season vs. Playoffs', 'Manager', 'POS', 'Player', 'Opp', 'Status', 'Stats', 'Fantasy Points'] if c in df_display_gc.columns]
    df_display_gc = df_display_gc[cols_gc].rename(columns=rename_gc)
    
    st.dataframe(
        df_display_gc,
        use_container_width=True,
        column_config={
            "Points Fantasy": st.column_config.NumberColumn(format="%.2f pts"),
        },
        hide_index=True
    )

# --- ONGLET 4 : AWARDS ---
with tab4:
    st.header("Palmarès & Récompenses")
    
    years_awards_list = sorted([y for y in df_awards['Year_Clean'].unique() if y != "0"], reverse=True)
    years_awards = ["Toutes"] + years_awards_list
    selected_award_year = st.selectbox("Filtrer par Année :", years_awards, key="awards_year")
    
    df_filtered_awards = df_awards.copy()
    if selected_award_year != "Toutes":
        df_filtered_awards = df_filtered_awards[df_filtered_awards['Year_Clean'] == selected_award_year]
        
    df_display_awards = df_filtered_awards.copy()
    
    award_cols = ['OPOY', 'DPOY', 'COY', 'WorM', 'TOY', 'Playoffs', 'PxC']
    for col in award_cols:
        if col in df_display_awards.columns:
            df_display_awards[col] = df_display_awards[col].apply(lambda x: "🏆" if str(x).strip() in ['1', '1.0'] else "-")
            
    def format_rank(val):
        if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '0.0']:
            return "-"
        try:
            r = int(float(val))
            if r == 1: return "🥇 1er"
            if r == 2: return "🥈 2ème"
            if r == 3: return "🥉 3ème"
            return f"{r}ème"
        except:
            return str(val)

    if 'Playoffs Rank' in df_display_awards.columns:
        df_display_awards['Playoffs Rank'] = df_display_awards['Playoffs Rank'].apply(format_rank)
    if 'Reg Season Rank' in df_display_awards.columns:
        df_display_awards['Reg Season Rank'] = df_display_awards['Reg Season Rank'].apply(format_rank)

    rename_awards = {
        'Year_Clean': 'Saison',
        'Player': 'Manager / Joueur',
        'Playoffs Rank': 'Rang Playoffs',
        'Reg Season Rank': 'Rang Reg. Season',
        'OPOY': 'OPOY 🏈',
        'DPOY': 'DPOY 🛡️',
        'COY': 'COY 🧢',
        'WorM': 'WorM 🪱',
        'TOY': 'TOY 🪖',
        'Playoffs': 'Playoffs 🎟️',
        'PxC': 'PxC 🎯'
    }
    
    cols_awards = [c for c in ['Year_Clean', 'Player', 'Playoffs Rank', 'Reg Season Rank', 'OPOY', 'DPOY', 'COY', 'WorM', 'TOY', 'Playoffs', 'PxC'] if c in df_display_awards.columns]
    df_display_awards = df_display_awards[cols_awards].rename(columns=rename_awards)
    
    st.dataframe(
        df_display_awards,
        use_container_width=True,
        hide_index=True
    )
