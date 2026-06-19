import pandas as pd
import streamlit as st
from services.db import get_connection


def render():
    st.title("Base de Clientes")
    termo = st.text_input("Filtrar base")
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    if termo and not df.empty:
        mask = df.astype(str).apply(lambda col: col.str.contains(termo, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.dataframe(df, use_container_width=True)
