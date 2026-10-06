import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter

# --- 1. CONFIGURATION DU SITE ---
st.set_page_config(page_title="Cockpit Modération", page_icon="🛡️", layout="wide")

# CSS personnalisé pour donner un look "Dashboard Excel"
st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-top: 3px solid #4a69bd; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #2d3436; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #0984e3 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SÉCURITÉ ET IMPORT ---
PASSWORD = "modo"
mot_de_passe = st.sidebar.text_input("🔐 Mot de passe :", type="password")

if mot_de_passe != PASSWORD:
    st.sidebar.warning("Veuillez entrer le mot de passe pour accéder au Cockpit.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("📁 Outils Quotidiens")
fichier_txt = st.sidebar.file_uploader("1. Scanneur du Jour (.txt)", type=["txt"])
fichier_excel_secours = st.sidebar.file_uploader("2. Import manuel Excel (Secours)", type=["xlsx", "ods"])

# --- 3. CHARGEMENT ET CALCUL DES DONNÉES ---
FICHIER_EXCEL = "suivi.xlsx"

def charger_donnees():
    if fichier_excel_secours is not None:
        return pd.read_excel(fichier_excel_secours)
    elif os.path.exists(FICHIER_EXCEL):
        return pd.read_excel(FICHIER_EXCEL)
    return None

df_brut = charger_donnees()

if df_brut is None:
    st.error("⚠️ Fichier 'suivi.xlsx' introuvable. Importe-le via GitHub ou utilise la zone de secours à gauche.")
    st.stop()

# Nettoyage et Recalcul automatique (pour être sûr que ça marche même s'il manque des formules dans l'Excel)
df = df_brut.copy()
col_nom = next((col for col in df.columns if "Nom" in str(col)), df.columns[0])

# On s'assure que les colonnes de base existent
for col in ['Total Active beaucoup', 'Total Active un peu', 'Total Pas là', 'Total Absence justifiée']:
    if col not in df.columns:
        df[col] = 0

df.fillna({col_nom: "Inconnu", 'Total Active beaucoup': 0, 'Total Active un peu': 0, 'Total Pas là': 0, 'Total Absence justifiée': 0}, inplace=True)

# Calculs mathématiques (comme dans ton Excel)
df['Sessions (+)'] = df['Total Active beaucoup'] + df['Total Active un peu']
df['Total Jours'] = df['Sessions (+)'] + df['Total Pas là'] + df['Total Absence justifiée']
df['Score Global'] = (df['Total Active beaucoup'] * 3) + (df['Total Active un peu'] * 1) + (df['Total Pas là'] * -1)
df['Assiduité %'] = df.apply(lambda x: (x['Sessions (+)'] / (x['Total Jours'] - x['Total Absence justifiée'])) * 100 if (x['Total Jours'] - x['Total Absence justifiée']) > 0 else 0, axis=1)

# Attribution des Grades Automatiques
def get_grade(score):
    if score >= 5: return "👑 Top Modo"
    elif score >= 3: return "⭐ Modo Actif"
    elif score >= 1: return "🔎 En observation"
    else: return "⚠️ Danger fantôme"

df['Grade'] = df['Score Global'].apply(get_grade)

# Couleurs pour les graphiques
color_map = {"👑 Top Modo": "#e17055", "⭐ Modo Actif": "#fdcb6e", "🔎 En observation": "#00b894", "⚠️ Danger fantôme": "#d63031"}

# --- 4. AFFICHAGE DU COCKPIT ---
st.markdown("<h1 style='text-align: center; color: #74b9ff;'>🛡️ COCKPIT DE PILOTAGE ET PERFORMANCE DES MODÉRATEURS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #b2bec3;'>Suivi d'activité en temps réel • Analyse individuelle et collective</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚀 Cockpit Interactif", "⚡ Analyseur .txt en direct", "💾 Base Excel Brut"])

