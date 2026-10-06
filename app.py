import streamlit as st
import pandas as pd
import re
from collections import Counter
import plotly.express as px

# 1. Configuration de la page (Mode Large pour un vrai Dashboard)
st.set_page_config(page_title="QG Modération", page_icon="🛡️", layout="wide")

# 2. Sécurité
PASSWORD = "modo"
mot_de_passe = st.sidebar.text_input("🔐 Mot de passe :", type="password")

if mot_de_passe != PASSWORD:
    st.sidebar.warning("Veuillez entrer le mot de passe pour accéder à l'outil.")
    st.stop()

# 3. Barre latérale (Sidebar) pour les imports
st.sidebar.markdown("---")
st.sidebar.header("📁 Import des Données")
fichier_excel = st.sidebar.file_uploader("1. Ton Historique (.xlsx)", type=["xlsx"])
fichier_txt = st.sidebar.file_uploader("2. Journal du Jour (.txt)", type=["txt"])

st.title("🛡️ QG Modération - Tableau de Bord")

# 4. Création des Onglets pour naviguer
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Global (Excel)", "🔥 Analyse du Jour (Texte)", "💾 Base de Données"])

df_historique = None
if fichier_excel:
    df_historique = pd.read_excel(fichier_excel)

# ONGLET 1 : Les stats de l'Excel (Le côté hyper interactif)
with tab1:
    if df_historique is not None:
        st.header("Vue d'ensemble de l'équipe")
        
        # On vérifie que la colonne "Score Global" existe bien dans ton Excel
        if 'Score Global' in df_historique.columns:
            df_top = df_historique.sort_values(by="Score Global", ascending=False)
            
            # -- Ligne de KPIs (Chiffres clés animés) --
            col1, col2, col3 = st.columns(3)
            meilleur_modo = df_top.iloc[0]['Nom du Modérateur']
            meilleur_score = df_top.iloc[0]['Score Global']
            effectif = len(df_historique)
            
            col1.metric(label="👑 Top Modérateur", value=f"{meilleur_modo}", delta=f"{meilleur_score} pts globaux")
            col2.metric(label="👥 Effectif Total", value=f"{effectif} Modos")
            col3.metric(label="📈 Taux d'analyse", value="100% Automatisé")
            
            st.markdown("---")
            
            # -- Graphique 1 : Top 10 en Barres dynamiques --
            colA, colB = st.columns([2, 1])
            with colA:
                st.subheader("🏆 Classement Général (Scores)")
                fig_bar = px.bar(df_top.head(10), x='Nom du Modérateur', y='Score Global', 
                                 text='Score Global', color='Score Global', 
                                 color_continuous_scale='Purp', template="plotly_dark")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # -- Graphique 2 : Répartition des actions --
            with colB:
                st.subheader("Effort de l'équipe")
                if 'Total Active beaucoup' in df_historique.columns:
                    tot_bcp = df_historique['Total Active beaucoup'].sum()
                    tot_peu = df_historique['Total Active un peu'].sum()
                    tot_pas = df_historique['Total Pas là'].sum()
                    
                    fig_pie = px.pie(names=["Hyper Actifs", "Activité Moyenne", "Absences"], 
                                     values=[tot_bcp, tot_peu, tot_pas],
                                     color_discrete_sequence=['#00b894', '#fdcb6e', '#d63031'],
                                     hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("⚠️ La colonne 'Score Global' n'a pas été trouvée dans votre fichier Excel.")
    else:
        st.info("👈 Importe ton fichier Excel de suivi à gauche pour afficher les graphiques globaux.")

# ONGLET 2 : L'analyse en direct
with tab2:
    if fichier_txt:
        content = fichier_txt.read().decode("utf-8")
        lines = content.split('\n')
        
        mod_counts = Counter()
        keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé', 'Demande', 'Exclusion', 'Vous avez été']
        
        for line in lines:
            if any(keyword in line for keyword in keywords):
                match = re.search(r' par ([\w_]+)', line)
                if match:
                    mod = match.group(1)
                    if mod.lower() not in ['wizebot', 'erreur']:
                        mod_counts[mod] += 1
                        
        if mod_counts:
            st.success("✅ Historique Twitch analysé !")
            
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
            
            col_chart, col_table = st.columns([2, 1])
            with col_chart:
                st.subheader("Activité du Jour (Graphique)")
                fig_jour = px.bar(df_jour.head(15), x='Modérateur', y='Actions', text='Actions', 
                                  color='Actions', color_continuous_scale='Blues', template="plotly_dark")
                st.plotly_chart(fig_jour, use_container_width=True)
                
            with col_table:
                st.subheader("Résultats à copier")
                st.dataframe(df_jour, use_container_width=True)
        else:
            st.warning("Aucune action de modération trouvée.")
    else:
        st.info("👈 Importe ton fichier .txt du jour à gauche pour voir les stats en direct.")

# ONGLET 3 : L'affichage brut de l'Excel
with tab3:
    if df_historique is not None:
        st.subheader("📋 Ton fichier Excel brut")
        st.dataframe(df_historique, use_container_width=True)
    else:
        st.info("👈 Importe ton fichier Excel à gauche pour l'afficher ici.")
