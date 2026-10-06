import streamlit as st
import pandas as pd
import re
from collections import Counter

# Configuration de la page
st.set_page_config(page_title="Suivi Modération", page_icon="🛡️")

# --- SYSTÈME DE MOT DE PASSE ---
# Tu peux changer "modo2026" par le mot de passe de ton choix
PASSWORD = "modo"
mot_de_passe = st.sidebar.text_input("🔐 Mot de passe :", type="password")

if mot_de_passe != PASSWORD:
    st.sidebar.warning("Veuillez entrer le mot de passe pour accéder à l'outil.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("🛡️ Tableau de Bord - Suivi Modération")
st.write("Glissez-déposez le fichier `.txt` contenant l'historique du tchat Twitch.")

# Zone d'import de fichier
uploaded_file = st.file_uploader("Fichier d'historique (.txt)", type=["txt"])

if uploaded_file is not None:
    # Lecture du fichier
    content = uploaded_file.read().decode("utf-8")
    lines = content.split('\n')
    
    mod_counts = Counter()
    # Mots-clés des actions Twitch à détecter
    keywords = ['Message supprimé', 'Avertissement', 'Banni', 'Ajouté', 'Supprimé', 'Retiré', 'Activé', 'Demande', 'Exclusion', 'Vous avez été']
    
    # Analyse ligne par ligne
    for line in lines:
        if any(keyword in line for keyword in keywords):
            match = re.search(r' par ([\w_]+)', line)
            if match:
                mod = match.group(1)
                # On ignore les bots et les erreurs
                if mod.lower() not in ['wizebot', 'erreur']:
                    mod_counts[mod] += 1
    
    if not mod_counts:
        st.warning("⚠️ Aucune action trouvée. Vérifiez que c'est le bon fichier.")
    else:
        st.success("✅ Fichier analysé avec succès !")
        
        # Création du tableau de données
        data = []
        for mod, count in mod_counts.most_common():
            if count >= 10:
                statut = "🟢 Active beaucoup"
            elif count > 0:
                statut = "🟡 Active un peu"
            else:
                statut = "🔴 Pas là"
            data.append({"Modérateur": mod, "Actions": count, "Statut": statut})
            
        df = pd.DataFrame(data)
        
        # Affichage du Top 3
        st.subheader("🏆 Top 3 du jour")
        top3 = df.head(3)
        for i, row in top3.iterrows():
            st.write(f"**{i+1}. {row['Modérateur']}** ({row['Actions']} actions)")
            
        # Affichage du tableau
        st.subheader("📊 Classement complet")
        st.dataframe(df, use_container_width=True)
        
        # Bouton d'export pour Excel
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV (Pour ton Excel)",
            data=csv,
            file_name='stats_moderation_jour.csv',
            mime='text/csv',
        )
