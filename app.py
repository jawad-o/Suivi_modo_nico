import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="QG Modération Ultime", page_icon="👑", layout="wide")

PASSWORD = "modo"
mot_de_passe = st.sidebar.text_input("🔐 Mot de passe :", type="password")

if mot_de_passe != PASSWORD:
    st.sidebar.warning("Veuillez entrer le mot de passe pour accéder au QG.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Analyse Quotidienne")
fichier_txt = st.sidebar.file_uploader("Glisse le .txt du jour ici", type=["txt"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📁 Secours (Optionnel)")
fichier_excel_secours = st.sidebar.file_uploader("Si le fichier automatique ne charge pas, glisse ton Excel ici", type=["xlsx", "ods"])

# --- CHARGEMENT DE L'EXCEL (SANS CACHE POUR ÉVITER LES BUGS) ---
FICHIER_EXCEL = "suivi.xlsx"

def charger_donnees():
    # 1. On donne la priorité au fichier glissé manuellement si besoin
    if fichier_excel_secours is not None:
        return pd.read_excel(fichier_excel_secours)
    # 2. Sinon on cherche le fichier automatique sur GitHub
    elif os.path.exists(FICHIER_EXCEL):
        return pd.read_excel(FICHIER_EXCEL)
    # 3. Si aucun des deux, on renvoie une erreur
    return None

df = charger_donnees()

# --- INTERFACE PRINCIPALE ---
st.title("👑 QG Modération - Direction")

if df is None:
    st.error("⚠️ Fichier 'suivi.xlsx' introuvable sur le GitHub. Tu peux utiliser la zone d'import 'Secours' dans le menu de gauche en attendant !")
    st.stop()

# Nettoyage et préparation des données
col_nom = next((col for col in df.columns if "Nom" in str(col)), df.columns[0])
col_score = next((col for col in df.columns if "Score" in str(col)), None)
col_bcp = next((c for c in df.columns if "beaucoup" in str(c).lower()), None)
col_peu = next((c for c in df.columns if "peu" in str(c).lower()), None)
col_pas = next((c for c in df.columns if "pas l" in str(c).lower()), None)

# Création des onglets
tab1, tab2, tab3, tab4 = st.tabs(["🏆 Mur des Légendes", "📈 Statistiques & Graphiques", "🔎 Profil 360°", "⚡ Scan du Jour (.txt)"])

# ----------------------------------------
# ONGLET 1 : MUR DES LÉGENDES (Leaderboard)
# ----------------------------------------
with tab1:
    st.subheader("Bilan de l'Équipe")
    
    if col_score:
        df_top = df.sort_values(by=col_score, ascending=False).dropna(subset=[col_score])
        
        # KPIs en haut
        col1, col2, col3, col4 = st.columns(4)
        top_1 = df_top.iloc[0][col_nom] if len(df_top) > 0 else "N/A"
        top_2 = df_top.iloc[1][col_nom] if len(df_top) > 1 else "N/A"
        effectif = len(df_top)
        total_actions = df[col_bcp].sum() * 15 + df[col_peu].sum() * 5 if col_bcp else 0 # Estimation
        
        col1.metric("🥇 1er Modérateur", f"{top_1}")
        col2.metric("🥈 2ème Modérateur", f"{top_2}")
        col3.metric("👥 Effectif Actif", f"{effectif} Modos")
        col4.metric("🔥 Estimation Actions", f"~{int(total_actions)}")
        
        st.markdown("---")
        
        # Heatmap (Tableau stylisé)
        st.subheader("🗺️️ Carte de chaleur des présences")
        st.write("Plus la case est foncée, plus le score est élevé.")
        
        df_display = df_top[[col_nom, col_score, col_bcp, col_peu, col_pas]].copy()
        st.dataframe(df_display.style.background_gradient(subset=[col_score], cmap="Greens"), use_container_width=True)
    else:
        st.warning("Ajoute une colonne 'Score Global' dans ton Excel pour voir le classement.")

# ----------------------------------------
# ONGLET 2 : STATISTIQUES AVANCÉES
# ----------------------------------------
with tab2:
    st.subheader("Analyse Visuelle de la Modération")
    if col_score and col_bcp:
        c1, c2 = st.columns(2)
        
        with c1:
            fig_tree = px.treemap(df_top.head(15), path=[px.Constant("Équipe"), col_nom], values=col_score,
                                  color=col_score, color_continuous_scale='Purp',
                                  title="Poids de chaque modérateur dans l'équipe (Top 15)")
            fig_tree.update_layout(template="plotly_dark", margin=dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with c2:
            tot_presences = df_top[col_bcp].sum() + df_top[col_peu].sum()
            tot_absences = df_top[col_pas].sum()
            tx_presence = (tot_presences / (tot_presences + tot_absences)) * 100 if (tot_presences + tot_absences) > 0 else 0
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = tx_presence,
                number = {'suffix': "%"},
                title = {'text': "Taux de Présence Global"},
                gauge = {'axis': {'range': [0, 100]},
                         'bar': {'color': "#00b894"},
                         'steps': [
                             {'range': [0, 50], 'color': "#d63031"},
                             {'range': [50, 80], 'color': "#fdcb6e"}],
                         }
            ))
            fig_gauge.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_gauge, use_container_width=True)

