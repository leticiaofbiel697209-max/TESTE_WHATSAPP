import pandas as pd
import streamlit as st
from services.db import get_connection, salvar_observacao, salvar_agendamento, marcar_ja_liguei


def render():
    st.title("Portal das Vendedoras")
    with get_connection() as conn:
        vendedores = [r[0] for r in conn.execute("SELECT DISTINCT vendedor FROM clientes WHERE vendedor IS NOT NULL AND vendedor <> '' ORDER BY vendedor").fetchall()]
    vendedor = st.selectbox("Vendedor responsável", vendedores) if vendedores else None
    if not vendedor:
        st.warning("Nenhum vendedor encontrado nos clientes sincronizados.")
        return
    with get_connection() as conn:
        clientes = pd.read_sql_query("SELECT * FROM clientes WHERE vendedor=? ORDER BY nome", conn, params=(vendedor,))
        orc = pd.read_sql_query("SELECT * FROM orcamentos WHERE vendedor=? ORDER BY data DESC", conn, params=(vendedor,))
    st.subheader("Carteira")
    st.dataframe(clientes, use_container_width=True)
    st.subheader("Orçamentos do vendedor")
    st.dataframe(orc, use_container_width=True)
    cliente_id = st.selectbox("Cliente", clientes["id"].astype(str).tolist())
    texto = st.text_area("Observação compartilhada")
    if st.button("Salvar observação") and texto.strip():
        salvar_observacao(cliente_id, "Portal das Vendedoras", vendedor, texto.strip())
        st.success("Observação salva e visível nos outros módulos.")
    data = st.date_input("Agendar retorno")
    if st.button("Salvar agendamento"):
        salvar_agendamento(cliente_id, "Portal das Vendedoras", vendedor, str(data), texto)
        st.success("Agendamento salvo e visível nos outros módulos.")
    if st.button("Já liguei"):
        marcar_ja_liguei(cliente_id, "Portal das Vendedoras", vendedor)
        st.success("Contato registrado.")
