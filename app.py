import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Cockpit Modération", page_icon="🛡️", layout="wide")

PASSWORD = "modo"
mot_de_passe = st.sidebar.text_input("🔐 Mot de passe :", type="password")

if mot_de_passe != PASSWORD:
    st.sidebar.warning("Veuillez entrer le mot de passe.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("📁 Outils Quotidiens")
fichier_txt = st.sidebar.file_uploader("1. Scanneur du Jour (.txt)", type=["txt"])
fichier_excel_secours = st.sidebar.file_uploader("2. Import manuel (Secours)", type=["xlsx", "ods"])

# --- 2. LECTURE INTELLIGENTE DE L'EXCEL ---
FICHIER_EXCEL = "suivi.xlsx"

def charger_donnees():
    fichier = fichier_excel_secours if fichier_excel_secours else (FICHIER_EXCEL if os.path.exists(FICHIER_EXCEL) else None)
    if fichier:
        try:
            # On charge l'Excel et on cherche LA bonne feuille (celle des données brutes, pas le cockpit visuel)
            xls = pd.ExcelFile(fichier)
            feuille_cible = xls.sheet_names[0] # Par défaut la première
            
            # On cherche activement la feuille nommée "Feuille 1" ou celle contenant "Feuille"
            for nom in xls.sheet_names:
                if "Feuille" in nom or "Base" in nom or "Données" in nom:
                    feuille_cible = nom
                    break
                    
            df_brut = pd.read_excel(fichier, sheet_name=feuille_cible)
            return df_brut
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            return None
    return None

df_brut = charger_donnees()

if df_brut is None:
    st.error("⚠️ Fichier introuvable ou illisible.")
    st.stop()

# Nettoyage anti-crash
df = df_brut.copy()
col_nom = next((col for col in df.columns if "Nom" in str(col)), df.columns[0])

for col in ['Total Active beaucoup', 'Total Active un peu', 'Total Pas là', 'Total Absence justifiée']:
    if col not in df.columns:
        df[col] = 0

df = df.dropna(subset=[col_nom]) # On supprime les lignes vides créées par le design Excel

# --- 3. RECALCULS AUTOMATIQUES ---
df['Sessions (+)'] = df['Total Active beaucoup'] + df['Total Active un peu']
df['Total Jours'] = df['Sessions (+)'] + df['Total Pas là'] + df['Total Absence justifiée']
df['Score Global'] = (df['Total Active beaucoup'] * 3) + (df['Total Active un peu'] * 1) + (df['Total Pas là'] * -1)
df['Assiduité %'] = df.apply(lambda x: (x['Sessions (+)'] / (x['Total Jours'] - x['Total Absence justifiée'])) * 100 if (x['Total Jours'] - x['Total Absence justifiée']) > 0 else 0, axis=1)

def get_grade(score):
    if score >= 5: return "👑 Top Modo"
    elif score >= 3: return "⭐ Modo Actif"
    elif score >= 1: return "🔎 En observation"
    else: return "⚠️ Danger fantôme"

df['Grade'] = df['Score Global'].apply(get_grade)
color_map = {"👑 Top Modo": "#00b894", "⭐ Modo Actif": "#fdcb6e", "🔎 En observation": "#0984e3", "⚠️ Danger fantôme": "#d63031"}

# --- 4. AFFICHAGE INTERACTIF ---
st.title("🛡️ Cockpit Interactif de Modération")

tab1, tab2, tab3 = st.tabs(["🚀 Dashboard Manager", "✏️ Éditeur de Base de Données (NOUVEAU)", "⚡ Analyseur Tchat"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Effectif", len(df))
    c2.metric("📉 Assiduité Moyenne", f"{df['Assiduité %'].mean():.1f}%")
    c3.metric("⭐ Équipe Performante", len(df[df['Grade'].isin(['👑 Top Modo', '⭐ Modo Actif'])]))
    c4.metric("⚠️ Alertes RH", len(df[df['Grade'] == '⚠️️ Danger fantôme']))
    
    st.markdown("---")
    colA, colB = st.columns([2, 1])
    
    with colA:
        st.subheader("Classement & Assiduité")
        # Graphique interactif : on peut zoomer, survoler pour voir les détails
        df_tri = df.sort_values('Score Global', ascending=False).head(20)
        fig_bar = px.bar(df_tri, x=col_nom, y='Score Global', color='Grade', color_discrete_map=color_map, 
                         hover_data=['Assiduité %', 'Sessions (+)'], template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with colB:
        st.subheader("Répartition des forces")
        repartition = df['Grade'].value_counts().reset_index()
        repartition.columns = ['Grade', 'Effectif']
        fig_pie = px.pie(repartition, values='Effectif', names='Grade', color='Grade', color_discrete_map=color_map, hole=0.4)
        fig_pie.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("✏️ Modification des données en direct")
    st.write("Tu peux cliquer sur n'importe quelle case de ce tableau pour la modifier manuellement (ajouter un point, corriger une erreur).")
    
    # LE COEUR DE L'INTERACTIVITÉ : Le tableau éditable
    colonnes_a_editer = [col_nom, 'Total Active beaucoup', 'Total Active un peu', 'Total Pas là', 'Total Absence justifiée', 'Score Global']
    df_edite = st.data_editor(df[colonnes_a_editer], num_rows="dynamic", use_container_width=True)
    
    # Bouton de téléchargement de la nouvelle base modifiée
    st.download_button(
        "📥 Télécharger la base mise à jour",
        data=df_edite.to_csv(index=False).encode('utf-8'),
        file_name="base_moderation_mise_a_jour.csv",
        mime="text/csv"
    )

with tab3:
    st.subheader("⚡ Analyse des logs bruts Twitch")
    if fichier_txt is not None:
        content = fichier_txt.read().decode("utf-8")
        mod_counts = Counter()
        keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé', 'Demande', 'Exclusion', 'Vous avez été']
        for line in content.split('\n'):
            if any(k in line for k in keywords):
                match = re.search(r' par ([\w_]+)', line)
                if match and match.group(1).lower() not in ['wizebot', 'erreur']:
                    mod_counts[match.group(1)] += 1
                        
        if mod_counts:
            data_jour = [{"Modérateur": mod, "Actions": count, "Statut": "🟢 Active beaucoup" if count >= 10 else "🟡 Active un peu"} for mod, count in mod_counts.most_common()]
            st.dataframe(pd.DataFrame(data_jour), use_container_width=True)
    else:
        st.info("👈 Glisse le fichier .txt du jour dans la barre latérale à gauche.")
