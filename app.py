import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="NFL Fantasy League - Stats Historiques",
    page_icon="🏈",
    layout="wide"
)

# Injection CSS : Empêche le clavier mobile iOS/Android de s'ouvrir sur les menus déroulants (selectbox)
st.markdown("""
    <style>
    div[data-baseweb="select"] input {
        pointer-events: none !important;
        caret-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏈 Stats Historiques - NFL Fantasy League")

# Chargement optimisé des données avec mise en cache
@st.cache_data
def load_data():
    file_path = "NFL Fantasy Stats.xlsx"
    
    # 1. Onglet SCORES
    df_scores = pd.read_excel(file_path, sheet_name="SCORES", usecols=range(10))
    
    # 2. Onglet GameCenter
    df_gamecenter = pd.read_excel(file_path, sheet_name="GameCenter", usecols=range(10))
    
    # 3. Onglet Awards
    df_awards = pd.read_excel(file_path, sheet_name="Awards", usecols=range(11))
    
    # Nettoyage des espaces invisibles dans les entêtes
    df_scores.columns = df_scores.columns.astype(str).str.strip()
    df_gamecenter.columns = df_gamecenter.columns.astype(str).str.strip()
    df_awards.columns = df_awards.columns.astype(str).str.strip()
    
    return df_scores, df_gamecenter, df_awards

# Chargement
try:
    df_scores, df_gamecenter, df_awards = load_data()
    st.sidebar.success("Données chargées avec succès !")
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Excel : {e}")
    st.stop()

# --- NETTOYAGE SCORES ---
for col in ['Offense', 'Defense', 'Delta', 'Combine']:
    if col in df_scores.columns:
        df_scores[col] = pd.to_numeric(df_scores[col], errors='coerce')

if 'Year' in df_scores.columns:
    df_scores['Year_Clean'] = pd.to_numeric(df_scores['Year'], errors='coerce').fillna(0).astype(int).astype(str)
else:
    df_scores['Year_Clean'] = ""

wk_col_candidates = [c for c in df_scores.columns if 'wk' in c.lower() or 'week' in c.lower()]
if wk_col_candidates:
    df_scores['Wk_Clean'] = pd.to_numeric(df_scores[wk_col_candidates[0]], errors='coerce').fillna(0).astype(int).astype(str)
else:
    df_scores['Wk_Clean'] = ""

season_col = next((c for c in df_scores.columns if 'season' in c.lower() and 'playoff' in c.lower() or c.lower() in ['season vs.', 'season vs']), None)

if 'WinLose' not in df_scores.columns:
    df_scores['WinLose'] = df_scores.apply(
        lambda r: 'W' if r['Offense'] > r['Defense'] else ('L' if r['Offense'] < r['Defense'] else 'T'), axis=1
    )

# --- NETTOYAGE GAMECENTER ---
if 'Fantasy Points' in df_gamecenter.columns:
    df_gamecenter['Fantasy Points'] = pd.to_numeric(df_gamecenter['Fantasy Points'], errors='coerce')

if 'Year' in df_gamecenter.columns:
    df_gamecenter['Year_Clean'] = pd.to_numeric(df_gamecenter['Year'], errors='coerce').fillna(0).astype(int).astype(str)

gc_wk_candidates = [c for c in df_gamecenter.columns if 'week' in c.lower() or 'wk' in c.lower()]
if gc_wk_candidates:
    df_gamecenter['Week_Clean'] = pd.to_numeric(df_gamecenter[gc_wk_candidates[0]], errors='coerce').fillna(0).astype(int).astype(str)
else:
    df_gamecenter['Week_Clean'] = ""

# Normalisation des positions et séparation Titulaires / Banc
bench_positions = ['BN', 'BENCH', 'BNCH', 'BE']
if 'POS' in df_gamecenter.columns:
    df_gamecenter['POS_Clean'] = df_gamecenter['POS'].astype(str).str.strip().str.upper().apply(
        lambda x: 'DEF' if x in ['DEF', 'D/ST', 'DST'] else x
    )
    is_bench_mask = df_gamecenter['POS_Clean'].isin(bench_positions)
    df_gc_starters = df_gamecenter[~is_bench_mask].copy()
    df_gc_bench = df_gamecenter[is_bench_mask].copy()
else:
    df_gc_starters = df_gamecenter.copy()
    df_gc_bench = pd.DataFrame()

# --- NETTOYAGE AWARDS ---
if 'Year' in df_awards.columns:
    df_awards['Year_Clean'] = pd.to_numeric(df_awards['Year'], errors='coerce').fillna(0).astype(int).astype(str)

# Fonctions de formatage des rangs et trophées
def format_rank_playoffs(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', '0', '0.0']:
        return "-"
    try:
        r = int(float(val))
        if r == 1: return "🏆 1er"
        if r == 2: return "🥈 2ème"
        if r == 3: return "🥉 3ème"
        return f"{r}ème"
    except:
        return str(val)

def format_rank_reg(val):
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

award_emojis = {
    'OPOY': '🏈',
    'DPOY': '🛡️',
    'COY': '🧢',
    'WorM': '🪱',
    'TOY': '🪖',
    'Playoffs': '🎟️',
    'PxC': '🎯'
}

# Navigation par onglets
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Scores & Matchups", 
    "⚔️ Face-à-Face & Rivalités", 
    "👤 Profils Managers",
    "🏅 Livre des Records",
    "⭐ GameCenter (Joueurs)", 
    "🏆 Trophées & Awards"
])

# --- ONGLET 1 : SCORES & MATCHUPS ---
with tab1:
    st.header("Historique des Scores & Matchups")
    
    valid_games = df_scores[(df_scores['Offense'] > 0) & (df_scores['Defense'] > 0)].copy()
    
    if not valid_games.empty:
        valid_games['Combine_Calc'] = valid_games['Offense'] + valid_games['Defense']
        valid_games['Delta_Calc'] = (valid_games['Offense'] - valid_games['Defense']).abs()
        
        c1, c2, c3, c4, c5 = st.columns(5)
        
        max_score_row = valid_games.loc[valid_games['Offense'].idxmax()]
        c1.metric(
            label="💥 Record Score",
            value=f"{max_score_row['Offense']:.2f} pts",
            delta=f"{max_score_row['Manager']} ({max_score_row['Year_Clean']} Wk {max_score_row.get('Wk_Clean', '')})",
            delta_color="normal"
        )
        
        min_score_row = valid_games.loc[valid_games['Offense'].idxmin()]
        c2.metric(
            label="🧊 Pire Score All-Time",
            value=f"{min_score_row['Offense']:.2f} pts",
            delta=f"{min_score_row['Manager']} ({min_score_row['Year_Clean']} Wk {min_score_row.get('Wk_Clean', '')})",
            delta_color="inverse"
        )
        
        max_combine_row = valid_games.loc[valid_games['Combine_Calc'].idxmax()]
        c3.metric(
            label="🔥 Plus gros Combine",
            value=f"{max_combine_row['Combine_Calc']:.2f} pts",
            delta=f"{max_combine_row['Manager']} vs {max_combine_row['Opponent']} ({max_combine_row['Year_Clean']})",
            delta_color="normal"
        )
        
        max_delta_row = valid_games.loc[valid_games['Delta_Calc'].idxmax()]
        c4.metric(
            label="🚀 Plus gros Écart",
            value=f"{max_delta_row['Delta_Calc']:.2f} pts",
            delta=f"{max_delta_row['Manager']} vs {max_delta_row['Opponent']} ({max_delta_row['Year_Clean']})",
            delta_color="normal"
        )
        
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

    col1, col2 = st.columns(2)
    with col1:
        managers = ["Tous"] + sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() not in ["", "nan"]])
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
    
    df_display_scores = df_filtered_scores.copy()
    df_display_scores['Result'] = df_display_scores['WinLose'].map({'W': '🟢 WIN', 'L': '🔴 LOSS', 'T': '⚪ TIE'}).fillna(df_display_scores['WinLose'])
    
    rename_dict_scores = {
        'Year_Clean': 'Saison',
        season_col: 'Phase',
        'Wk_Clean': 'Semaine',
        'Manager': 'Manager',
        'Offense': 'Points Marqués',
        'Result': 'Résultat',
        'Defense': 'Points Encaissés',
        'Opponent': 'Adversaire',
        'Delta': 'Écart (Delta)',
        'Combine': 'Total Match (Combine)'
    }
    
    cols_to_show_scores = [c for c in ['Year_Clean', season_col, 'Wk_Clean', 'Manager', 'Offense', 'Result', 'Defense', 'Opponent', 'Delta', 'Combine'] if c and c in df_display_scores.columns or c == 'Result']
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

    st.markdown("---")
    st.subheader("🍀 Indice de Chance & Poisse (Luck Index - Attaque vs. Défense Subie)")
    
    # Graphique Scatter Plot Luck Index
    df_luck = df_scores[df_scores['Offense'] > 0].groupby(['Manager', 'Year_Clean']).agg(
        Pts_Marques=('Offense', 'sum'),
        Pts_Encaisses=('Defense', 'sum'),
        Victoires=('WinLose', lambda x: (x == 'W').sum()),
        Defaites=('WinLose', lambda x: (x == 'L').sum()),
        Nuls=('WinLose', lambda x: (x == 'T').sum())
    ).reset_index()
    
    if not df_luck.empty:
        df_luck['Record'] = df_luck.apply(
            lambda r: f"{r['Victoires']}W-{r['Defaites']}L" + (f"-{r['Nuls']}T" if r['Nuls'] > 0 else ""), axis=1
        )
        avg_pts_m = df_luck['Pts_Marques'].mean()
        avg_pts_e = df_luck['Pts_Encaisses'].mean()
        
        fig_luck = px.scatter(
            df_luck,
            x='Pts_Marques',
            y='Pts_Encaisses',
            color='Manager',
            text='Record',
            hover_data={'Manager': True, 'Year_Clean': True, 'Record': True, 'Pts_Marques': ':.2f', 'Pts_Encaisses': ':.2f'},
            labels={'Pts_Marques': 'Points Marqués (Attaque)', 'Pts_Encaisses': 'Points Encaissés (Défense Subie)'}
        )
        fig_luck.add_vline(x=avg_pts_m, line_dash="dash", line_color="gray", annotation_text="Moyenne Ligue Attaque")
        fig_luck.add_hline(y=avg_pts_e, line_dash="dash", line_color="gray", annotation_text="Moyenne Ligue Défense Subie")
        fig_luck.update_traces(textposition='top center', marker=dict(size=10))
        fig_luck.update_layout(height=500, margin=dict(l=40, r=40, t=30, b=40))
        st.plotly_chart(fig_luck, use_container_width=True)


# --- ONGLET 2 : FACE-A-FACE & RIVALITÉS ---
with tab2:
    st.header("⚔️ Comparateur Face-à-Face & Rivalités")
    
    managers_list_h2h = sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() not in ["", "nan"]])
    
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
                wins_m1 = len(h2h_df[h2h_df['WinLose'] == 'W'])
                wins_m2 = len(h2h_df[h2h_df['WinLose'] == 'L'])
                ties_h2h = len(h2h_df[h2h_df['WinLose'] == 'T'])
                avg_m1 = h2h_df['Offense'].mean()
                avg_m2 = h2h_df['Defense'].mean()
                
                h2h_df['Delta_Abs'] = (h2h_df['Offense'] - h2h_df['Defense']).abs()
                
                st.markdown(f"### Bilan Global : **{m1}** `{wins_m1}` - `{wins_m2}` **{m2}**" + (f" *({ties_h2h} nul(s))* " if ties_h2h > 0 else ""))
                
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Matchs Joués", f"{len(h2h_df)}")
                mc2.metric(f"Moyenne {m1}", f"{avg_m1:.2f} pts")
                mc3.metric(f"Moyenne {m2}", f"{avg_m2:.2f} pts")
                
                m1_wins_df = h2h_df[h2h_df['WinLose'] == 'W']
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
                h2h_display['Result'] = h2h_display['WinLose'].map({'W': f'🟢 {m1}', 'L': f'🔴 {m2}', 'T': '⚪ TIE'}).fillna(h2h_display['WinLose'])
                
                rename_h2h = {
                    'Year_Clean': 'Saison',
                    season_col: 'Phase',
                    'Wk_Clean': 'Semaine',
                    'Offense': f'Pts {m1}',
                    'Result': 'Vainqueur',
                    'Defense': f'Pts {m2}',
                    'Delta_Abs': 'Écart'
                }
                
                cols_candidates_h2h = ['Year_Clean', season_col, 'Wk_Clean', 'Offense', 'Result', 'Defense', 'Delta_Abs']
                cols_h2h_show = [c for c in cols_candidates_h2h if c and c in h2h_display.columns]
                
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

    st.markdown("---")
    st.subheader("🔥 Matrice de Rivalité Globale (Tous les Managers Historiques)")
    
    # Heatmap H2H globale
    all_historical_managers = sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() not in ["", "nan"]])
    
    matrix_text = []
    matrix_pct = []
    
    for mgr1 in all_historical_managers:
        row_text = []
        row_pct = []
        for mgr2 in all_historical_managers:
            if mgr1 == mgr2:
                row_text.append("-")
                row_pct.append(np.nan)
            else:
                df_pair = df_scores[(df_scores['Manager'] == mgr1) & (df_scores['Opponent'] == mgr2) & (df_scores['Offense'] > 0)]
                if df_pair.empty:
                    row_text.append("N/A")
                    row_pct.append(np.nan)
                else:
                    w = (df_pair['WinLose'] == 'W').sum()
                    l = (df_pair['WinLose'] == 'L').sum()
                    t = (df_pair['WinLose'] == 'T').sum()
                    
                    emoji = "🟢" if w > l else ("🔴" if w < l else "🤝")
                    pct = (w + 0.5 * t) / len(df_pair) * 100
                    txt = f"{emoji} {w}-{l}" + (f"-{t}" if t > 0 else "")
                    
                    row_text.append(txt)
                    row_pct.append(pct)
        matrix_text.append(row_text)
        matrix_pct.append(row_pct)
        
    fig_heatmap = px.imshow(
        matrix_pct,
        x=all_historical_managers,
        y=all_historical_managers,
        labels=dict(x="Adversaire", y="Manager", color="% Victoires"),
        text_auto=False,
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    fig_heatmap.update_traces(
        text=matrix_text,
        texttemplate="%{text}",
        hovertemplate="Manager: %{y}<br>Adversaire: %{x}<br>Bilan: %{text}<extra></extra>"
    )
    fig_heatmap.update_layout(height=600, margin=dict(l=40, r=40, t=30, b=40))
    st.plotly_chart(fig_heatmap, use_container_width=True)


# --- ONGLET 3 : PROFILS MANAGERS ---
with tab3:
    st.header("👤 Profil & CV de Manager")
    
    managers_list_prof = sorted([str(m) for m in df_scores['Manager'].dropna().unique() if str(m).strip() not in ["", "nan"]])
    selected_prof = st.selectbox("Sélectionner un Manager :", managers_list_prof, key="prof_manager_select")
    
    m_scores = df_scores[(df_scores['Manager'].astype(str) == selected_prof) & (df_scores['Offense'] > 0)].copy()
    
    if m_scores.empty:
        st.info("Aucune statistique enregistrée pour ce manager.")
    else:
        wins = len(m_scores[m_scores['WinLose'] == 'W'])
        losses = len(m_scores[m_scores['WinLose'] == 'L'])
        ties = len(m_scores[m_scores['WinLose'] == 'T'])
        total_games = len(m_scores)
        win_pct = (wins / total_games * 100) if total_games > 0 else 0
        
        total_pts = m_scores['Offense'].sum()
        avg_pts = m_scores['Offense'].mean()
        
        best_week = m_scores.loc[m_scores['Offense'].idxmax()]
        worst_week = m_scores.loc[m_scores['Offense'].idxmin()]
        
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        col_p1.metric(
            label="Bilan All-Time",
            value=f"{wins}W - {losses}L" + (f" - {ties}T" if ties > 0 else ""),
            delta=f"{win_pct:.1f}% W/L",
            delta_color="normal" if win_pct >= 50 else "inverse"
        )
        
        col_p2.metric(
            label="Moyenne Points / Match",
            value=f"{avg_pts:.2f} pts",
            delta=f"Total: {total_pts:.1f} pts",
            delta_color="off"
        )
        
        col_p3.metric(
            label="Meilleure Semaine",
            value=f"{best_week['Offense']:.2f} pts",
            delta=f"{best_week['Year_Clean']} Wk {best_week.get('Wk_Clean', '')}",
            delta_color="normal"
        )
        
        col_p4.metric(
            label="Pire Semaine",
            value=f"{worst_week['Offense']:.2f} pts",
            delta=f"{worst_week['Year_Clean']} Wk {worst_week.get('Wk_Clean', '')}",
            delta_color="inverse"
        )
        
        st.markdown("---")
        
        # SUB-TABS DANS LE PROFIL MANAGER
        p_subtab1, p_subtab2, p_subtab3, p_subtab4 = st.tabs([
            "🌟 Roster Snapshot (All-Star)",
            "🕸️ Balance Positionnelle (Spider Chart)",
            "📈 Évolution W/L & Scoring",
            "🏆 Trophées & Bilan Saison"
        ])
        
        # 1. ROSTER SNAPSHOT ALL-STAR
        with p_subtab1:
            st.subheader("🌟 Roster Snapshot Titulaire par Saison")
            
            mgr_years = sorted([y for y in m_scores['Year_Clean'].unique() if y != "0"], reverse=True)
            if mgr_years:
                selected_roster_year = st.selectbox("Choisir la Saison :", mgr_years, key="roster_year_select")
                
                # Badges de fin de saison (Awards)
                m_awards_yr = df_awards[(df_awards['Player'].astype(str) == selected_prof) & (df_awards['Year_Clean'] == selected_roster_year)]
                
                reg_rank_str = "-"
                playoff_rank_str = "-"
                if not m_awards_yr.empty:
                    row_a = m_awards_yr.iloc[0]
                    reg_rank_str = format_rank_reg(row_a.get('Reg Season Rank', None))
                    playoff_rank_str = format_rank_playoffs(row_a.get('Playoffs Rank', None))
                    
                b_col1, b_col2 = st.columns(2)
                b_col1.metric(f"Rang Saison Régulière ({selected_roster_year})", reg_rank_str)
                b_col2.metric(f"Rang Playoffs Final ({selected_roster_year})", playoff_rank_str)
                
                # All-Star Lineup (Titulaires uniquement, POS != BN)
                df_m_starters = df_gc_starters[
                    (df_gc_starters['Manager'].astype(str) == selected_prof) & 
                    (df_gc_starters['Year_Clean'] == selected_roster_year)
                ].copy()
                
                if not df_m_starters.empty:
                    player_summary = df_m_starters.groupby(['Player', 'POS_Clean']).agg(
                        Total_Pts=('Fantasy Points', 'sum'),
                        Games=('Fantasy Points', 'count')
                    ).reset_index()
                    
                    all_star_lineup = []
                    used_players = set()
                    
                    # QB1
                    qbs = player_summary[player_summary['POS_Clean'] == 'QB'].sort_values(by='Total_Pts', ascending=False)
                    if not qbs.empty:
                        row = qbs.iloc[0]
                        all_star_lineup.append(('🎯 QB1', row['Player'], row['Total_Pts'], row['Games']))
                        used_players.add(row['Player'])
                        
                    # RB1 & RB2
                    rbs = player_summary[player_summary['POS_Clean'] == 'RB'].sort_values(by='Total_Pts', ascending=False)
                    for idx, slot in enumerate(['🏃 RB1', '🏃 RB2']):
                        if len(rbs) > idx:
                            row = rbs.iloc[idx]
                            all_star_lineup.append((slot, row['Player'], row['Total_Pts'], row['Games']))
                            used_players.add(row['Player'])
                            
                    # WR1 & WR2
                    wrs = player_summary[player_summary['POS_Clean'] == 'WR'].sort_values(by='Total_Pts', ascending=False)
                    for idx, slot in enumerate(['🙌 WR1', '🙌 WR2']):
                        if len(wrs) > idx:
                            row = wrs.iloc[idx]
                            all_star_lineup.append((slot, row['Player'], row['Total_Pts'], row['Games']))
                            used_players.add(row['Player'])
                            
                    # TE1
                    tes = player_summary[player_summary['POS_Clean'] == 'TE'].sort_values(by='Total_Pts', ascending=False)
                    if not tes.empty:
                        row = tes.iloc[0]
                        all_star_lineup.append(('⚡ TE1', row['Player'], row['Total_Pts'], row['Games']))
                        used_players.add(row['Player'])
                        
                    # FLEX (Top RB/WR/TE restant)
                    flex_candidates = player_summary[
                        (player_summary['POS_Clean'].isin(['RB', 'WR', 'TE'])) & 
                        (~player_summary['Player'].isin(used_players))
                    ].sort_values(by='Total_Pts', ascending=False)
                    if not flex_candidates.empty:
                        row = flex_candidates.iloc[0]
                        all_star_lineup.append((f"🔀 FLEX ({row['POS_Clean']})", row['Player'], row['Total_Pts'], row['Games']))
                        used_players.add(row['Player'])
                        
                    # K1
                    ks = player_summary[player_summary['POS_Clean'] == 'K'].sort_values(by='Total_Pts', ascending=False)
                    if not ks.empty:
                        row = ks.iloc[0]
                        all_star_lineup.append(('🦶 K1', row['Player'], row['Total_Pts'], row['Games']))
                        used_players.add(row['Player'])
                        
                    # DEF1
                    defs = player_summary[player_summary['POS_Clean'] == 'DEF'].sort_values(by='Total_Pts', ascending=False)
                    if not defs.empty:
                        row = defs.iloc[0]
                        all_star_lineup.append(('🛡️ DEF1', row['Player'], row['Total_Pts'], row['Games']))
                        used_players.add(row['Player'])
                        
                    df_lineup_disp = pd.DataFrame(all_star_lineup, columns=['Poste', 'Joueur', 'Points Marqués (Titulaire)', 'Matchs Joués'])
                    st.dataframe(
                        df_lineup_disp,
                        use_container_width=True,
                        hide_index=True,
                        column_config={"Points Marqués (Titulaire)": st.column_config.NumberColumn(format="%.2f pts")}
                    )
                else:
                    st.info("Données GameCenter indisponibles pour ce manager sur cette saison.")

        # 2. SPIDER CHART / RADAR CHART
        with p_subtab2:
            st.subheader("🕸️ Balance Positionnelle (Radar Chart - Titulaires)")
            
            pos_order = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
            df_starters_pos = df_gc_starters[df_gc_starters['POS_Clean'].isin(pos_order)].copy()
            
            if not df_starters_pos.empty:
                pos_totals = df_starters_pos.groupby(['Manager', 'POS_Clean'])['Fantasy Points'].sum().reset_index()
                pivot_pos = pos_totals.pivot(index='Manager', columns='POS_Clean', values='Fantasy Points').fillna(0)
                
                for p in pos_order:
                    if p not in pivot_pos.columns:
                        pivot_pos[p] = 0.0
                pivot_pos = pivot_pos[pos_order]
                
                min_vals = pivot_pos.min()
                max_vals = pivot_pos.max()
                
                norm_pivot = pivot_pos.copy()
                for p in pos_order:
                    span = max_vals[p] - min_vals[p]
                    norm_pivot[p] = (pivot_pos[p] - min_vals[p]) / span * 100 if span > 0 else 100.0
                    
                col_radar_opt, _ = st.columns([1, 2])
                with col_radar_opt:
                    other_mgrs = ["Moyenne de la Ligue"] + [m for m in managers_list_prof if m != selected_prof]
                    compare_target = st.selectbox("Comparer avec :", other_mgrs, key="compare_radar_select")
                    
                fig_radar = go.Figure()
                
                # Courbe du manager sélectionné
                r_mgr = norm_pivot.loc[selected_prof, pos_order].tolist() if selected_prof in norm_pivot.index else [0]*6
                raw_mgr = pivot_pos.loc[selected_prof, pos_order].tolist() if selected_prof in pivot_pos.index else [0]*6
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_mgr + [r_mgr[0]],
                    theta=pos_order + [pos_order[0]],
                    fill='toself',
                    name=selected_prof,
                    opacity=0.7,
                    text=raw_mgr + [raw_mgr[0]],
                    hovertemplate='%{theta}: %{text:.1f} pts<extra></extra>'
                ))
                
                # Superposition comparaison
                if compare_target == "Moyenne de la Ligue":
                    avg_raw = pivot_pos.mean().loc[pos_order].tolist()
                    avg_norm = norm_pivot.mean().loc[pos_order].tolist()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=avg_norm + [avg_norm[0]],
                        theta=pos_order + [pos_order[0]],
                        fill='toself',
                        name="Moyenne Ligue",
                        opacity=0.3,
                        line=dict(dash='dash', color='gray'),
                        text=avg_raw + [avg_raw[0]],
                        hovertemplate='%{theta}: %{text:.1f} pts (Moy)<extra></extra>'
                    ))
                elif compare_target in pivot_pos.index:
                    r_comp = norm_pivot.loc[compare_target, pos_order].tolist()
                    raw_comp = pivot_pos.loc[compare_target, pos_order].tolist()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=r_comp + [r_comp[0]],
                        theta=pos_order + [pos_order[0]],
                        fill='toself',
                        name=compare_target,
                        opacity=0.4,
                        line=dict(dash='dot'),
                        text=raw_comp + [raw_comp[0]],
                        hovertemplate='%{theta}: %{text:.1f} pts<extra></extra>'
                    ))
                    
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
                    showlegend=True,
                    height=450,
                    margin=dict(l=40, r=40, t=30, b=30)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        # 3. ÉVOLUTION W/L & SCORING
        with p_subtab3:
            st.subheader("📈 Évolution du % W/L et des Points Marqués All-Time")
            
            wl_season = m_scores.groupby('Year_Clean').agg(
                W=('WinLose', lambda x: (x == 'W').sum()),
                L=('WinLose', lambda x: (x == 'L').sum()),
                T=('WinLose', lambda x: (x == 'T').sum()),
                Total_Games=('WinLose', 'count'),
                Pts_Marques=('Offense', 'sum'),
                Moy_Pts=('Offense', 'mean')
            ).reset_index()
            
            wl_season['WL_Pct'] = (wl_season['W'] + 0.5 * wl_season['T']) / wl_season['Total_Games'] * 100
            wl_season['WL_Text'] = wl_season.apply(
                lambda r: f"{r['W']}W - {r['L']}L" + (f" - {r['T']}T" if r['T'] > 0 else "") + f" ({r['WL_Pct']:.1f}% W/L)", axis=1
            )
            
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                fig_wl = px.line(
                    wl_season,
                    x='Year_Clean',
                    y='WL_Pct',
                    markers=True,
                    title="Courbe du Ratio % W/L par Saison",
                    labels={'Year_Clean': 'Saison', 'WL_Pct': '% Victoires (W/L)'},
                    text='WL_Text'
                )
                fig_wl.update_traces(textposition="top center")
                fig_wl.update_layout(height=400, yaxis=dict(range=[0, 100]), margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_wl, use_container_width=True)
                
            with col_graph2:
                fig_pts = px.line(
                    wl_season,
                    x='Year_Clean',
                    y='Moy_Pts',
                    markers=True,
                    title="Moyenne de Points Marqués / Match par Saison",
                    labels={'Year_Clean': 'Saison', 'Moy_Pts': 'Pts / Match'},
                    text=wl_season['Moy_Pts'].map("{:.1f} pts".format)
                )
                fig_pts.update_traces(textposition="top center")
                fig_pts.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_pts, use_container_width=True)

        # 4. TROPHÉES & BILAN SAISON
        with p_subtab4:
            st.subheader("🏆 Armoire à Trophées & Récompenses")
            m_awards = df_awards[df_awards['Player'].astype(str) == selected_prof].copy()
            
            if not m_awards.empty:
                df_disp_m_awards = m_awards.copy()
                
                for col, emoji in award_emojis.items():
                    if col in df_disp_m_awards.columns:
                        df_disp_m_awards[col] = df_disp_m_awards[col].apply(
                            lambda x: emoji if str(x).strip() in ['1', '1.0', '1.00'] else "-"
                        )

                if 'Playoffs Rank' in df_disp_m_awards.columns:
                    df_disp_m_awards['Playoffs Rank'] = df_disp_m_awards['Playoffs Rank'].apply(format_rank_playoffs)
                if 'Reg Season Rank' in df_disp_m_awards.columns:
                    df_disp_m_awards['Reg Season Rank'] = df_disp_m_awards['Reg Season Rank'].apply(format_rank_reg)

                rename_awards_prof = {
                    'Year_Clean': 'Saison',
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
                
                cols_awards_prof = [c for c in ['Year_Clean', 'Playoffs Rank', 'Reg Season Rank', 'OPOY', 'DPOY', 'COY', 'WorM', 'TOY', 'Playoffs', 'PxC'] if c in df_disp_m_awards.columns]
                df_disp_m_awards = df_disp_m_awards[cols_awards_prof].rename(columns=rename_awards_prof)
                
                st.dataframe(df_disp_m_awards, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun trophée ou classement répertorié dans l'onglet Awards pour ce manager.")
                
            st.markdown("---")
            
            st.subheader("📈 Bilan Saison par Saison")
            saison_summary = m_scores.groupby('Year_Clean').agg(
                Matchs=('WinLose', 'count'),
                Victoires=('WinLose', lambda x: (x == 'W').sum()),
                Défaites=('WinLose', lambda x: (x == 'L').sum()),
                Nuls=('WinLose', lambda x: (x == 'T').sum()),
                Total_Points=('Offense', 'sum'),
                Moyenne_Points=('Offense', 'mean')
            ).reset_index().rename(columns={
                'Year_Clean': 'Saison',
                'Total_Points': 'Total Pts Marqués',
                'Moyenne_Points': 'Moyenne Pts/Match'
            })
            
            saison_summary['% W/L'] = ((saison_summary['Victoires'] + 0.5 * saison_summary['Nuls']) / saison_summary['Matchs'] * 100).map("{:.1f}%".format)
            saison_summary = saison_summary.sort_values(by='Saison', ascending=False)
            
            st.dataframe(
                saison_summary[['Saison', 'Matchs', 'Victoires', 'Défaites', 'Nuls', '% W/L', 'Total Pts Marqués', 'Moyenne Pts/Match']],
                use_container_width=True,
                column_config={
                    "Total Pts Marqués": st.column_config.NumberColumn(format="%.2f"),
                    "Moyenne Pts/Match": st.column_config.NumberColumn(format="%.2f"),
                },
                hide_index=True
            )


# --- ONGLET 4 : LIVRE DES RECORDS ---
with tab4:
    st.header("🏅 Le Livre des Records (Hall of Fame & Shame)")
    
    valid_scores_rec = df_scores[(df_scores['Offense'] > 0) & (df_scores['Defense'] > 0)].copy()
    valid_scores_rec['Combine_Calc'] = valid_scores_rec['Offense'] + valid_scores_rec['Defense']
    valid_scores_rec['Delta_Calc'] = (valid_scores_rec['Offense'] - valid_scores_rec['Defense']).abs()
    
    def make_match_id(r):
        teams = sorted([str(r['Manager']).strip(), str(r['Opponent']).strip()])
        return f"{r['Year_Clean']}_{r['Wk_Clean']}_{teams[0]}_vs_{teams[1]}"
        
    valid_scores_rec['Match_ID'] = valid_scores_rec.apply(make_match_id, axis=1)
    
    winners_df = valid_scores_rec[valid_scores_rec['Offense'] >= valid_scores_rec['Defense']].copy()
    winners_df = winners_df.drop_duplicates(subset=['Match_ID'])
    
    rec_tab1, rec_tab2, rec_tab3, rec_tab4 = st.tabs([
        "🔥 Scores Extrêmes", 
        "🚀 Blowouts & Suspense", 
        "💥 Combines (Total Match)", 
        "⭐ Tops Joueurs NFL"
    ])
    
    # 1. SCORES EXTRÊMES
    with rec_tab1:
        col_hof, col_hos = st.columns(2)
        
        with col_hof:
            st.subheader("🔥 Hall of Fame (Top 10 Scores)")
            top_scores = valid_scores_rec.sort_values(by='Offense', ascending=False).head(10).copy()
            top_scores['Result'] = top_scores['WinLose'].map({'W': '🟢 WIN', 'L': '🔴 LOSS', 'T': '⚪ TIE'})
            
            show_cols_hof = ['Offense', 'Manager', 'Opponent', 'Year_Clean', 'Wk_Clean', 'Result']
            top_scores_disp = top_scores[[c for c in show_cols_hof if c in top_scores.columns]].rename(columns={
                'Offense': 'Score', 'Manager': 'Manager', 'Opponent': 'Adversaire', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine', 'Result': 'Résultat'
            })
            st.dataframe(top_scores_disp, use_container_width=True, hide_index=True, column_config={"Score": st.column_config.NumberColumn(format="%.2f")})
            
        with col_hos:
            st.subheader("🧊 Hall of Shame (Flop 10 Scores)")
            flop_scores = valid_scores_rec.sort_values(by='Offense', ascending=True).head(10).copy()
            flop_scores['Result'] = flop_scores['WinLose'].map({'W': '🟢 WIN', 'L': '🔴 LOSS', 'T': '⚪ TIE'})
            
            show_cols_hos = ['Offense', 'Manager', 'Opponent', 'Year_Clean', 'Wk_Clean', 'Result']
            flop_scores_disp = flop_scores[[c for c in show_cols_hos if c in flop_scores.columns]].rename(columns={
                'Offense': 'Score', 'Manager': 'Manager', 'Opponent': 'Adversaire', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine', 'Result': 'Résultat'
            })
            st.dataframe(flop_scores_disp, use_container_width=True, hide_index=True, column_config={"Score": st.column_config.NumberColumn(format="%.2f")})

    # 2. BLOWOUTS & SUSPENSE
    with rec_tab2:
        col_blow, col_tight = st.columns(2)
        
        with col_blow:
            st.subheader("🚀 Top 10 Blowouts (Plus Gros Écarts)")
            top_blowouts = winners_df.sort_values(by='Delta_Calc', ascending=False).head(10).copy()
            
            show_cols_blow = ['Delta_Calc', 'Manager', 'Offense', 'Opponent', 'Defense', 'Year_Clean', 'Wk_Clean']
            top_blow_disp = top_blowouts[[c for c in show_cols_blow if c in top_blowouts.columns]].rename(columns={
                'Delta_Calc': 'Écart', 'Manager': 'Vainqueur', 'Offense': 'Pts Vainqueur', 'Opponent': 'Adversaire', 'Defense': 'Pts Adversaire', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine'
            })
            st.dataframe(top_blow_disp, use_container_width=True, hide_index=True, column_config={
                "Écart": st.column_config.NumberColumn(format="%.2f"),
                "Pts Vainqueur": st.column_config.NumberColumn(format="%.2f"),
                "Pts Adversaire": st.column_config.NumberColumn(format="%.2f")
            })

        with col_tight:
            st.subheader("🔍 Top 10 Suspense (Matchs Serrés & Ties)")
            top_tight = winners_df.sort_values(by='Delta_Calc', ascending=True).head(10).copy()
            
            show_cols_tight = ['Delta_Calc', 'Manager', 'Offense', 'Opponent', 'Defense', 'Year_Clean', 'Wk_Clean']
            top_tight_disp = top_tight[[c for c in show_cols_tight if c in top_tight.columns]].rename(columns={
                'Delta_Calc': 'Écart', 'Manager': 'Manager / Vainqueur', 'Offense': 'Pts M1', 'Opponent': 'Adversaire', 'Defense': 'Pts M2', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine'
            })
            st.dataframe(top_tight_disp, use_container_width=True, hide_index=True, column_config={
                "Écart": st.column_config.NumberColumn(format="%.2f"),
                "Pts M1": st.column_config.NumberColumn(format="%.2f"),
                "Pts M2": st.column_config.NumberColumn(format="%.2f")
            })

    # 3. COMBINES
    with rec_tab3:
        col_comb_max, col_comb_min = st.columns(2)
        
        with col_comb_max:
            st.subheader("🔥 Top 10 Plus Gros Combines (Matchs Mitraillettes)")
            top_combines_max = winners_df.sort_values(by='Combine_Calc', ascending=False).head(10).copy()
            
            show_cols_cmax = ['Combine_Calc', 'Manager', 'Offense', 'Opponent', 'Defense', 'Year_Clean', 'Wk_Clean']
            top_cmax_disp = top_combines_max[[c for c in show_cols_cmax if c in top_combines_max.columns]].rename(columns={
                'Combine_Calc': 'Total Match', 'Manager': 'Équipe 1', 'Offense': 'Pts E1', 'Opponent': 'Équipe 2', 'Defense': 'Pts E2', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine'
            })
            st.dataframe(top_cmax_disp, use_container_width=True, hide_index=True, column_config={
                "Total Match": st.column_config.NumberColumn(format="%.2f"),
                "Pts E1": st.column_config.NumberColumn(format="%.2f"),
                "Pts E2": st.column_config.NumberColumn(format="%.2f")
            })
            
        with col_comb_min:
            st.subheader("🧊 Top 10 Plus Faibles Combines (Purges Offensives)")
            top_combines_min = winners_df.sort_values(by='Combine_Calc', ascending=True).head(10).copy()
            
            show_cols_cmin = ['Combine_Calc', 'Manager', 'Offense', 'Opponent', 'Defense', 'Year_Clean', 'Wk_Clean']
            top_cmin_disp = top_combines_min[[c for c in show_cols_cmin if c in top_combines_min.columns]].rename(columns={
                'Combine_Calc': 'Total Match', 'Manager': 'Équipe 1', 'Offense': 'Pts E1', 'Opponent': 'Équipe 2', 'Defense': 'Pts E2', 'Year_Clean': 'Saison', 'Wk_Clean': 'Semaine'
            })
            st.dataframe(top_cmin_disp, use_container_width=True, hide_index=True, column_config={
                "Total Match": st.column_config.NumberColumn(format="%.2f"),
                "Pts E1": st.column_config.NumberColumn(format="%.2f"),
                "Pts E2": st.column_config.NumberColumn(format="%.2f")
            })

    # 4. TOPS JOUEURS NFL
    with rec_tab4:
        st.subheader("⭐ Top 20 Performances Individuelles de Joueurs (Titulaires All-Time)")
        if not df_gc_starters.empty and 'Fantasy Points' in df_gc_starters.columns:
            top_players = df_gc_starters.sort_values(by='Fantasy Points', ascending=False).head(20).copy()
            
            show_cols_p = ['Player', 'POS', 'Fantasy Points', 'Manager', 'Year_Clean', 'Week_Clean', 'Stats']
            top_players_disp = top_players[[c for c in show_cols_p if c in top_players.columns]].rename(columns={
                'Player': 'Joueur', 'POS': 'POS', 'Fantasy Points': 'Pts Fantasy', 'Manager': 'Manager Fantasy', 'Year_Clean': 'Saison', 'Week_Clean': 'Semaine', 'Stats': 'Ligne de Stat'
            })
            st.dataframe(top_players_disp, use_container_width=True, hide_index=True, column_config={
                "Pts Fantasy": st.column_config.NumberColumn(format="%.2f pts")
            })
        else:
            st.info("Données GameCenter indisponibles.")

        st.markdown("---")

        st.subheader("🛋️ Top 20 Scores de Joueurs Laissés sur le Banc (All-Time)")
        if not df_gc_bench.empty and 'Fantasy Points' in df_gc_bench.columns:
            top_bench_players = df_gc_bench.sort_values(by='Fantasy Points', ascending=False).head(20).copy()
            
            show_cols_b = ['Player', 'POS', 'Fantasy Points', 'Manager', 'Year_Clean', 'Week_Clean', 'Stats']
            top_bench_disp = top_bench_players[[c for c in show_cols_b if c in top_bench_players.columns]].rename(columns={
                'Player': 'Joueur', 'POS': 'POS', 'Fantasy Points': 'Pts Fantasy Laissés sur le Banc', 'Manager': 'Manager Fantasy', 'Year_Clean': 'Saison', 'Week_Clean': 'Semaine', 'Stats': 'Ligne de Stat'
            })
            st.dataframe(top_bench_disp, use_container_width=True, hide_index=True, column_config={
                "Pts Fantasy Laissés sur le Banc": st.column_config.NumberColumn(format="%.2f pts")
            })
        else:
            st.info("Aucun score enregistré sur le banc dans GameCenter.")


# --- ONGLET 5 : GAMECENTER (JOUEURS) ---
with tab5:
    st.header("⭐ GameCenter - Performances des Joueurs (Titulaires Uniquement)")
    
    # Filtres interactifs avancés sur la base des titulaires
    gc_col1, gc_col2, gc_col3, gc_col4 = st.columns(4)
    
    with gc_col1:
        pos_list = ["Toutes"] + sorted([str(p) for p in df_gc_starters['POS'].dropna().unique() if str(p).strip() not in ["", "nan"]])
        selected_pos = st.selectbox("Position (POS) :", pos_list)
        
    with gc_col2:
        gc_managers = ["Tous"] + sorted([str(m) for m in df_gc_starters['Manager'].dropna().unique() if str(m).strip() not in ["", "nan"]])
        selected_gc_manager = st.selectbox("Manager Fantasy :", gc_managers, key="gc_manager_select")
        
    with gc_col3:
        gc_years_list = sorted([y for y in df_gc_starters['Year_Clean'].unique() if y != "0"], reverse=True)
        gc_years = ["Toutes"] + gc_years_list
        selected_gc_year = st.selectbox("Saison :", gc_years, key="gc_year_select")
        
    with gc_col4:
        player_search = st.text_input("Rechercher un joueur :", placeholder="ex: Patrick Mahomes")
        
    # Base filtrée pour les KPIs (recherche, manager, saison)
    df_kpi_base = df_gc_starters.dropna(subset=['Fantasy Points']).copy()
    
    if selected_gc_manager != "Tous":
        df_kpi_base = df_kpi_base[df_kpi_base['Manager'].astype(str) == selected_gc_manager]
    if selected_gc_year != "Toutes":
        df_kpi_base = df_kpi_base[df_kpi_base['Year_Clean'] == selected_gc_year]
    if player_search:
        df_kpi_base = df_kpi_base[df_kpi_base['Player'].astype(str).str.contains(player_search, case=False, na=False)]
        
    if not df_kpi_base.empty:
        # SECTION 1 : RECORDS SUR 1 MATCH
        st.subheader("⚡ Record sur 1 Match (Titulaire)")
        gc_c1, gc_c2, gc_c3, gc_c4, gc_c5, gc_c6 = st.columns(6)
        
        positions_kpi = [
            ("🎯 Top QB", "QB", gc_c1),
            ("🏃 Top RB", "RB", gc_c2),
            ("🙌 Top WR", "WR", gc_c3),
            ("⚡ Top TE", "TE", gc_c4),
            ("🦶 Top K", "K", gc_c5),
            ("🛡️ Top DEF", "DEF", gc_c6)
        ]
        
        for label, pos_code, col in positions_kpi:
            if pos_code == "DEF":
                pos_df = df_kpi_base[df_kpi_base['POS_Clean'] == 'DEF']
            else:
                pos_df = df_kpi_base[df_kpi_base['POS_Clean'] == pos_code]
                
            if not pos_df.empty:
                max_row = pos_df.loc[pos_df['Fantasy Points'].idxmax()]
                if selected_gc_manager == "Tous":
                    sub_text = f"{max_row['Player']} ({max_row['Manager']} - {max_row['Year_Clean']})"
                else:
                    sub_text = f"{max_row['Player']} ({max_row['Year_Clean']} Wk {max_row.get('Week_Clean', '')})"
                    
                col.metric(
                    label=label,
                    value=f"{max_row['Fantasy Points']:.2f} pts",
                    delta=sub_text,
                    delta_color="normal"
                )
            else:
                col.metric(label=label, value="-", delta="Aucune donnée", delta_color="off")

        # SECTION 2 : TOTAUX CUMULÉS DE POINTS
        st.subheader("📊 Totaux Cumulés de Points (Titulaire)")
        tot_c1, tot_c2, tot_c3, tot_c4, tot_c5, tot_c6 = st.columns(6)
        
        positions_tot_kpi = [
            ("🎯 Cumul QB", "QB", tot_c1),
            ("🏃 Cumul RB", "RB", tot_c2),
            ("🙌 Cumul WR", "WR", tot_c3),
            ("⚡ Cumul TE", "TE", tot_c4),
            ("🦶 Cumul K", "K", tot_c5),
            ("🛡️ Cumul DEF", "DEF", tot_c6)
        ]
        
        for label, pos_code, col in positions_tot_kpi:
            if pos_code == "DEF":
                pos_df = df_kpi_base[df_kpi_base['POS_Clean'] == 'DEF']
            else:
                pos_df = df_kpi_base[df_kpi_base['POS_Clean'] == pos_code]
                
            if not pos_df.empty:
                player_totals = pos_df.groupby('Player')['Fantasy Points'].sum()
                if not player_totals.empty:
                    top_player_name = player_totals.idxmax()
                    top_player_score = player_totals.max()
                    
                    col.metric(
                        label=label,
                        value=f"{top_player_score:.2f} pts",
                        delta=f"{top_player_name}",
                        delta_color="normal"
                    )
                else:
                    col.metric(label=label, value="-", delta="Aucune donnée", delta_color="off")
            else:
                col.metric(label=label, value="-", delta="Aucune donnée", delta_color="off")

    st.markdown("---")
    
    # Application de tous les filtres pour le tableau (y compris la position)
    df_filtered_gc = df_gc_starters.copy()
    if selected_pos != "Toutes":
        df_filtered_gc = df_filtered_gc[df_filtered_gc['POS'].astype(str) == selected_pos]
    if selected_gc_manager != "Tous":
        df_filtered_gc = df_filtered_gc[df_filtered_gc['Manager'].astype(str) == selected_gc_manager]
    if selected_gc_year != "Toutes":
        df_filtered_gc = df_filtered_gc[df_filtered_gc['Year_Clean'] == selected_gc_year]
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


# --- ONGLET 6 : AWARDS ---
with tab6:
    st.header("Palmarès & Récompenses")
    
    years_awards_list = sorted([y for y in df_awards['Year_Clean'].unique() if y != "0"], reverse=True)
    years_awards = ["Toutes"] + years_awards_list
    selected_award_year = st.selectbox("Filtrer par Année :", years_awards, key="awards_year")
    
    df_filtered_awards = df_awards.copy()
    if selected_award_year != "Toutes":
        df_filtered_awards = df_filtered_awards[df_filtered_awards['Year_Clean'] == selected_award_year]
        
    df_display_awards = df_filtered_awards.copy()
    
    for col, emoji in award_emojis.items():
        if col in df_display_awards.columns:
            df_display_awards[col] = df_display_awards[col].apply(
                lambda x: emoji if str(x).strip() in ['1', '1.0', '1.00'] else "-"
            )

    if 'Playoffs Rank' in df_display_awards.columns:
        df_display_awards['Playoffs Rank'] = df_display_awards['Playoffs Rank'].apply(format_rank_playoffs)
    if 'Reg Season Rank' in df_display_awards.columns:
        df_display_awards['Reg Season Rank'] = df_display_awards['Reg Season Rank'].apply(format_rank_reg)

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
