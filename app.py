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
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Global", "🔥 Analyse du Jour", "🔎 Fiche Modérateur"])

df_historique = None
if fichier_excel:
    try:
        df_historique = pd.read_excel(fichier_excel)
    except Exception as e:
        st.error(f"Erreur de lecture de l'Excel : {e}")

# ONGLET 1 : Les stats de l'Excel
with tab1:
    if df_historique is not None:
        st.header("Vue d'ensemble de l'équipe")
        
        # Recherche flexible de la colonne Score (anti-crash)
        col_score = next((col for col in df_historique.columns if "Score" in str(col)), None)
        col_nom = next((col for col in df_historique.columns if "Nom" in str(col)), df_historique.columns[0])
        
        if col_score:
            df_top = df_historique.sort_values(by=col_score, ascending=False).dropna(subset=[col_score])
            
            # -- Ligne de KPIs (Chiffres clés animés) --
            col1, col2, col3 = st.columns(3)
            meilleur_modo = df_top.iloc[0][col_nom] if not df_top.empty else "N/A"
            meilleur_score = df_top.iloc[0][col_score] if not df_top.empty else 0
            effectif = len(df_historique[col_nom].dropna().unique())
            
            col1.metric(label="👑 Top Modérateur", value=str(meilleur_modo), delta=f"{meilleur_score} pts globaux")
            col2.metric(label="👥 Effectif Total", value=f"{effectif} Modos enregistrés")
            col3.metric(label="📈 État du système", value="100% Synchronisé")
            
            st.markdown("---")
            
            # -- Graphique 1 : Top 15 en Barres dynamiques --
            colA, colB = st.columns([2, 1])
            with colA:
                st.subheader("🏆 Classement Général (Scores)")
                fig_bar = px.bar(df_top.head(15), x=col_nom, y=col_score, 
                                 text=col_score, color=col_score, 
                                 color_continuous_scale='Purp', template="plotly_dark")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # -- Graphique 2 : Répartition de l'effort --
            with colB:
                st.subheader("Effort Global")
                # Recherche flexible des colonnes de totaux (anti-crash)
                col_bcp = next((c for c in df_historique.columns if "beaucoup" in str(c).lower()), None)
                col_peu = next((c for c in df_historique.columns if "peu" in str(c).lower()), None)
                col_pas = next((c for c in df_historique.columns if "pas l" in str(c).lower()), None)
                
                tot_bcp = df_historique[col_bcp].sum() if col_bcp else 0
                tot_peu = df_historique[col_peu].sum() if col_peu else 0
                tot_pas = df_historique[col_pas].sum() if col_pas else 0
                
                if tot_bcp + tot_peu + tot_pas > 0:
                    fig_pie = px.pie(names=["Hyper Actifs", "Activité Moyenne", "Absences"], 
                                     values=[tot_bcp, tot_peu, tot_pas],
                                     color_discrete_sequence=['#00b894', '#fdcb6e', '#d63031'],
                                     hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Pas assez de données pour générer le graphique de répartition.")
        else:
            st.warning("⚠️ La colonne de Score n'a pas été trouvée. Assure-toi d'avoir une colonne 'Score Global' dans ton Excel.")
    else:
        st.info("👈 Importe ton fichier Excel de suivi à gauche pour afficher les graphiques globaux.")

# ONGLET 2 : L'analyse en direct du .txt
with tab2:
    if fichier_txt:
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
            st.success("✅ Historique Twitch analysé en temps réel !")
            
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
                st.subheader("Activité du Jour")
                fig_jour = px.bar(df_jour.head(15), x='Modérateur', y='Actions', text='Actions', 
                                  color='Actions', color_continuous_scale='Blues', template="plotly_dark")
                st.plotly_chart(fig_jour, use_container_width=True)
                
            with col_table:
                st.subheader("Résultats à copier")
                st.dataframe(df_jour, use_container_width=True)
                
                csv = df_jour.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger en CSV", data=csv, file_name='stats_jour.csv', mime='text/csv')
        else:
            st.warning("Aucune action de modération trouvée dans ce fichier texte.")
    else:
        st.info("👈 Importe ton fichier .txt du jour à gauche pour voir les stats en direct.")

# ONGLET 3 : Fiche Modérateur Interactive
with tab3:
    if df_historique is not None:
        st.subheader("🔎 Profil détaillé")
        col_nom = next((col for col in df_historique.columns if "Nom" in str(col)), df_historique.columns[0])
        liste_modos = df_historique[col_nom].dropna().unique().tolist()
        
        modo_choisi = st.selectbox("Sélectionne un modérateur pour voir son dossier :", ["-- Choisir un profil --"] + liste_modos)
        
        if modo_choisi != "-- Choisir un profil --":
            stats_modo = df_historique[df_historique[col_nom] == modo_choisi].iloc[0]
            
            # Affichage stylisé des infos du modérateur
            st.markdown(f"### Dossier de : **{modo_choisi}**")
            st.dataframe(pd.DataFrame(stats_modo.dropna()).T, use_container_width=True)
    else:
        st.info("👈 Importe ton fichier Excel à gauche pour pouvoir chercher un modérateur.")