with tab1:
    # --- KPIs GLOBAUX ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    effectif_tot = len(df)
    assiduite_moy = df['Assiduité %'].mean()
    modos_actifs = len(df[df['Grade'].isin(['👑 Top Modo', '⭐ Modo Actif'])])
    alertes = len(df[df['Grade'] == '⚠️ Danger fantôme'])
    score_moy = df['Score Global'].mean()
    actions_estimees = int((df['Total Active beaucoup'].sum() * 15) + (df['Total Active un peu'].sum() * 5))
    
    c1.metric("👥 EFFECTIF TOTAL", f"{effectif_tot}", "Membres")
    c2.metric("📉 ASSIDUITÉ MOYENNE", f"{assiduite_moy:.1f}%", "Sur la période")
    c3.metric("⭐ MODOS ACTIFS", f"{modos_actifs}", "Top & Actifs")
    c4.metric("⚠️ ALERTES FANTÔME", f"{alertes}", "- À surveiller", delta_color="inverse")
    c5.metric("🎯 SCORE MOYEN", f"{score_moy:.1f}", "Points / modo")
    c6.metric("⚡ ACTIONS ÉQUIPE", f"~{actions_estimees}", "Estimées")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- DEUX COLONNES PRINCIPALES ---
    col_gauche, col_droite = st.columns([1, 2.5])
    
    # === COLONNE GAUCHE : PROFIL INDIVIDUEL ===
    with col_gauche:
        st.markdown("### 👤 PROFIL INDIVIDUEL")
        liste_modos = df[col_nom].tolist()
        modo_select = st.selectbox("Sélection :", liste_modos)
        
        modo_data = df[df[col_nom] == modo_select].iloc[0]
        
        st.write(f"**Grade actuel :** {modo_data['Grade']}")
        st.write(f"**Score Global :** {modo_data['Score Global']} pts")
        
        st.markdown("**Jauge d'assiduité :**")
        st.progress(min(int(modo_data['Assiduité %']), 100))
        st.write(f"<div style='text-align: right;'><b>{modo_data['Assiduité %']:.1f}%</b></div>", unsafe_allow_html=True)
        
        # Répartition
        st.markdown("📊 **Répartition des sessions**")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("🟢 Bcp", modo_data['Total Active beaucoup'])
        sc2.metric("🟡 Peu", modo_data['Total Active un peu'])
        sc3.metric("🔴 Abs", modo_data['Total Pas là'])
        
        st.markdown("---")
        st.markdown("🎯 **OBJECTIFS & CIBLE HEBDO**")
        cible = 200
        # Simulation d'actions selon les présences
        actions_simulees = int((modo_data['Total Active beaucoup'] * 25) + (modo_data['Total Active un peu'] * 8))
        taux_atteinte = min((actions_simulees / cible) * 100, 100)
        
        st.write(f"Cible : **{cible} actions** | Estimées : **{actions_simulees}**")
        st.progress(int(taux_atteinte))
        
        if taux_atteinte >= 80:
            st.success(f"Taux d'atteinte : {taux_atteinte:.1f}% - Objectif validé ✅")
        elif taux_atteinte >= 40:
            st.warning(f"Taux d'atteinte : {taux_atteinte:.1f}% - Rythme modéré ⚠️")
        else:
            st.error(f"Taux d'atteinte : {taux_atteinte:.1f}% - Sous-performance 🚨")

    # === COLONNE DROITE : VUE DYNAMIQUE & GRAPHIQUE ===
    with col_droite:
        st.markdown("### ⚡ VUE DYNAMIQUE DE L'ÉQUIPE")
        
        # Filtre
        filtre_grade = st.selectbox("Filtre par Grade :", ["TOUS", "👑 Top Modo", "⭐ Modo Actif", "🔎 En observation", "⚠️ Danger fantôme"])
        
        df_filtre = df.copy()
        if filtre_grade != "TOUS":
            df_filtre = df_filtre[df_filtre['Grade'] == filtre_grade]
            
        # Formatage du tableau pour l'affichage
        df_affichage = df_filtre[[col_nom, 'Grade', 'Score Global', 'Assiduité %', 'Sessions (+)']].copy()
        df_affichage['Assiduité %'] = df_affichage['Assiduité %'].apply(lambda x: f"{x:.1f}%")
        df_affichage = df_affichage.sort_values(by='Score Global', ascending=False)
        
        # Disposition Tableau / Donut
        ctab, cchart = st.columns([1.5, 1])
        
        with ctab:
            st.dataframe(df_affichage, use_container_width=True, height=400)
            
        with cchart:
            # Répartition par grade (Donut Chart)
            repartition = df['Grade'].value_counts().reset_index()
            repartition.columns = ['Grade', 'Effectif']
            
            fig_pie = px.pie(repartition, values='Effectif', names='Grade', 
                             color='Grade', color_discrete_map=color_map,
                             hole=0.5, title="Répartition par Grade")
            fig_pie.update_traces(textposition='inside', textinfo='percent+value')
            fig_pie.update_layout(template="plotly_dark", showlegend=True, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_pie, use_container_width=True)

        # Synthèse RH en bas
        st.markdown("### 📋 SYNTHÈSE OPÉRATIONNELLE & RH")
        top_membres = ", ".join(df[df['Grade'] == '👑 Top Modo'][col_nom].tolist()[:5])
        st.success(f"**👑 Pôle Top Modos ({len(df[df['Grade'] == '👑 Top Modo'])} membres) :** {top_membres}...")
        st.info("Action RH : Valorisation et maintien prioritaire des droits de modération.")
        
        danger_membres = ", ".join(df[df['Grade'] == '⚠️ Danger fantôme'][col_nom].tolist()[:5])
        st.error(f"**⚠️ Pôle Fantôme ({len(df[df['Grade'] == '⚠️ Danger fantôme'])} membres) :** {danger_membres}...")
        st.info("Action RH : Avertissement, vérification des absences, rétrogradation possible.")