# ----------------------------------------
# ONGLET 3 : PROFIL 360° DU MODÉRATEUR
# ----------------------------------------
with tab3:
    st.subheader("Dossier Individuel")
    liste_modos = df[col_nom].dropna().unique().tolist()
    modo_choisi = st.selectbox("Rechercher un modérateur :", ["-- Sélectionner --"] + sorted(liste_modos))
    
    if modo_choisi != "-- Sélectionner --":
        stats_modo = df[df[col_nom] == modo_choisi].iloc[0]
        
        col_prof1, col_prof2 = st.columns([1, 2])
        with col_prof1:
            st.markdown(f"## 👤 {modo_choisi}")
            score_actuel = stats_modo[col_score] if col_score else "N/A"
            st.metric("Score Global", score_actuel)
            
            if col_bcp and col_peu and col_pas:
                st.write(f"**🟢 Fortes activités :** {stats_modo[col_bcp]}")
                st.write(f"**🟡 Faibles activités :** {stats_modo[col_peu]}")
                st.write(f"**🔴 Absences :** {stats_modo[col_pas]}")
                
        with col_prof2:
            if col_bcp and col_peu and col_pas:
                fig_radar = go.Figure(data=go.Scatterpolar(
                  r=[stats_modo[col_bcp], stats_modo[col_peu], stats_modo[col_pas], stats_modo[col_bcp]],
                  theta=['Implication Forte', 'Présence Légère', 'Absences', 'Fiabilité'],
                  fill='toself',
                  line_color='#a29bfe'
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False, template="plotly_dark", title="Radar d'Activité")
                st.plotly_chart(fig_radar, use_container_width=True)

# ----------------------------------------
# ONGLET 4 : LE SCANNEUR QUOTIDIEN (.txt)
# ----------------------------------------
with tab4:
    st.subheader("Analyse du tchat en direct")
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
                if count >= 10:
                    statut = "🟢 Active beaucoup"
                elif count > 0:
                    statut = "🟡 Active un peu"
                else:
                    statut = "🔴 Pas là"
                data_jour.append({"Modérateur": mod, "Actions": count, "Statut": statut})
                
            df_jour = pd.DataFrame(data_jour)
            
            st.success("✅ Fichier journalier analysé avec succès !")
            st.dataframe(df_jour, use_container_width=True)
            
            csv_jour = df_jour.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger ces stats pour mettre à jour l'Excel", data=csv_jour, file_name='nouveau_jour.csv', mime='text/csv')
    else:
        st.info("👈 Glisse le fichier .txt du jour dans la barre latérale à gauche pour le faire analyser par l'IA.")
