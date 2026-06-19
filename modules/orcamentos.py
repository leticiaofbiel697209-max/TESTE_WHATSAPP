import pandas as pd
import streamlit as st
from services.db import get_connection, salvar_observacao


def render():
    st.title("Orçamentos")
    status = st.text_input("Filtrar status", value="")
    query = "SELECT o.*, c.nome, c.nome_fantasia, c.cnpj FROM orcamentos o LEFT JOIN clientes c ON c.id=o.cliente_id"
    params = ()
    if status:
        query += " WHERE o.status LIKE ?"
        params = (f"%{status}%",)
    query += " ORDER BY o.data DESC"
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        cliente_id = st.selectbox("Cliente do orçamento", df["cliente_id"].dropna().astype(str).unique().tolist())
        texto = st.text_area("Observação sobre orçamento")
        if st.button("Salvar observação") and texto.strip():
            salvar_observacao(cliente_id, "Orçamentos", "usuario", texto.strip())
            st.success("Observação salva.")
