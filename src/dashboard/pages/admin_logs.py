import sys
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

# --- HACK PYTHONPATH ---
root_path = str(Path(__file__).resolve().parents[3])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Chemin vers la DB
DB_PATH = Path(root_path) / "logs_estimations.db"

st.set_page_config(page_title="Admin Logs", layout="wide")
st.title("Logs des Estimations")

if not DB_PATH.exists():
    st.warning("Aucune base de données trouvée. Lancez d'abord l'API et faites une estimation.")
else:
    # Bouton de rafraîchissement
    if st.button("Rafraîchir les données"):
        st.rerun()

    # Connexion et lecture
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM logs ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Estimations", len(df))
    if not df.empty:
        last_date = pd.to_datetime(df['timestamp']).dt.strftime('%d/%m %H:%M').iloc[0]
        col2.metric("Dernière activité", last_date)

        # Prix moyen estimé
        avg_price = df['prix_estime'].mean()
        col3.metric("Prix moyen estimé", f"{avg_price:,.0f} €/m²")

    st.divider()

    # Tableau interactif
    st.dataframe(
        df,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date", format="D MMM, HH:mm"),
            "prix_estime": st.column_config.NumberColumn("Prix/m²", format="%.0f €"),
            "classification": st.column_config.TextColumn("Classe", width="small"),
            "confiance": st.column_config.ProgressColumn("Confiance", format="%.1f%%", min_value=0, max_value=100),
        },
        use_container_width=True,
        height=500
    )

    # Export CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Télécharger les logs (CSV)",
        csv,
        "logs_estimations.csv",
        "text/csv",
        key='download-csv'
    )