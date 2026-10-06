import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter
import time

# --- 1. CONFIGURATION DU SITE (MODE APP) ---
st.set_page_config(page_title="TwitchMod Manager", page_icon="⚡", layout="wide")

# CSS Ultra-Moderne (Style SaaS)
st.markdown("""
    <style>
    /* Cache les éléments de base de Streamlit pour faire plus "Site Web" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Design des cartes statistiques */
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #2d3142;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid #0984e3;
    }
    
    /* Titres et textes */
    h1, h2, h3 { color: #f5f6fa !important; font-family: 'Helvetica Neue', sans-serif; }
    hr { border-color: #2d3142; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MENU DE NAVIGATION WEB ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/733/733562.png", width=50) # Logo Twitch générique
    st.markdown("## TwitchMod Manager")
    st.markdown("---")
    
    # Le vrai menu de navigation
    page = st.radio("Navigation", [
        "📊 Tableau de Bord", 
        "👤 Fiches Modérateurs", 
        "⚡ Scanneur Twitch (Direct)",
        "⚙️ Base de données"
    ])
    st.markdown("---")
    st.caption("v2.0 - Propulsé par Python")

# --- 3. CHARGEMENT INVISIBLE DES DONNÉES ---
FICHIER_EXCEL = "suivi.xlsx"

@st.cache_data(ttl=60) # Garde en mémoire 60 secondes pour aller vite, mais se rafraîchit
def charger_donnees():
    if os.path.exists(FICHIER_EXCEL):
        try:
            # On force la lecture de la "Feuille 1" pour éviter que le code lise ton beau cockpit visuel
            xls = pd.ExcelFile(FICHIER_EXCEL)
            feuille = "Feuille 1" if "Feuille 1" in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(FICHIER_EXCEL, sheet_name=feuille)
            
            # Nettoyage invisible
            col_nom = next((col for col in df.columns if "Nom" in str(col)), df.columns[0])
            df = df.dropna(subset=[col_nom])
            
            # Recalculs propres
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

if df is None and page != "⚡ Scanneur Twitch (Direct)":
    st.error("Connexion à la base de données (suivi.xlsx) échouée.")
    st.stop()

# ==========================================
# PAGE 1 : TABLEAU DE BORD (DASHBOARD)
# ==========================================
if page == "📊 Tableau de Bord":
    st.title("Aperçu de l'Équipe")
    st.write("Analyse globale des performances de ta modération.")
    
    # 4 Cartes (Metrics) modernes
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Effectif Opérationnel", len(df), "Modérateurs")
    c2.metric("Équipe d'Élite", len(df[df['Grade'] == '👑 Top Modo']), "Top Modos")
    c3.metric("Activité Globale", int(df['Total Active beaucoup'].sum() + df['Total Active un peu'].sum()), "Sessions actives")
    c4.metric("Modérateurs à risque", len(df[df['Grade'] == '⚠️ Fantôme']), "Fantômes", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("Classement des Performances")
        df_tri = df.sort_values('Score Global', ascending=False).head(12)
        fig_bar = px.bar(df_tri, x=col_nom, y='Score Global', color='Grade', color_discrete_map=color_map, template="plotly_dark")
        fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.subheader("Santé de l'équipe")
        repartition = df['Grade'].value_counts().reset_index()
        fig_pie = px.pie(repartition, values='count', names='Grade', color='Grade', color_discrete_map=color_map, hole=0.6)
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# PAGE 2 : FICHES MODÉRATEURS
# ==========================================
elif page == "👤 Fiches Modérateurs":
    st.title("Dossiers Individuels")
    
    col_recherche, col_vide = st.columns([1, 2])
    with col_recherche:
        liste_modos = df[col_nom].tolist()
        modo = st.selectbox("Rechercher un membre :", liste_modos)
    
    st.markdown("---")
    
    if modo:
        data_modo = df[df[col_nom] == modo].iloc[0]
        
        c_profil, c_radar = st.columns([1, 1.5])
        
        with c_profil:
            st.markdown(f"## 👤 {modo}")
            st.markdown(f"**Statut actuel :** <span style='color:{color_map.get(data_modo['Grade'], '#fff')}'>{data_modo['Grade']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Score de fiabilité :** {data_modo['Score Global']} pts")
            
            st.markdown("<br><b>Historique des présences :</b>", unsafe_allow_html=True)
            st.progress(min(int((data_modo['Total Active beaucoup'] * 5) + (data_modo['Total Active un peu'] * 2)), 100))
            
            st.info(f"💡 Ce modérateur comptabilise **{data_modo['Total Active beaucoup']}** sessions à forte activité et **{data_modo['Total Pas là']}** absences.")
            
        with c_radar:
            # Création d'un vrai Radar Chart pro
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[data_modo['Total Active beaucoup'], data_modo['Total Active un peu'], data_modo['Total Pas là'], data_modo['Total Active beaucoup']],
                theta=["Forte Implication", "Présence Légère", "Absences", "Forte Implication"],
                fill='toself', name=modo, line_color="#0984e3"
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=False)),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# ==========================================
# PAGE 3 : LE SCANNEUR TWITCH
# ==========================================
elif page == "⚡ Scanneur Twitch (Direct)":
    st.title("Scanneur d'Activité")
    st.write("Importe ton journal de modération brut, l'algorithme s'occupe du reste.")
    
    fichier_txt = st.file_uploader("Drop ton fichier .txt ici", type=["txt"])
    
    if fichier_txt:
        with st.spinner('Analyse des logs en cours...'):
            time.sleep(1) # Petite animation fluide
            content = fichier_txt.read().decode("utf-8")
            mod_counts = Counter()
            keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé']
            
            for line in content.split('\n'):
                if any(k in line for k in keywords):
                    match = re.search(r' par ([\w_]+)', line)
                    if match and match.group(1).lower() not in ['wizebot', 'erreur']:
                        mod_counts[match.group(1)] += 1
            
            if mod_counts:
                st.toast('Analyse terminée avec succès !', icon='✅')
                
                data_jour = []
                for m, c in mod_counts.most_common():
                    data_jour.append({"Modérateur": m, "Actions": c, "Badge": "🥇" if c >= 15 else "🥈" if c >= 5 else "🥉"})
                
                df_jour = pd.DataFrame(data_jour)
                
                st.subheader("Les plus actifs du jour")
                fig_jour = px.bar(df_jour.head(10), x='Actions', y='Modérateur', orientation='h', text='Actions', template="plotly_dark", color='Actions', color_continuous_scale="Blues")
                fig_jour.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_jour, use_container_width=True)

# ==========================================
# PAGE 4 : BASE DE DONNÉES (Cachée pour les pros)
# ==========================================
elif page == "⚙️ Base de données":
    st.title("Gestion des Données")
    st.write("C'est ici que tu peux voir ou éditer la matrice d'origine si besoin.")
    
    with st.expander("Ouvrir l'éditeur de tableau (Mode Excel)", expanded=True):
        st.write("Tu peux modifier les cases directement ici :")
        cols = [col_nom, 'Total Active beaucoup', 'Total Active un peu', 'Total Pas là', 'Score Global', 'Grade']
        st.data_editor(df[cols], use_container_width=True, hide_index=True)