# --- ONGLET 2 : LE SCANNEUR TXT ---
with tab2:
    st.markdown("### ⚡ Analyse des logs bruts Twitch")
    if fichier_txt is not None:
        content = fichier_txt.read().decode("utf-8")
        lines = content.split('\n')
        
        mod_counts = Counter()
        keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé', 'Demande', 'Exclusion', 'Vous avez été']
        for line in lines:
            if any(k in line for k in keywords):
                match = re.search(r' par ([\w_]+)', line)
                if match:
                    mod = match.group(1)
                    if mod.lower() not in ['wizebot', 'erreur']:
                        mod_counts[mod] += 1
                        
        if mod_counts:
            data_jour = []
            for mod, count in mod_counts.most_common():
                if count >= 10: statut = "🟢 Active beaucoup"
                elif count > 0: statut = "🟡 Active un peu"
                else: statut = "🔴 Pas là"
                data_jour.append({"Modérateur": mod, "Actions": count, "Statut": statut})
                
            df_jour = pd.DataFrame(data_jour)
            st.success("✅ Fichier journalier analysé avec succès !")
            
            c_bar, c_tab = st.columns(2)
            with c_bar:
                fig_jour = px.bar(df_jour.head(15), x='Modérateur', y='Actions', text='Actions', color='Actions', color_continuous_scale='Blues', template="plotly_dark")
                st.plotly_chart(fig_jour, use_container_width=True)
            with c_tab:
                st.dataframe(df_jour, use_container_width=True)
                csv_jour = df_jour.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger ces stats pour mettre à jour l'Excel", data=csv_jour, file_name='nouveau_jour.csv', mime='text/csv')
    else:
        st.info("👈 Glisse le fichier .txt du jour dans la barre latérale à gauche.")

# --- ONGLET 3 : DATA BRUTE ---
with tab3:
    st.markdown("### 💾 Fichier Source")
    st.dataframe(df_brut, use_container_width=True)
