import streamlit as st
from src.dashboard.utils.data_loader import load_dvf_data, load_rfr_data, load_annonces_data

st.set_page_config(page_title="Explorateur", layout="wide")
st.title("Explorateur de Données Brutes")

# Sélecteur de Source
dataset_name = st.radio("Choisir le jeu de données à explorer :",
                        ["Transactions DVF", "Revenus Fiscaux (RFR)", "Annonces Immobilières"],
                        horizontal=True)

df = None
if dataset_name == "Transactions DVF":
    df = load_dvf_data()
elif dataset_name == "Revenus Fiscaux (RFR)":
    df = load_rfr_data()
elif dataset_name == "Annonces Immobilières":
    df = load_annonces_data()

if df is not None and not df.empty:
    st.write(f"**{len(df)}** lignes chargées.")

    # Filtres dynamiques simples
    with st.expander("Filtres rapides"):
        cols = st.multiselect("Colonnes à afficher", df.columns.tolist(), default=df.columns.tolist()[:10])

    st.dataframe(df[cols] if cols else df, use_container_width=True, height=600)

    # Bouton Download
    csv = df.to_csv(sep=';', index=False).encode('utf-8')
    st.download_button("Télécharger ce dataset", csv, f"{dataset_name}.csv", "text/csv")
else:
    st.warning("Jeu de données vide ou introuvable.")