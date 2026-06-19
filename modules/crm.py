import pandas as pd
import streamlit as st
from services.db import get_connection, marcar_ja_liguei, salvar_observacao, salvar_agendamento


def render():
    st.title("CRM")
    with get_connection() as conn:
        clientes = pd.read_sql_query("SELECT * FROM clientes ORDER BY atualizado_em DESC", conn)
    if clientes.empty:
        st.warning("Nenhum cliente sincronizado.")
        return
    st.dataframe(clientes, use_container_width=True)
    cliente_id = st.selectbox("Cliente para ação", clientes["id"].astype(str).tolist())
    obs = st.text_area("Observação")
    col1, col2 = st.columns(2)
    if col1.button("Salvar observação no CRM") and obs.strip():
        salvar_observacao(cliente_id, "CRM", "usuario", obs.strip())
        st.success("Observação salva.")
    data = col2.date_input("Retorno")
    if st.button("Agendar retorno no CRM"):
        salvar_agendamento(cliente_id, "CRM", "usuario", str(data), obs)
        st.success("Agendamento salvo.")
    if st.button("Marcar Já Liguei no CRM"):
        marcar_ja_liguei(cliente_id, "CRM")
        st.success("Já Liguei registrado.")
