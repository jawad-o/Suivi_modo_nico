import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter
import time

# --- 1. CONFIGURATION ET INJECTION DE DESIGN (CSS) ---
st.set_page_config(page_title="TwitchMod Manager", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Import d'une police moderne */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    
    /* Nettoyage de l'interface de base */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Design "Glassmorphism" pour les cartes (Effet de transparence pro) */
    .glass-card {
        background: linear-gradient(135deg, rgba(45, 52, 54, 0.8), rgba(30, 39, 46, 0.9));
        border-radius: 15px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    
    .glass-card h3 { margin-top: 0; color: #a29bfe; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;}
    .glass-card h1 { margin-top: 5px; color: #f5f6fa; font-size: 2.5rem; font-weight: 800;}
    
    /* Badges pour les profils */
    .badge {
        display: inline-block;
        padding: 6px 15px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        margin-right: 10px;
        margin-bottom: 10px;
        background: #0984e3;
        color: white;
    }
    .badge-elite { background: linear-gradient(135deg, #e1b12c, #fbc531); color: #2f3640;}
    .badge-fire { background: linear-gradient(135deg, #e84118, #c23616); }
    .badge-shield { background: linear-gradient(135deg, #00a8ff, #0097e6); }
    
    /* Avatars ronds */
    .avatar {
        border-radius: 50%;
        width: 120px;
        height: 120px;
        border: 3px solid #6c5ce7;
        box-shadow: 0 0 15px rgba(108, 92, 231, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SÉCURITÉ ET MENU ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/733/733562.png", width=60)
    st.markdown("## TwitchMod Pro")
    mot_de_passe = st.text_input("🔑 Authentification :", type="password")
    
    if mot_de_passe != "modo":
        st.warning("Accès restreint.")
        st.stop()
        
    st.markdown("---")
    page = st.radio("NAVIGATION", [
        "📊 Dashboard Exécutif", 
        "👤 CRM Modérateurs", 
        "⚡ Radar Temps Réel",
        "⚙️ Paramètres & Base"
    ])

# --- 3. CHARGEMENT ET TRAITEMENT DES DONNÉES ---
FICHIER_EXCEL = "suivi.xlsx"

@st.cache_data(ttl=60)
def charger_donnees():
    if os.path.exists(FICHIER_EXCEL):
        try:
            xls = pd.ExcelFile(FICHIER_EXCEL)
            feuille = "Feuille 1" if "Feuille 1" in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(FICHIER_EXCEL, sheet_name=feuille)
            col_nom = next((col for col in df.columns if "Nom" in str(col)), df.columns[0])
            df = df.dropna(subset=[col_nom])
            
            for col in ['Total Active beaucoup', 'Total Active un peu', 'Total Pas là']:
                if col not in df.columns: df[col] = 0
                
            df['Score Global'] = (df['Total Active beaucoup'] * 3) + (df['Total Active un peu'] * 1) + (df['Total Pas là'] * -1)
            
            def get_grade(score):
                if score >= 5: return "👑 Top Modo"
                elif score >= 3: return "⭐ Actif"
                elif score >= 1: return "🔎 En observation"
                else: return "⚠️ Fantôme"

            df['Grade'] = df['Score Global'].apply(get_grade)
            return df, col_nom
        except Exception:
            return None, None
    return None, None

df, col_nom = charger_donnees()
color_map = {"👑 Top Modo": "#00b894", "⭐ Actif": "#fdcb6e", "🔎 En observation": "#0984e3", "⚠️ Fantôme": "#d63031"}

if df is None and page != "⚡ Radar Temps Réel":
    st.error("Base de données introuvable.")
    st.stop()

# ==========================================
# PAGE 1 : DASHBOARD EXÉCUTIF (Design Web)
# ==========================================
if page == "📊 Dashboard Exécutif":
    st.markdown("<h1>Tableau de Bord Stratégique</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b2bec3; margin-bottom:30px;'>Analyse de l'équipe de modération en temps réel.</p>", unsafe_allow_html=True)
    
    # KPIs en HTML Custom (Plus de st.metric fade)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="glass-card">
                <h3>👥 Effectif Déployé</h3>
                <h1>{len(df)} <span style='font-size:1rem; color:#00b894;'>Actifs</span></h1>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        top_modos = len(df[df['Grade'] == '👑 Top Modo'])
        st.markdown(f"""
            <div class="glass-card">
                <h3>👑 Unité d'Élite</h3>
                <h1>{top_modos} <span style='font-size:1rem; color:#fdcb6e;'>Top Modos</span></h1>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        fantomes = len(df[df['Grade'] == '⚠️ Fantôme'])
        st.markdown(f"""
            <div class="glass-card">
                <h3>⚠️ Zones à Risque</h3>
                <h1>{fantomes} <span style='font-size:1rem; color:#d63031;'>Fantômes</span></h1>
            </div>
        """, unsafe_allow_html=True)

    # Graphiques Design
    st.markdown("<br>", unsafe_allow_html=True)
    colA, colB = st.columns([2.5, 1])
    
    with colA:
        df_tri = df.sort_values('Score Global', ascending=False).head(12)
        fig_bar = px.bar(df_tri, x=col_nom, y='Score Global', color='Grade', color_discrete_map=color_map, template="plotly_dark")
        fig_bar.update_layout(title="Classement des Performances", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with colB:
        repartition = df['Grade'].value_counts().reset_index()
        fig_pie = px.pie(repartition, values='count', names='Grade', color='Grade', color_discrete_map=color_map, hole=0.7)
        fig_pie.update_layout(title="Répartition", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        fig_pie.add_annotation(text="ÉQUIPE", x=0.5, y=0.5, font_size=20, showarrow=False)
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# PAGE 2 : CRM MODÉRATEURS (Fiches riches)
# ==========================================
elif page == "👤 CRM Modérateurs":
    st.markdown("<h1>Dossiers Modérateurs</h1>", unsafe_allow_html=True)
    
    # Barre de recherche type CRM
    recherche = st.selectbox("Rechercher un membre de l'équipe :", df[col_nom].tolist())
    st.markdown("---")
    
    if recherche:
        data = df[df[col_nom] == recherche].iloc[0]
        
        c_avatar, c_info, c_stats = st.columns([1, 2, 1.5])
        
        with c_avatar:
            # Avatar généré dynamiquement selon le pseudo
            avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={recherche}&backgroundColor=1e2130"
            st.markdown(f'<img src="{avatar_url}" class="avatar">', unsafe_allow_html=True)
            
        with c_info:
            st.markdown(f"<h1 style='margin-bottom:0;'>{recherche}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color:{color_map.get(data['Grade'], '#fff')}; margin-top:0;'>{data['Grade']}</h3>", unsafe_allow_html=True)
            
            # Système de Badges (Gamification)
            badges = []
            if data['Score Global'] >= 10: badges.append("<span class='badge badge-elite'>💎 Pilier de la Chaîne</span>")
            if data['Total Pas là'] == 0: badges.append("<span class='badge badge-shield'>🛡️ Bouclier (0 Absence)</span>")
            if data['Total Active beaucoup'] >= 5: badges.append("<span class='badge badge-fire'>🔥 Hyper-Actif</span>")
            if not badges: badges.append("<span class='badge'>🌱 En formation</span>")
            
            st.markdown(" ".join(badges), unsafe_allow_html=True)
            
            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-top:20px;">
                    <p style="color:#b2bec3; margin:0;">Score d'Évaluation RH :</p>
                    <h2 style="margin:0; color:#00b894;">{data['Score Global']} Points</h2>
                </div>
            """, unsafe_allow_html=True)
            
        with c_stats:
            # Radar Chart pour l'empreinte de modération
            fig_radar = go.Figure(go.Scatterpolar(
                r=[data['Total Active beaucoup'], data['Total Active un peu'], data['Total Pas là'], data['Total Active beaucoup']],
                theta=["Actions Lourdes", "Veille Légère", "Inactivité", "Actions Lourdes"],
                fill='toself', line_color="#6c5ce7"
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=False)),
                showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=250
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# ==========================================
# PAGE 3 : RADAR TEMPS RÉEL (Finis les tableaux moches)
# ==========================================
elif page == "⚡ Radar Temps Réel":
    st.markdown("<h1>Radar d'Activité Twitch</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b2bec3;'>Dépose le journal brut. L'IA extrait les interventions et génère le rapport.</p>", unsafe_allow_html=True)
    
    fichier_txt = st.file_uploader("Journal Twitch (.txt)", type=["txt"])
    
    if fichier_txt:
        with st.spinner('Décryptage des logs de modération...'):
            time.sleep(1)
            content = fichier_txt.read().decode("utf-8")
            mod_counts = Counter()
            keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé']
            
            for line in content.split('\n'):
                if any(k in line for k in keywords):
                    match = re.search(r' par ([\w_]+)', line)
                    if match and match.group(1).lower() not in ['wizebot', 'erreur']:
                        mod_counts[match.group(1)] += 1
            
            if mod_counts:
                # Affichage des Tops du jour sous forme de podium au lieu d'un tableau
                tops = mod_counts.most_common(3)
                
                c1, c2, c3 = st.columns(3)
                if len(tops) > 0:
                    c1.markdown(f"<div class='glass-card' style='text-align:center; border-top: 4px solid #fbc531;'><h1>🥇</h1><h3>{tops[0][0]}</h3><p>{tops[0][1]} actions</p></div>", unsafe_allow_html=True)
                if len(tops) > 1:
                    c2.markdown(f"<div class='glass-card' style='text-align:center; border-top: 4px solid #bdc3c7;'><h1>🥈</h1><h3>{tops[1][0]}</h3><p>{tops[1][1]} actions</p></div>", unsafe_allow_html=True)
                if len(tops) > 2:
                    c3.markdown(f"<div class='glass-card' style='text-align:center; border-top: 4px solid #cd6133;'><h1>🥉</h1><h3>{tops[2][0]}</h3><p>{tops[2][1]} actions</p></div>", unsafe_allow_html=True)
                
                # Le reste en graphique bulle
                st.markdown("### Cartographie du reste de l'équipe")
                df_jour = pd.DataFrame([{"Modérateur": m, "Interventions": c} for m, c in mod_counts.most_common()[3:]])
                if not df_jour.empty:
                    fig_jour = px.bar(df_jour, x='Interventions', y='Modérateur', orientation='h', template="plotly_dark", color='Interventions', color_continuous_scale="Purp")
                    fig_jour.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=300)
                    st.plotly_chart(fig_jour, use_container_width=True)

# ==========================================
# PAGE 4 : GESTIONNAIRE CRM (La Base Cachée)
# ==========================================
elif page == "⚙️ Paramètres & Base":
    st.markdown("<h1>Gestionnaire de Base de Données</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b2bec3;'>L'accès direct à la matrice. Utilise les filtres pour cibler les profils avant modification.</p>", unsafe_allow_html=True)
    
    # Filtres type CRM
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtre_grade = st.multiselect("Filtrer par Grade :", df['Grade'].unique(), default=df['Grade'].unique())
    with col_f2:
        recherche_nom = st.text_input("🔍 Chercher un nom précis :")
        
    # Application des filtres
    df_filtre = df[df['Grade'].isin(filtre_grade)]
    if recherche_nom:
        df_filtre = df_filtre[df_filtre[col_nom].str.contains(recherche_nom, case=False, na=False)]
    
    st.markdown("---")
    
    # Éditeur propre
    colonnes_a_editer = [col_nom, 'Total Active beaucoup', 'Total Active un peu', 'Total Pas là']
    df_edite = st.data_editor(df_filtre[colonnes_a_editer], num_rows="dynamic", use_container_width=True, hide_index=True)
    
    st.download_button(
        "📥 Exporter les modifications (CSV)",
        data=df_edite.to_csv(index=False).encode('utf-8'),
        file_name="base_export.csv",
        mime="text/csv"
    )
