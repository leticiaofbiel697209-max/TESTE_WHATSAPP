import pandas as pd
import streamlit as st
from services.db import contar_registros, get_connection, listar_agendamentos


def render():
    st.title("Dashboard CEO")
    counts = contar_registros()
    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes", counts["clientes"])
    c2.metric("Vendas", counts["vendas"])
    c3.metric("Orçamentos", counts["orcamentos"])
    with get_connection() as conn:
        vendas = pd.read_sql_query("SELECT data, valor_total, status, vendedor FROM vendas ORDER BY data DESC LIMIT 200", conn)
        orc = pd.read_sql_query("SELECT data, valor_total, status, vendedor FROM orcamentos ORDER BY data DESC LIMIT 200", conn)
    st.subheader("Vendas recentes")
    st.dataframe(vendas, use_container_width=True)
    st.subheader("Orçamentos recentes")
    st.dataframe(orc, use_container_width=True)
    st.subheader("Retornos agendados")
    st.dataframe(pd.DataFrame(listar_agendamentos()), use_container_width=True)
